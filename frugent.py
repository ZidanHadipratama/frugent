#!/usr/bin/env python3
"""Frugent — frugal + agent. Multi-agent coordination for solo developers."""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# --- Configuration ---
FRUGENT_DIR = Path.home() / ".frugent"
USAGE_FILE = FRUGENT_DIR / "usage.json"
TEMPLATES_DIR = FRUGENT_DIR / "templates"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GEMINI_TELEMETRY_FILE = FRUGENT_DIR / "gemini-telemetry.jsonl"
CLAUDE_SKILL_SRC = Path.home() / ".claude" / "CLAUDE.md"

DOCS_DIR = Path("docs")

# Claude thresholds
CLAUDE_WINDOW_WARN_MINS = 240      # warn at 4h of 5h window
CLAUDE_WEEKLY_WARN_MINS = 2100     # warn at 35h of 40h week

# Gemini thresholds
GEMINI_PRO_DAILY_BUDGET = 30000
GEMINI_PRO_WARN_TOKENS = 25000     # warn at ~80%

# Colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"


# ============================================================
# LAUNCHER
# ============================================================

def launch():
    """Interactive launcher — detect project state and launch agent."""
    print()
    print(f"  {BOLD}Frugent{NC} — frugal + agent")
    print(f"  {DIM}Multi-agent coordination for solo developers{NC}")
    print()

    # Check for frugent-specific files, not just any docs/ folder
    frugent_markers = ["log.md", "plan.md", "briefing.md", "contracts.md"]
    is_existing = DOCS_DIR.exists() and any(
        (DOCS_DIR / marker).exists() for marker in frugent_markers
    )

    if is_existing:
        launch_existing()
    else:
        launch_new()


def launch_new():
    """Launch flow for new projects (no frugent docs found)."""
    print(f"  {YELLOW}New project detected.{NC}")
    print()

    # Check for PRD/SRS
    has_prd = _find_file("PRD.md")
    has_srs = _find_file("SRS.md")

    if has_prd:
        print(f"  {GREEN}Found:{NC} {has_prd}")
    if has_srs:
        print(f"  {GREEN}Found:{NC} {has_srs}")
    if not has_prd and not has_srs:
        print(f"  {DIM}No PRD.md or SRS.md found — agent will ask about this.{NC}")

    # Check for existing CLAUDE.md and back it up
    has_old_claude = _setup_claude_md()
    if has_old_claude:
        print(f"  {GREEN}Backed up:{NC} CLAUDE.md → docs/old-CLAUDE.md")
        print(f"  {GREEN}Replaced:{NC} CLAUDE.md with frugent version")
    print()

    # Choose init mode
    print(f"  {BOLD}Init mode:{NC}")
    print(f"    [1] Quick  — fast scan, start working now")
    print(f"    [2] Deep   — Gemini scans codebase first (free)")
    print(f"    [3] Skip   — just copy templates")
    print()

    mode = _prompt_choice("  Choose mode", ["1", "2", "3"])
    mode_name = {"1": "quick", "2": "deep", "3": "skip"}[mode]

    # Scaffold docs
    _scaffold_docs()

    # Write briefing
    _write_init_briefing(mode_name, has_prd, has_srs, has_old_claude)

    # Show quota
    print()
    display_status()
    print()

    # Build prompts and write to docs/README.md
    if mode_name == "skip":
        _write_readme(None, None)
        print(f"  {GREEN}Templates copied to docs/. Done!{NC}")
        print(f"  {DIM}Open claude or gemini and start working.{NC}")
    elif mode_name == "deep":
        analysis_prompt = _build_analysis_prompt()
        init_prompt = _build_init_prompt("deep", has_prd, has_srs, has_old_claude)
        _write_readme(init_prompt, analysis_prompt)

        _print_prompt_box(
            "Step 1: Open gemini and paste this:",
            analysis_prompt
        )
        print()
        _print_prompt_box(
            "Step 2: After Gemini finishes, open claude and paste this:",
            init_prompt
        )
    else:
        init_prompt = _build_init_prompt("quick", has_prd, has_srs, has_old_claude)
        _write_readme(init_prompt, None)

        _print_prompt_box(
            "Open claude and paste this to start:",
            init_prompt
        )
    print()


