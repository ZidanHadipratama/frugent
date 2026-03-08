# Frugent — Claude Code Rules

You are part of the Frugent multi-agent system. These rules apply every session.

## Frugent Commands

- **/frugent-init** — Initialize frugent for this project
- **/frugent-plan** — Create or update the execution plan
- **/frugent-execute** — Execute tasks from the plan
- **/frugent-handoff** — Write handoff document for session end
- **/frugent-status** — Check quota and project state

## During Work

- After completing a task, append a `[progress]` entry to `docs/log.md`:
  ```
  ## YYYY-MM-DD — Claude [progress]
  - **Task completed:** what you did
  - **Files modified:** list of files
  - **Next task:** what comes next
  ```
- If stuck, immediately append a `[blocker]` entry to `docs/log.md`. Do NOT hallucinate a solution.
- If you think of something out of scope, append a `[suggestion]` entry to `docs/log.md`. Do NOT implement it.
- Do not implement features outside your assigned task.

## Quota Awareness

**Per-session (native):** After completing every task and before starting the next:
1. Check your context window usage
2. If context is getting large (long conversation, many files read) → run /frugent-handoff and stop
3. If you notice degraded performance → run /frugent-handoff immediately

**Cross-session:** Run `python ~/.frugent/tracker.py status` to check accumulated usage across all sessions.
- If at 80%+ of any limit → finish current task, run /frugent-handoff, and stop
- Do not start a new complex task if budget is low
