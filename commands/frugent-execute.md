# Frugent Execute

You are executing tasks for this project using the Frugent multi-agent workflow.

## Step 1: Check Quota

Run `python ~/.frugent/tracker.py status` and report the result. If any quota is at 80%+:
- Finish only your current in-progress task (if any)
- Write a `[handoff]` entry in `docs/log.md` with: session summary, what's completed, what's in progress, what's remaining, files modified, and resume instructions
- Tell the user to continue with a different agent or in a new session
- STOP — do not start new work

## Step 2: Read Context

Read these files:
1. `docs/briefing.md` — current state and assignment
2. `docs/plan.md` — phases, tasks, and assignments
3. `docs/contracts.md` — interfaces you must follow
4. `docs/log.md` — check for recent `[handoff]` or `[blocker]` entries

If `docs/plan.md` doesn't exist or has no tasks, stop and tell the user: "Run /frugent-plan first."

## Step 3: Determine What to Work On

Check `docs/log.md` for the latest entry:
- If there's an open `[handoff]`, resume from where it left off
- If there's an unresolved `[blocker]`, address it or escalate
- Otherwise, find the next `pending` task in `docs/plan.md`

### Task Routing (important!)
- If you are **Gemini CLI or Codex** (free tier): only work on tasks tagged `standard`. If the next pending task is `complex`, skip it and tell the user: "Next task is complex — run /frugent-execute in Claude."
- If you are **Claude Code** (paid tier): work on tasks tagged `complex`. You CAN also work on `standard` tasks if no complex tasks are pending.

Tell the user which task you're about to work on and confirm before starting.

## Step 4: Execute

- Follow contracts in `docs/contracts.md` exactly
- Stay within your assigned task — do not implement features outside scope
- If you encounter something architecturally significant not covered by contracts → STOP and raise a `[blocker]`:
  ```
  ## YYYY-MM-DD — [Agent] [blocker]
  - **Task attempted:** what you were doing
  - **Blocker type:** ambiguity / technical / dependency / environment
  - **What's needed:** what information or action would unblock this
  - **Severity:** blocking / degraded / minor
  ```
- If you think of something out of scope, append a `[suggestion]` entry to `docs/log.md`. Do NOT implement it.

## Step 5: After Each Task

1. Mark the task as `done` in `docs/plan.md`
2. Append a `[progress]` entry to `docs/log.md`:
   ```
   ## YYYY-MM-DD — [Agent] [progress]
   - **Task completed:** what you did
   - **Files modified:** list of files
   - **Next task:** what comes next
   ```
3. Update `docs/briefing.md` with current state for the next session/agent

## Step 6: Check Quota Again

Run `python ~/.frugent/tracker.py status` again. If quota is still OK, ask: "Continue with the next task?" If the user says yes, go back to Step 3.

If quota is nearing limits, write a `[handoff]` entry and stop.

## Step 7: Phase Complete

When all tasks in a phase are done:
1. Update `docs/plan.md` — mark the phase as complete
2. Append a `[progress]` entry noting phase completion
3. Tell the user: "Phase N complete. Run /frugent-execute to start the next phase, or /frugent-plan to re-plan."