def launch_existing():
    """Launch flow for existing frugent projects (docs/ exists)."""
    print(f"  {GREEN}Existing project detected.{NC}")
    print()

    # Read last activity from log.md
    last_activity = _read_last_log_entries()
    blockers = _read_unresolved_blockers()
    handoff = _read_last_handoff()

    if last_activity:
        print(f"  {BOLD}Last activity:{NC}")
        for line in last_activity:
            print(f"    {line}")
        print()

    if blockers:
        print(f"  {RED}Unresolved blockers:{NC}")
        for line in blockers:
            print(f"    {line}")
        print()
    else:
        print(f"  {DIM}Unresolved blockers: none{NC}")

    if handoff:
        print(f"  {YELLOW}Open handoff:{NC}")
        for line in handoff:
            print(f"    {line}")
        print()
    else:
        print(f"  {DIM}Open handoff: none{NC}")

    # Update briefing.md with current state
    _update_briefing(last_activity, blockers, handoff)

    # Show quota
    display_status()
    print()

    # Build and show the resume prompt
    prompt = _build_resume_prompt(handoff is not None)
    _write_readme(prompt, None)
    _print_prompt_box(
        "Open claude or gemini and paste this to resume:",
        prompt
    )
    print()


def _find_file(name):
    """Find a file in current dir, docs/, or parent dirs."""
    candidates = [
        Path(name),
        Path("docs") / name,
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def _scaffold_docs():
    """Copy templates into docs/."""
    if not TEMPLATES_DIR.exists():
        print(f"  {RED}Templates not found at {TEMPLATES_DIR}{NC}")
        print(f"  Run setup.sh first.")
        sys.exit(1)

    DOCS_DIR.mkdir(exist_ok=True)
    count = 0
    for template in TEMPLATES_DIR.iterdir():
        if template.is_file():
            dest = DOCS_DIR / template.name
            if not dest.exists():
                shutil.copy2(template, dest)
                count += 1

    print(f"  {GREEN}Scaffolded {count} templates into docs/{NC}")


def _prompt_choice(prompt, options):
    """Prompt user for a choice."""
    while True:
        try:
            choice = input(f"{prompt} [{'/'.join(options)}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if choice in options:
            return choice
        print(f"  Please enter one of: {', '.join(options)}")


def _setup_claude_md():
    """Back up existing CLAUDE.md and replace with frugent's version."""
    claude_md = Path("CLAUDE.md")
    has_old = False

    # Back up existing CLAUDE.md if it exists
    if claude_md.exists():
        DOCS_DIR.mkdir(exist_ok=True)
        backup = DOCS_DIR / "old-CLAUDE.md"
        shutil.copy2(claude_md, backup)
        has_old = True

    # Overwrite with frugent's CLAUDE.md
    if CLAUDE_SKILL_SRC.exists():
        shutil.copy2(CLAUDE_SKILL_SRC, claude_md)
    else:
        print(f"  {RED}Frugent CLAUDE.md not found at {CLAUDE_SKILL_SRC}{NC}")
        print(f"  Run setup.sh first.")

    return has_old


def _write_init_briefing(mode, has_prd, has_srs, has_old_claude=False):
    """Write init context to docs/briefing.md for the agent to read."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = ["# Briefing", ""]
    lines.append("## Current State")
    lines.append(f"- **Date:** {today}")
    lines.append(f"- **Status:** New project — init required")
    lines.append(f"- **Init mode:** {mode}")
    lines.append("")

    lines.append("## Context")
    if has_prd:
        lines.append(f"- **PRD:** `{has_prd}`")
    if has_srs:
        lines.append(f"- **SRS:** `{has_srs}`")
    if not has_prd and not has_srs:
        lines.append("- No PRD or SRS found — ask the developer if they want you to generate them.")
    if has_old_claude:
        lines.append("- **Previous CLAUDE.md:** `docs/old-CLAUDE.md` — contains project context from before frugent was set up. Read this to understand the project.")
    lines.append("- Templates are already scaffolded in `docs/`.")
    lines.append("")

    briefing_file = DOCS_DIR / "briefing.md"
    try:
        briefing_file.write_text("\n".join(lines))
    except IOError:
        pass


def _build_init_prompt(mode, has_prd, has_srs, has_old_claude=False):
    """Build the copy-paste prompt for init."""
    parts = [f"Init frugent for this project using {mode} mode."]

    if has_prd:
        parts.append(f"PRD is at {has_prd}.")
    if has_srs:
        parts.append(f"SRS is at {has_srs}.")
    if not has_prd and not has_srs:
        parts.append("No PRD or SRS found — ask me if I want you to generate them.")

    if has_old_claude:
        parts.append("Read docs/old-CLAUDE.md first — it has the existing project context (architecture, tech stack, conventions). Use it to fill in the frugent docs.")

    parts.append("Templates are already scaffolded in docs/. Read docs/briefing.md for full context.")
    return " ".join(parts)


def _build_analysis_prompt():
    """Build the copy-paste prompt for Gemini codebase analysis."""
    return (
        "Analyze this codebase for frugent. "
        "Read the entire codebase and fill in docs/codebase-analysis.md with: "
        "tech stack, project structure, all modules/components and their status, "
        "existing interfaces/APIs, existing tests, installed dependencies, "
        "git state (branches, uncommitted work), and a summary of what's built vs what's missing. "
        "Be thorough — this analysis will be used by Claude to create the project plan."
    )


def _build_resume_prompt(has_handoff):
    """Build the copy-paste prompt for resuming work."""
    if has_handoff:
        return (
            "Resume work on this frugent project. "
            "Read docs/briefing.md for current state — there is an open handoff from a previous session. "
            "Check docs/log.md for the latest handoff entry and continue from there."
        )
    return (
        "Resume work on this frugent project. "
        "Read docs/briefing.md for current state, then check docs/log.md for recent activity. "
        "Continue with the next task in docs/plan.md."
    )


def _write_readme(init_prompt, analysis_prompt=None):
    """Write the getting-started prompt(s) to docs/README.md."""
    lines = ["# Frugent — Getting Started", ""]
    lines.append("Paste the prompt(s) below into your agent to get started.")
    lines.append("")

    if analysis_prompt:
        lines.append("## Step 1: Codebase Analysis (Gemini — free)")
        lines.append("")
        lines.append("Open `gemini` and paste this:")
        lines.append("")
        lines.append("```")
        lines.append(analysis_prompt)
        lines.append("```")
        lines.append("")
        lines.append("## Step 2: Planning (Claude)")
        lines.append("")
        lines.append("After Gemini finishes, open `claude` and paste this:")
        lines.append("")
    elif init_prompt:
        lines.append("## Start Prompt")
        lines.append("")
        lines.append("Open `claude` or `gemini` and paste this:")
        lines.append("")

    if init_prompt:
        lines.append("```")
        lines.append(init_prompt)
        lines.append("```")
        lines.append("")

    readme_file = DOCS_DIR / "README.md"
    try:
        readme_file.write_text("\n".join(lines))
    except IOError:
        pass


def _print_prompt_box(header, prompt):
    """Print a prompt in a visible box for the user to copy-paste."""
    print(f"  {BOLD}{header}{NC}")
    print()
    print(f"  {CYAN}┌{'─' * 70}┐{NC}")
    # Wrap prompt into lines that fit in the box
    words = prompt.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > 68:
            print(f"  {CYAN}│{NC} {line:<68} {CYAN}│{NC}")
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        print(f"  {CYAN}│{NC} {line:<68} {CYAN}│{NC}")
    print(f"  {CYAN}└{'─' * 70}┘{NC}")


# ============================================================
# LOG READING
# ============================================================

def _read_last_log_entries(n=1):
    """Read the last n entries from log.md."""
    log_file = DOCS_DIR / "log.md"
    if not log_file.exists():
        return None

    try:
        content = log_file.read_text()
    except IOError:
        return None

    # Split by entry headers (## YYYY-MM-DD — ...)
    entries = re.split(r'\n(?=## \d{4}-\d{2}-\d{2})', content)
    entries = [e.strip() for e in entries if re.match(r'## \d{4}-\d{2}-\d{2}', e.strip())]

    if not entries:
        return None

    result = []
    for entry in entries[-n:]:
        lines = entry.strip().split("\n")
        for line in lines[:5]:  # First 5 lines of each entry
            result.append(line.strip())
    return result


def _read_unresolved_blockers():
    """Find [blocker] entries that don't have a matching resolution."""
    log_file = DOCS_DIR / "log.md"
    if not log_file.exists():
        return None

    try:
        content = log_file.read_text()
    except IOError:
        return None

    # Find blocker entries
    blockers = []
    entries = re.split(r'\n(?=## \d{4}-\d{2}-\d{2})', content)
    for entry in entries:
        if "[blocker]" in entry.lower():
            lines = entry.strip().split("\n")
            # Check if there's a resolution marker
            if not any("[resolved]" in line.lower() for line in lines):
                for line in lines[:4]:
                    blockers.append(line.strip())

    return blockers if blockers else None


def _read_last_handoff():
    """Read the most recent [handoff] entry."""
    log_file = DOCS_DIR / "log.md"
    if not log_file.exists():
        return None

    try:
        content = log_file.read_text()
    except IOError:
        return None

    entries = re.split(r'\n(?=## \d{4}-\d{2}-\d{2})', content)
    handoffs = [e for e in entries if "[handoff]" in e.lower()]

    if not handoffs:
        return None

    last = handoffs[-1].strip()
    lines = last.split("\n")
    return [line.strip() for line in lines[:8]]  # First 8 lines


def _update_briefing(last_activity, blockers, handoff):
    """Update briefing.md with current project state."""
    briefing_file = DOCS_DIR / "briefing.md"
    plan_file = DOCS_DIR / "plan.md"

    # Read current task from plan.md
    current_task = "Check docs/plan.md"
    if plan_file.exists():
        try:
            plan_content = plan_file.read_text()
            # Find first pending task
            for line in plan_content.split("\n"):
                if "pending" in line.lower():
                    # Extract task from table row
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if len(cells) >= 2:
                        current_task = cells[1]  # Task column
                    break
        except IOError:
            pass

    # Build briefing content
    today = datetime.now().strftime("%Y-%m-%d")
    lines = ["# Briefing", ""]
    lines.append("## Current State")
    lines.append(f"- **Date:** {today}")

    if last_activity:
        last_header = last_activity[0] if last_activity else "Unknown"
        lines.append(f"- **Last activity:** {last_header}")

    lines.append(f"- **Current task:** {current_task}")
    lines.append("")

    if blockers:
        lines.append("## Known Blockers")
        for b in blockers:
            lines.append(f"- {b}")
        lines.append("")

    if handoff:
        lines.append("## Open Handoff")
        for h in handoff:
            lines.append(f"- {h}")
        lines.append("")

    lines.append("## Quota Budget")
    lines.append("<!-- Run: python ~/.frugent/tracker.py status -->")
    lines.append("")

    try:
        briefing_file.write_text("\n".join(lines))
    except IOError:
        pass


# ============================================================
# TRACKER (from tracker.py)
# ============================================================

def get_week_start(dt=None):
    if dt is None:
        dt = datetime.now()
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def load_usage():
    if not USAGE_FILE.exists():
        return create_empty_usage()
    try:
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return create_empty_usage()
    current_week = get_week_start()
    if data.get("week_start") != current_week:
        data = create_empty_usage()
        save_usage(data)
    return data


def create_empty_usage():
    return {
        "week_start": get_week_start(),
        "claude": {"weekly_total_mins": 0, "sessions": []},
        "gemini": {"daily_totals": []}
    }


def save_usage(data):
    FRUGENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Claude Code Tracking ---

def scan_claude_sessions():
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
    return {"weekly_total_mins": round(total_active_mins, 1), "sessions": sessions}, None


def parse_claude_jsonl(filepath, week_start_dt):
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
        msg_type = msg.get("type") or msg.get("role", "")
        if msg_type not in ("human", "user"):
            i += 1
            continue
        ts_start = extract_timestamp(msg)
        if ts_start is None or ts_start < week_start_dt:
            i += 1
            continue
        j = i + 1
        while j < len(messages):
            next_msg = messages[j]
            next_type = next_msg.get("type") or next_msg.get("role", "")
            if next_type == "assistant":
                ts_end = extract_timestamp(next_msg)
                if ts_end is not None:
                    delta = (ts_end - ts_start).total_seconds() / 60.0
                    if 0 < delta <= 30:
                        active_mins += delta
                        intervals += 1
                break
            j += 1
        i = j + 1 if j < len(messages) else i + 1

    if intervals == 0:
        return None

    project_name = filepath.parent.name
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
    for key in ("timestamp", "ts", "time", "created_at"):
        val = entry.get(key)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                if val > 1e12:
                    return datetime.fromtimestamp(val / 1000)
                return datetime.fromtimestamp(val)
            except (ValueError, OSError):
                continue
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00").replace("+00:00", ""))
            except ValueError:
                continue
    return None


# --- Gemini CLI Tracking ---

def get_gemini_today(data):
    today = get_today()
    for entry in data.get("gemini", {}).get("daily_totals", []):
        if entry.get("date") == today:
            return entry
    return {"date": today, "pro_tokens": 0, "flash_tokens": 0, "prompts": 0}


def record_gemini_usage(data, pro_tokens, flash_tokens):
    today = get_today()
    daily_totals = data.setdefault("gemini", {}).setdefault("daily_totals", [])
    for entry in daily_totals:
        if entry.get("date") == today:
            entry["pro_tokens"] = entry.get("pro_tokens", 0) + pro_tokens
            entry["flash_tokens"] = entry.get("flash_tokens", 0) + flash_tokens
            entry["prompts"] = entry.get("prompts", 0) + 1
            save_usage(data)
            return
    daily_totals.append({"date": today, "pro_tokens": pro_tokens, "flash_tokens": flash_tokens, "prompts": 1})
    save_usage(data)


def scan_gemini_telemetry():
    if not GEMINI_TELEMETRY_FILE.exists():
        return None, "no-file"
    today = get_today()
    pro_tokens = 0
    flash_tokens = 0
    prompts = 0
    parsed_any = False
    try:
        with open(GEMINI_TELEMETRY_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tokens = extract_gemini_tokens(entry, today)
                if tokens:
                    parsed_any = True
                    pro_tokens += tokens.get("pro", 0)
                    flash_tokens += tokens.get("flash", 0)
                    prompts += tokens.get("prompts", 0)
    except (IOError, PermissionError) as e:
        return None, f"Unable to read telemetry: {e}"
    if not parsed_any:
        return None, "no-data"
    return {"pro_tokens": pro_tokens, "flash_tokens": flash_tokens, "prompts": prompts}, None


def extract_gemini_tokens(entry, today):
    # Check date
    entry_date = None
    for key in ("timestamp", "timeUnixNano", "time", "ts", "observedTimeUnixNano"):
        val = entry.get(key)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                if val > 1e18:
                    dt = datetime.fromtimestamp(val / 1e9)
                elif val > 1e12:
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

    # Strategy 1: OTel log attributes
    attrs = entry.get("attributes", {})
    if isinstance(attrs, list):
        attrs = {a.get("key"): a.get("value", {}).get("intValue", a.get("value", {}).get("stringValue", ""))
                 for a in attrs if isinstance(a, dict)}
    for key, val in (attrs.items() if isinstance(attrs, dict) else []):
        if "token" in key.lower():
            found = True
            try:
                token_val = int(val) if not isinstance(val, int) else val
            except (ValueError, TypeError):
                continue
            model = _find_model_name(entry, attrs)
            if "pro" in model:
                pro += token_val
            else:
                flash += token_val

    # Strategy 2: Nested stats
    stats = entry.get("stats", {})
    if isinstance(stats, dict):
        for model_name, model_data in stats.get("models", {}).items():
            total = model_data.get("tokens", {}).get("total", 0) if isinstance(model_data, dict) else 0
            if "pro" in model_name.lower():
                pro += total
                found = True
            elif "flash" in model_name.lower():
                flash += total
                found = True

    # Strategy 3: Metric data points
    if entry.get("name", "").startswith("gemini_cli.token"):
        for dp in entry.get("dataPoints", entry.get("data_points", [])):
            val = dp.get("asInt", dp.get("value", 0))
            dp_attrs = dp.get("attributes", {})
            if isinstance(dp_attrs, list):
                dp_attrs = {a.get("key"): a.get("value", {}).get("stringValue", "") for a in dp_attrs if isinstance(a, dict)}
            model = dp_attrs.get("model", dp_attrs.get("gen_ai.request.model", ""))
            if "pro" in model.lower():
                pro += int(val)
                found = True
            else:
                flash += int(val)
                found = True

    if not found:
        return None
    return {"pro": pro, "flash": flash, "prompts": 1}


def _find_model_name(entry, attrs):
    for key in ("model", "gen_ai.request.model", "modelId"):
        if key in attrs:
            return str(attrs[key]).lower()
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
    print("  CLAUDE CODE")
    claude_data, error = scan_claude_sessions()
    if error:
        print(f"    Unable to read usage data — {error}")
        print(f"    Proceed with caution and monitor quota manually")
        return
    if claude_data is None:
        print(f"    No usage data found this week")
        return

    data["claude"] = claude_data
    save_usage(data)

    weekly_mins = claude_data["weekly_total_mins"]
    weekly_pct = (weekly_mins / (40 * 60)) * 100
    remaining_mins = max(0, 40 * 60 - weekly_mins)
    recent_mins = calculate_recent_window(claude_data["sessions"])
    window_pct = (recent_mins / (5 * 60)) * 100

    warn_window = recent_mins >= CLAUDE_WINDOW_WARN_MINS
    warn_weekly = weekly_mins >= CLAUDE_WEEKLY_WARN_MINS

    tag = f"{RED}prepare handoff soon{NC}" if warn_window else f"{GREEN}OK{NC}"
    print(f"    5-hour window: {format_time(recent_mins)} of ~5h ({window_pct:.0f}%) — {tag}")

    tag = f"{RED}prepare handoff soon{NC}" if warn_weekly else ""
    print(f"    Weekly: {format_time(weekly_mins)} of ~40h ({weekly_pct:.0f}%) — {format_time(remaining_mins)} remaining{' — ' + tag if tag else ''}")

    if show_week and claude_data["sessions"]:
        print()
        print(f"    Weekly breakdown:")
        for session in claude_data["sessions"]:
            print(f"      {session['date']} | {session['project']}: {format_time(session['active_mins'])} ({session['intervals']} intervals)")


def calculate_recent_window(sessions):
    today = get_today()
    return sum(s.get("active_mins", 0) for s in sessions if s.get("date") == today)


def display_gemini_status(data):
    print("  GEMINI CLI")
    telemetry_data, telemetry_error = scan_gemini_telemetry()

    if telemetry_data:
        today = get_today()
        daily_totals = data.setdefault("gemini", {}).setdefault("daily_totals", [])
        found = False
        for entry in daily_totals:
            if entry.get("date") == today:
                entry.update(telemetry_data)
                found = True
                break
        if not found:
            daily_totals.append({"date": today, **telemetry_data})
        save_usage(data)

    gemini_today = get_gemini_today(data)
    pro_tokens = gemini_today.get("pro_tokens", 0)
    flash_tokens = gemini_today.get("flash_tokens", 0)
    pro_pct = (pro_tokens / GEMINI_PRO_DAILY_BUDGET) * 100 if GEMINI_PRO_DAILY_BUDGET > 0 else 0

    if telemetry_data:
        source = "telemetry"
    elif pro_tokens > 0 or flash_tokens > 0:
        source = "manual"
    else:
        source = None

    warn = pro_tokens >= GEMINI_PRO_WARN_TOKENS
    tag = f"{RED}prepare handoff soon{NC}" if warn else f"{GREEN}OK{NC}"
    print(f"    Pro tokens today: {pro_tokens:,} of ~{GEMINI_PRO_DAILY_BUDGET:,} ({pro_pct:.0f}%) — {tag}")
    print(f"    Flash tokens: {flash_tokens:,} (no limit concern)")

    if source:
        print(f"    Source: {source}")
    elif telemetry_error == "no-file":
        print(f"    {DIM}Source: no telemetry — run setup.sh to enable{NC}")
    elif telemetry_error == "no-data":
        print(f"    {DIM}Source: telemetry empty — no usage today{NC}")


def parse_gemini_json(json_str):
    try:
        output = json.loads(json_str)
    except json.JSONDecodeError:
        print("Unable to parse Gemini output — JSON format may have changed")
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


# ============================================================
# UPDATE
# ============================================================

def update_frugent():
    """Pull latest changes from repo and re-run setup."""
    repo_path_file = FRUGENT_DIR / ".repo_path"

    if not repo_path_file.exists():
        print(f"  {RED}Cannot update — repo path not found.{NC}")
        print(f"  Re-install with: cd /path/to/frugent && bash setup.sh")
        sys.exit(1)

    repo_path = repo_path_file.read_text().strip()
    if not Path(repo_path).is_dir():
        print(f"  {RED}Repo not found at {repo_path}{NC}")
        print(f"  Re-install with: cd /path/to/frugent && bash setup.sh")
        sys.exit(1)

    print(f"  {BOLD}Updating Frugent...{NC}")
    print(f"  {DIM}Repo: {repo_path}{NC}")
    print()

    # Git pull
    result = subprocess.run(
        ["git", "pull"], cwd=repo_path, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  {RED}git pull failed:{NC}")
        print(f"  {result.stderr.strip()}")
        sys.exit(1)

    pull_output = result.stdout.strip()
    if "Already up to date" in pull_output:
        print(f"  {GREEN}Already up to date.{NC}")
        return

    print(f"  {GREEN}Pulled latest changes:{NC}")
    print(f"  {DIM}{pull_output}{NC}")
    print()

    # Re-run setup.sh
    setup_script = Path(repo_path) / "setup.sh"
    if not setup_script.exists():
        print(f"  {RED}setup.sh not found in repo{NC}")
        sys.exit(1)

    print(f"  Running setup.sh...")
    print()
    os.execvp("bash", ["bash", str(setup_script)])


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    args = sys.argv[1:]

    # No args → interactive launcher
    if not args:
        launch()
        return

    cmd = args[0]

    if cmd == "status":
        flags = args[1:]
        print()
        if "--claude" in flags:
            display_status(show_claude=True, show_gemini=False, show_week="--week" in flags)
        elif "--gemini" in flags:
            display_status(show_claude=False, show_gemini=True)
        elif "--week" in flags:
            display_status(show_claude=True, show_gemini=True, show_week=True)
        else:
            display_status()
        print()

    elif cmd == "record-gemini":
        if len(args) < 2:
            print("Usage: frugent record-gemini '<json>'")
            sys.exit(1)
        parse_gemini_json(args[1])

    elif cmd == "update":
        update_frugent()

    elif cmd == "init":
        # Quick scaffold without launching an agent
        _scaffold_docs()

    elif cmd in ("help", "--help", "-h"):
        print()
        print(f"  {BOLD}Frugent{NC} — frugal + agent")
        print()
        print(f"  {BOLD}Usage:{NC}")
        print(f"    frugent               Setup project and get start prompt")
        print(f"    frugent status        Quota status for Claude + Gemini")
        print(f"    frugent status --claude/--gemini/--week")
        print(f"    frugent update        Pull latest version and re-install")
        print(f"    frugent init          Scaffold docs/ templates only")
        print(f"    frugent record-gemini JSON   Record Gemini usage (fallback)")
        print(f"    frugent help          Show this help")
        print()

    else:
        print(f"Unknown command: {cmd}")
        print("Run 'frugent help' for usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
