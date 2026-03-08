#!/usr/bin/env python3
"""Frugent Usage Tracker — monitors Claude Code and Gemini CLI quota usage."""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# --- Configuration ---
FRUGENT_DIR = Path.home() / ".frugent"
USAGE_FILE = FRUGENT_DIR / "usage.json"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GEMINI_TELEMETRY_FILE = FRUGENT_DIR / "gemini-telemetry.jsonl"

# Claude thresholds
CLAUDE_WINDOW_WARN_MINS = 240      # warn at 4h of 5h window
CLAUDE_WEEKLY_WARN_MINS = 2100     # warn at 35h of 40h week

# Gemini thresholds
GEMINI_PRO_DAILY_BUDGET = 30000
GEMINI_PRO_WARN_TOKENS = 25000     # warn at ~80%


def get_week_start(dt=None):
    """Get Monday of the current week as ISO date string."""
    if dt is None:
        dt = datetime.now()
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def load_usage():
    """Load usage data, auto-reset if new week detected."""
    if not USAGE_FILE.exists():
        return create_empty_usage()

    try:
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return create_empty_usage()

    current_week = get_week_start()
    if data.get("week_start") != current_week:
        # Auto-reset: new week detected
        data = create_empty_usage()
        save_usage(data)

    return data


def create_empty_usage():
    return {
        "week_start": get_week_start(),
        "claude": {
            "weekly_total_mins": 0,
            "sessions": []
        },
        "gemini": {
            "daily_totals": []
        }
    }


def save_usage(data):
    FRUGENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Claude Code Tracking ---

def scan_claude_sessions():
    """Read Claude JSONL logs and calculate active time for current week."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return None, "Claude projects directory not found"

    week_start_str = get_week_start()
    week_start_dt = datetime.strptime(week_start_str, "%Y-%m-%d")
    total_active_mins = 0
    sessions = []

    try:
        for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                result = parse_claude_jsonl(jsonl_file, week_start_dt)
                if result and result["active_mins"] > 0:
                    sessions.append(result)
                    total_active_mins += result["active_mins"]
    except (PermissionError, OSError) as e:
        return None, f"Unable to read Claude logs: {e}"

    return {
        "weekly_total_mins": round(total_active_mins, 1),
        "sessions": sessions
    }, None


def parse_claude_jsonl(filepath, week_start_dt):
    """Parse a single JSONL file and return active time this week."""
    messages = []

    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    messages.append(entry)
                except json.JSONDecodeError:
                    continue
    except (IOError, PermissionError):
        return None

    if not messages:
        return None

    active_mins = 0
    intervals = 0

    i = 0
    while i < len(messages):
        msg = messages[i]

        # Look for user/human messages
        msg_type = msg.get("type") or msg.get("role", "")
        if msg_type not in ("human", "user"):
            i += 1
            continue

        # Get timestamp
        ts_start = extract_timestamp(msg)
        if ts_start is None:
            i += 1
            continue

        # Check if this is within current week
        if ts_start < week_start_dt:
            i += 1
            continue

        # Find next assistant message
        j = i + 1
        while j < len(messages):
            next_msg = messages[j]
            next_type = next_msg.get("type") or next_msg.get("role", "")
            if next_type in ("assistant",):
                ts_end = extract_timestamp(next_msg)
                if ts_end is not None:
                    delta = (ts_end - ts_start).total_seconds() / 60.0
                    # Cap individual intervals at 30 min to exclude idle time
                    if 0 < delta <= 30:
                        active_mins += delta
                        intervals += 1
                break
            j += 1

        i = j + 1 if j < len(messages) else i + 1

    if intervals == 0:
        return None

    # Determine project name from directory
    project_name = filepath.parent.name

    # Determine date from first message in range
    first_ts = None
    for msg in messages:
        ts = extract_timestamp(msg)
        if ts and ts >= week_start_dt:
            first_ts = ts
            break

    return {
        "date": first_ts.strftime("%Y-%m-%d") if first_ts else get_today(),
        "project": project_name,
        "active_mins": round(active_mins, 1),
        "intervals": intervals
    }


def extract_timestamp(entry):
    """Extract datetime from a JSONL entry, trying common formats."""
    for key in ("timestamp", "ts", "time", "created_at"):
        val = entry.get(key)
        if val is None:
            continue

        # Unix timestamp (seconds or milliseconds)
        if isinstance(val, (int, float)):
            try:
                if val > 1e12:  # milliseconds
                    return datetime.fromtimestamp(val / 1000)
                return datetime.fromtimestamp(val)
            except (ValueError, OSError):
                continue

        # ISO format string
        if isinstance(val, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S%z"):
                try:
                    return datetime.strptime(val.replace("+00:00", "Z").rstrip("Z") + "Z",
                                             "%Y-%m-%dT%H:%M:%S.%fZ") if "." in val else \
                           datetime.strptime(val.rstrip("Z") + "Z", "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue
            # Try plain parse as last resort
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00").replace("+00:00", ""))
            except ValueError:
                continue

    return None


# --- Gemini CLI Tracking ---

def get_gemini_today(data):
    """Get today's Gemini usage from stored data."""
    today = get_today()
    for entry in data.get("gemini", {}).get("daily_totals", []):
        if entry.get("date") == today:
            return entry
    return {"date": today, "pro_tokens": 0, "flash_tokens": 0, "prompts": 0}


