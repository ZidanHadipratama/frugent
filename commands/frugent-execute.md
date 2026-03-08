# Frugent Execute

You are executing tasks using the Frugent v2.2 "Elite Prompting" workflow.

## Step 1: Quota & Context Check
Run `python ~/.frugent/tracker.py status`. Read `docs/briefing.md`, `docs/plan.md`, and `docs/log.md`.
**MANDATORY:** Always start your analysis with: "Based on the information in the provided documentation..."

## Step 2: The 4 Deviation Rules (MANDATORY)
If you encounter an unexpected situation, follow these rules in order:
1. **Auto-Fix Bugs:** If it's a small implementation bug in YOUR code, fix it immediately and try again.
2. **Stop for Architecture:** If the fix requires an architectural change or a new library not in `plan.md`, raise a `[blocker]` and stop.
3. **3-Attempt Limit:** If a bug or task fails 3 times, raise a `[blocker]` with a detailed post-mortem and wait for instructions.
4. **No Hallucination:** If a library or file is missing, do not assume it's there. Verify first.

## Step 3: Operational Guardrails
- **Anti-Paralysis:** If you read >5 files without an action, stop and explain why.
- **No Stubs:** Never write `// TODO` or stubs. Implementation must be complete.
- **No Scope Creep:** Only work on the assigned task in `briefing.md`.

## Step 4: Execute
Implement the task as defined in the XML `<task>` block in `plan.md`.
**Chain-of-Thought:** Before writing code, provide a 1-2 sentence rationale inside a `<thinking>` block.

## Step 5: Mandatory Self-Check (Verification)
Before marking as `done`, you must verify the `<verify>` criteria from the task contract.
Check:
1. Do the files exist and are they correctly named?
2. Does the code compile/run?
3. Are all imports/exports wired?
4. Does it fulfill the goal, not just the task?

## Step 6: After Task Completion
1. Mark the task as `done` in `docs/plan.md`.
2. Append a `[progress]` entry to `docs/log.md`.
3. Update `docs/briefing.md` for the next role/session.

## Step 7: Next Task
Run `python ~/.frugent/tracker.py status`. If quota is OK, continue to the next task in the phase. If the phase is done, tell the user.

## Critical Checklist (Enforce these last)
1. **No Stubs:** Implementation must be complete.
2. **CoT First:** Thinking block before action.
3. **Verify:** Use the `<verify>` criteria from the task contract before finishing.
