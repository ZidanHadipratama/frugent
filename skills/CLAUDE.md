# Frugent — Claude Code Rules

You are part of the Frugent multi-agent system. These rules apply every session.

## Frugent Commands

- **/frugent-init** — Initialize frugent for this project
- **/frugent-plan** — Create or update the execution plan
- **/frugent-execute** — Execute tasks from the plan
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

- If `tracker.py` warns you are at 80%+ of any limit, finish your current task and write a `[handoff]` entry in `docs/log.md`.
- A `[handoff]` entry must include: session summary, what's completed, what's in progress, what's remaining, files modified, and resume instructions.
- Do not start a new complex task if budget is low. Wrap up and hand off.
