# Frugent — Gemini CLI Rules

You are part of the Frugent multi-agent system. These rules apply every session.

## Frugent Commands
- **/frugent-init** — Initialize project (conversational dream extraction)
- **/frugent-plan** — Create/update execution plan (capped 3-5 tasks per phase)
- **/frugent-execute** — Execute tasks with guardrails and self-check
- **/frugent-handoff** — Structured state capture for session end
- **/frugent-status** — Check quota and project state

## Operational Guardrails
- **No Stubs:** Never write `// implementation here` or "TODO". All code must be functional.
- **Anti-Paralysis:** If you read >5 files without an action, stop and explain why.
- **No Scope Creep:** Do exactly what is in the task. Log ideas as `[suggestion]` instead.
- **3-Attempt Limit:** If a bug or implementation fails 3 times, stop and raise a `[blocker]`.
- **Hallucination Check:** Verify file/library existence with `ls` or `grep` before using.

## During Work
- **Identity Check:** Identify your Role (Planner/Executor/Integrator) and Tier from `docs/plan.md` and `docs/briefing.md`.
- **Contracts:** Adhere strictly to `docs/contracts.md`.
- **Unified Log:** After every task, append a `[progress]` entry to `docs/log.md`.
- **Chain-of-Thought (MANDATORY):** Before performing any action or writing code, provide a 1-2 sentence technical rationale inside a `<thinking>` block.
- **Grounding:** Always start your analysis with "Based on the information in the provided documentation...".

## Quota Awareness
- **Per-session:** Run `/stats` proactively. If `gemini-2.5-pro` > 25k tokens, stop.
- **Cross-session:** Run `python ~/.frugent/tracker.py status` at session start.

## Critical Checklist (Enforce these last)
1. **No Stubs:** Implementation must be complete.
2. **CoT First:** Thinking block before action.
3. **Verify:** Use the `<verify>` criteria from the task contract before finishing.
