# Frugent — Claude Code Rules

You are part of the Frugent multi-agent system. These rules apply every session.

## Frugent Commands
- **/frugent-init** — Initialize project (conversational dream extraction)
- **/frugent-plan** — Create/update execution plan (capped 3-5 tasks per phase)
- **/frugent-execute** — Execute tasks with guardrails and self-check
- **/frugent-handoff** — Structured state capture for session end
- **/frugent-status** — Check quota and project state

## Operational Guardrails (Strict Enforcement)
- **No Stubs:** Never write `// implementation here` or "TODO". All code must be functional or clearly marked as a blocker.
- **Anti-Paralysis:** If you read >5 files without an action (edit/test/run), stop and explain why. If stuck in a loop, raise a `[blocker]`.
- **No Scope Creep:** Do exactly what is in the task. Do not "fix" unrelated files or add unrequested features. Log ideas as `[suggestion]` instead.
- **3-Attempt Limit:** If a bug or implementation fails 3 times, stop. Raise a `[blocker]` with a detailed post-mortem and ask for a new strategy.
- **Hallucination Check:** Never assume a library or file exists. Verify with `ls` or `grep` before importing/using.

## During Work
- **Identity Check:** Identify your Role (Planner/Executor/Integrator) and Cost Tier from `docs/plan.md` and `docs/briefing.md`.
- **Contracts:** Adhere strictly to `docs/contracts.md`.
- **Unified Log:** Append `[progress]` to `docs/log.md` after every task.
- **Immediate Blockers:** Raise `[blocker]` for any unplanned architectural decision or ambiguity.

## Quota Awareness
- **Per-session:** Check context window usage. If getting large, run /frugent-handoff and stop.
- **Cross-session:** Run `python ~/.frugent/tracker.py status` at session start. If budget > 80% used, warn and suggest handoff.
