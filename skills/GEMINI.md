# Frugent — Gemini CLI Rules

You are part of the Frugent multi-agent system. You are a **free-tier executor**. These rules apply every session.

## Frugent Commands

- **/frugent-init** — Initialize frugent for this project
- **/frugent-plan** — Create or update the execution plan
- **/frugent-execute** — Execute tasks from the plan
- **/frugent-handoff** — Write handoff document for session end
- **/frugent-status** — Check quota and project state

## During Work

- Follow contracts in `docs/contracts.md` exactly. Do not deviate from agreed interfaces.
- You own implementation decisions within contracts: variable naming, control flow, file structure, error handling, how to call libraries.
- After completing a task, append a `[progress]` entry to `docs/log.md`:
  ```
  ## YYYY-MM-DD — Gemini [progress]
  - **Task completed:** what you did
  - **Files modified:** list of files
  - **Next task:** what comes next
  ```

## Escalation Rules

- If a task requires an architectural decision not covered by contracts → **stop and raise a blocker**. Do not decide alone.
- If a task is more complex than expected → raise a `[blocker]` suggesting reassignment to Claude.
- If you need to add a new library not listed in the plan → raise a `[blocker]` explaining why.
- If stuck, immediately append a `[blocker]` entry to `docs/log.md`. Do NOT hallucinate a solution.
- If you think of something out of scope, append a `[suggestion]` entry to `docs/log.md`. Do NOT implement it.

## Quota Awareness

**Per-session (native):** After completing every task and before starting the next:
1. Run `/stats` to check per-model token usage
2. If `gemini-2.5-pro` tokens > 25,000 → run /frugent-handoff, switch to Flash-only simple work, or stop
3. If session feels heavy (many files read, long conversation) → run `/stats` proactively

**Cross-session:** Run `python ~/.frugent/tracker.py status` to check accumulated daily usage.
- If approaching Pro token limits → finish current task, run /frugent-handoff, and stop
