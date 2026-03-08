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
    # Sum up the most recent sessions up to roughly the last 5 hours of wall time
    # This is an approximation — we use the most recent day's sessions
    today = get_today()
    recent_mins = 0
    for session in sessions:
        if session.get("date") == today:
            recent_mins += session.get("active_mins", 0)
    return recent_mins


def display_gemini_status(data):
    print("GEMINI CLI")

    gemini_today = get_gemini_today(data)
    pro_tokens = gemini_today.get("pro_tokens", 0)
    flash_tokens = gemini_today.get("flash_tokens", 0)
    pro_pct = (pro_tokens / GEMINI_PRO_DAILY_BUDGET) * 100 if GEMINI_PRO_DAILY_BUDGET > 0 else 0

    if pro_tokens >= GEMINI_PRO_WARN_TOKENS:
        print(f"  Pro tokens today: {pro_tokens:,} of ~{GEMINI_PRO_DAILY_BUDGET:,} ({pro_pct:.0f}%) — prepare handoff soon")
    else:
        print(f"  Pro tokens today: {pro_tokens:,} of ~{GEMINI_PRO_DAILY_BUDGET:,} ({pro_pct:.0f}%) — OK")

    print(f"  Flash tokens: {flash_tokens:,} (no limit concern)")


# --- Gemini JSON Parsing ---

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
        # Usage: tracker.py record-gemini '{"stats": ...}'
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
        print("  record-gemini JSON  Record Gemini CLI token usage from JSON output")
        print("  help                Show this help")

    else:
        print(f"Unknown command: {args[0]}")
        print("Run 'tracker.py help' for usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
