# Frugent Status

Show the current project state and quota.

## Quota

Run `python ~/.frugent/tracker.py status` and report the result clearly.

## Project State

Read these files and summarize:
1. `docs/briefing.md` — current phase, task, and assignment
2. `docs/log.md` — last 3 entries (show timestamps, agent, and what happened)
3. `docs/plan.md` — count of tasks by status (done / pending) and phase progress

Report:
- Current phase and progress (e.g., "Phase 2: 5/8 tasks done")
- Last activity (from log.md)
- Any unresolved `[blocker]` entries
- Any open `[handoff]` entries
- Quota status for both Claude and Gemini

If `docs/` doesn't exist, tell the user: "No frugent project found. Run /frugent-init to set up."