def record_gemini_usage(data, pro_tokens, flash_tokens):
    """Record Gemini token usage for today."""
    today = get_today()
    daily_totals = data.setdefault("gemini", {}).setdefault("daily_totals", [])

    for entry in daily_totals:
        if entry.get("date") == today:
            entry["pro_tokens"] = entry.get("pro_tokens", 0) + pro_tokens
            entry["flash_tokens"] = entry.get("flash_tokens", 0) + flash_tokens
            entry["prompts"] = entry.get("prompts", 0) + 1
            save_usage(data)
            return

    daily_totals.append({
        "date": today,
        "pro_tokens": pro_tokens,
        "flash_tokens": flash_tokens,
        "prompts": 1
    })
    save_usage(data)


def scan_gemini_telemetry():
    """Read Gemini telemetry log and extract today's token usage.

    Handles both JSONL (one object per line) and pretty-printed multi-line JSON.
    """
    if not GEMINI_TELEMETRY_FILE.exists():
        return None, "no-file"

    today = get_today()
    pro_tokens = 0
    flash_tokens = 0
    prompts = 0
    parsed_any = False

    try:
        content = GEMINI_TELEMETRY_FILE.read_text()
        if not content.strip():
            return None, "no-data"

        import json
        decoder = json.JSONDecoder()
        pos = 0
        content_len = len(content)

        while pos < content_len:
            # Skip whitespace
            while pos < content_len and content[pos].isspace():
                pos += 1
            if pos >= content_len:
                break

            try:
                entry, pos = decoder.raw_decode(content, pos)
                tokens = extract_gemini_tokens(entry, today)
                if tokens:
                    parsed_any = True
                    pro_tokens += tokens.get("pro", 0)
                    flash_tokens += tokens.get("flash", 0)
                    prompts += tokens.get("prompts", 0)
            except json.JSONDecodeError:
                # If decode fails, skip current character and try again
                pos += 1

    except (IOError, PermissionError) as e:
        return None, f"Unable to read telemetry: {e}"

    if not parsed_any:
        return None, "no-data"

    return {
        "pro_tokens": pro_tokens,
        "flash_tokens": flash_tokens,
        "prompts": prompts
    }, None


def extract_gemini_tokens(entry, today):
    """Extract token counts from a telemetry entry.

    Handles multiple possible formats:
    1. OpenTelemetry log record with attributes
    2. OpenTelemetry metric record
    3. Gemini CLI custom format
    """
    if not isinstance(entry, dict):
        return None

    # Check if this entry is from today
    entry_date = None
    for key in ("timestamp", "timeUnixNano", "time", "ts", "observedTimeUnixNano"):
        val = entry.get(key)
        if val is None:
            # Check nested: body.timestamp, attributes, etc.
            continue
        if isinstance(val, (int, float)):
            try:
                if val > 1e18:  # nanoseconds
                    dt = datetime.fromtimestamp(val / 1e9)
                elif val > 1e12:  # milliseconds
                    dt = datetime.fromtimestamp(val / 1000)
                else:
                    dt = datetime.fromtimestamp(val)
                entry_date = dt.strftime("%Y-%m-%d")
            except (ValueError, OSError):
                continue
        elif isinstance(val, str):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00").replace("+00:00", ""))
                entry_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        if entry_date:
            break

    if entry_date and entry_date != today:
        return None

    pro = 0
    flash = 0
    found = False

    # Strategy 1: Look for token attributes in OTel log records
    # OTel logs have: body, attributes, severityText, etc.
    attrs = entry.get("attributes", {})
    if isinstance(attrs, list):
        # OTel format: attributes is a list of {key, value} pairs
        attrs = {a.get("key"): a.get("value", {}).get("intValue", a.get("value", {}).get("stringValue", ""))
                 for a in attrs if isinstance(a, dict)}

    for key, val in attrs.items() if isinstance(attrs, dict) else []:
        key_lower = key.lower()
        if "token" in key_lower:
            found = True
            try:
                token_val = int(val) if not isinstance(val, int) else val
            except (ValueError, TypeError):
                continue
            # Determine if pro or flash based on model info in the entry
            model = _find_model_name(entry, attrs)
            if "pro" in model:
                pro += token_val
            else:
                flash += token_val

    # Strategy 2: Look for nested stats (like headless JSON output)
    stats = entry.get("stats", {})
    if isinstance(stats, dict):
        models = stats.get("models", {})
        for model_name, model_data in models.items():
            total = 0
            if isinstance(model_data, dict):
                tokens_data = model_data.get("tokens", {})
                total = tokens_data.get("total", 0) if isinstance(tokens_data, dict) else 0
            if "pro" in model_name.lower():
                pro += total
                found = True
            elif "flash" in model_name.lower():
                flash += total
                found = True

    # Strategy 3: Look for metric data points
    if entry.get("name", "").startswith("gemini_cli.token"):
        data_points = entry.get("dataPoints", entry.get("data_points", []))
        for dp in data_points if isinstance(data_points, list) else []:
            val = dp.get("asInt", dp.get("value", 0))
            dp_attrs = dp.get("attributes", {})
            if isinstance(dp_attrs, list):
                dp_attrs = {a.get("key"): a.get("value", {}).get("stringValue", "")
                            for a in dp_attrs if isinstance(a, dict)}
            model = dp_attrs.get("model", dp_attrs.get("gen_ai.request.model", ""))
            if "pro" in model.lower():
                pro += int(val)
                found = True
            else:
                flash += int(val)
                found = True

    if not found:
        return None

    return {"pro": pro, "flash": flash, "prompts": 1 if found else 0}


def _find_model_name(entry, attrs):
    """Try to find model name from entry or attributes."""
    for key in ("model", "gen_ai.request.model", "modelId"):
        if key in attrs:
            return str(attrs[key]).lower()
    # Check body or nested fields
    body = entry.get("body", {})
    if isinstance(body, dict):
        for key in ("model", "modelId"):
            if key in body:
                return str(body[key]).lower()
    return ""


# --- Display ---

def format_time(mins):
    hours = int(mins // 60)
    remaining_mins = int(mins % 60)
    return f"{hours}h {remaining_mins:02d}m"


def display_status(show_claude=True, show_gemini=True, show_week=False):
    data = load_usage()

    if show_claude:
        display_claude_status(data, show_week)

    if show_claude and show_gemini:
        print()

    if show_gemini:
        display_gemini_status(data)


def display_claude_status(data, show_week=False):
    print("CLAUDE CODE")

    # Scan fresh from JSONL files
    claude_data, error = scan_claude_sessions()

    if error:
        print(f"  Unable to read usage data — {error}")
        print("  Proceed with caution and monitor quota manually")
        return

    if claude_data is None:
        print("  No usage data found this week")
        return

    # Update stored data
    data["claude"] = claude_data
    save_usage(data)

    weekly_mins = claude_data["weekly_total_mins"]
    weekly_pct = (weekly_mins / (40 * 60)) * 100
    remaining_mins = max(0, 40 * 60 - weekly_mins)

    # 5-hour window (approximate recent usage)
    recent_mins = calculate_recent_window(claude_data["sessions"])
    window_pct = (recent_mins / (5 * 60)) * 100

    # Window warning
    if recent_mins >= CLAUDE_WINDOW_WARN_MINS:
        print(f"  5-hour window: {format_time(recent_mins)} of ~5h ({window_pct:.0f}%) — prepare handoff soon")
    else:
        print(f"  5-hour window: {format_time(recent_mins)} of ~5h ({window_pct:.0f}%) — OK")

    # Weekly warning
    if weekly_mins >= CLAUDE_WEEKLY_WARN_MINS:
        print(f"  Weekly: {format_time(weekly_mins)} of ~40h ({weekly_pct:.0f}%) — {format_time(remaining_mins)} remaining — prepare handoff soon")
    else:
        print(f"  Weekly: {format_time(weekly_mins)} of ~40h ({weekly_pct:.0f}%) — {format_time(remaining_mins)} remaining")

    if show_week and claude_data["sessions"]:
        print()
        print("  Weekly breakdown:")
        for session in claude_data["sessions"]:
            print(f"    {session['date']} | {session['project']}: {format_time(session['active_mins'])} ({session['intervals']} intervals)")


def calculate_recent_window(sessions):
    """Estimate active time in the most recent ~5 hour window."""
    today = get_today()
    recent_mins = 0
    for session in sessions:
        if session.get("date") == today:
            recent_mins += session.get("active_mins", 0)
    return recent_mins


def display_gemini_status(data):
    print("GEMINI CLI")

    # Try reading telemetry log first (automatic)
    telemetry_data, telemetry_error = scan_gemini_telemetry()

    if telemetry_data:
        # Update stored data with fresh telemetry
        today = get_today()
        daily_totals = data.setdefault("gemini", {}).setdefault("daily_totals", [])

        # Replace today's entry with telemetry data
        found = False
        for entry in daily_totals:
            if entry.get("date") == today:
                entry["pro_tokens"] = telemetry_data["pro_tokens"]
                entry["flash_tokens"] = telemetry_data["flash_tokens"]
                entry["prompts"] = telemetry_data["prompts"]
                found = True
                break
        if not found:
            daily_totals.append({
                "date": today,
                "pro_tokens": telemetry_data["pro_tokens"],
                "flash_tokens": telemetry_data["flash_tokens"],
                "prompts": telemetry_data["prompts"]
            })
        save_usage(data)

    # Display from stored data (whether from telemetry or manual record)
    gemini_today = get_gemini_today(data)
    pro_tokens = gemini_today.get("pro_tokens", 0)
    flash_tokens = gemini_today.get("flash_tokens", 0)
    pro_pct = (pro_tokens / GEMINI_PRO_DAILY_BUDGET) * 100 if GEMINI_PRO_DAILY_BUDGET > 0 else 0

    # Source indicator
    if telemetry_data:
        source = "telemetry"
    elif pro_tokens > 0 or flash_tokens > 0:
        source = "manual"
    else:
        source = None

    if pro_tokens >= GEMINI_PRO_WARN_TOKENS:
        print(f"  Pro tokens today: {pro_tokens:,} of ~{GEMINI_PRO_DAILY_BUDGET:,} ({pro_pct:.0f}%) — prepare handoff soon")
    else:
        print(f"  Pro tokens today: {pro_tokens:,} of ~{GEMINI_PRO_DAILY_BUDGET:,} ({pro_pct:.0f}%) — OK")

    print(f"  Flash tokens: {flash_tokens:,} (no limit concern)")

    if source:
        print(f"  Source: {source}")
    elif telemetry_error == "no-file":
        print("  Source: no telemetry file found — using manual records only")
        print("  Tip: run setup.sh to enable automatic Gemini tracking")
    elif telemetry_error == "no-data":
        print("  Source: telemetry file empty — no Gemini usage recorded today")


# --- Gemini JSON Parsing (manual fallback) ---

def parse_gemini_json(json_str):
    """Parse Gemini CLI JSON output and record token usage."""
    try:
        output = json.loads(json_str)
    except json.JSONDecodeError:
        print("Unable to parse Gemini output — JSON format may have changed")
        print("Proceed with caution and monitor quota manually")
        return

    models = output.get("stats", {}).get("models", {})
    pro_tokens = 0
    flash_tokens = 0

    for model_name, model_data in models.items():
        total = model_data.get("tokens", {}).get("total", 0)
        if "pro" in model_name.lower():
            pro_tokens += total
        elif "flash" in model_name.lower():
            flash_tokens += total

    data = load_usage()
    record_gemini_usage(data, pro_tokens, flash_tokens)
    print(f"Recorded: {pro_tokens:,} Pro tokens, {flash_tokens:,} Flash tokens")


# --- CLI ---

def main():
    args = sys.argv[1:]

    if not args or args[0] == "status":
        flags = args[1:] if len(args) > 1 else []

        if "--claude" in flags:
            display_status(show_claude=True, show_gemini=False, show_week="--week" in flags)
        elif "--gemini" in flags:
            display_status(show_claude=False, show_gemini=True)
        elif "--week" in flags:
            display_status(show_claude=True, show_gemini=True, show_week=True)
        else:
            display_status()

    elif args[0] == "record-gemini":
        # Manual fallback: tracker.py record-gemini '{"stats": ...}'
        if len(args) < 2:
            print("Usage: tracker.py record-gemini '<json>'")
            sys.exit(1)
        parse_gemini_json(args[1])

    elif args[0] == "help":
        print("Frugent Usage Tracker")
        print()
        print("Commands:")
        print("  status              Full status for Claude + Gemini")
        print("  status --claude     Claude Code usage only")
        print("  status --gemini     Gemini CLI usage only")
        print("  status --week       Full weekly breakdown")
        print("  record-gemini JSON  Record Gemini token usage manually (fallback)")
        print("  help                Show this help")
        print()
        print("Gemini tracking:")
        print("  Primary: reads ~/.frugent/gemini-telemetry.jsonl (auto, via OTel)")
        print("  Fallback: record-gemini command (manual)")

    else:
        print(f"Unknown command: {args[0]}")
        print("Run 'tracker.py help' for usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
