# Frugent Plan

You are creating the execution plan for this project using the Frugent multi-agent workflow.

## Step 1: Check Quota

Run `python ~/.frugent/tracker.py status` and report the result. If quota is at 80%+, write a `[handoff]` entry in `docs/log.md` instead of planning — include what needs to happen and hand off to the next session.

## Step 2: Read Context

Read these files in order:
1. `docs/briefing.md` — current project state
2. `docs/log.md` — recent activity, blockers, handoffs
3. PRD and/or SRS if they exist (check `docs/`, project root, or README)
4. `docs/codebase-analysis.md` — if it exists (from /frugent-init)
5. `docs/old-CLAUDE.md` — if it exists (previous project context)

If `docs/briefing.md` doesn't exist, stop and tell the user: "Run /frugent-init first."

## Step 3: Produce plan.md

Fill in `docs/plan.md` with:
- **Project summary** (1 paragraph)
- **Phase list** with goals per phase
- **Per phase:** features → tasks → complexity tag (`standard` or `complex`)
- **Dependency map** (what must be done before what)
- **Agent assignment** per task: `standard` → Gemini/Codex (free), `complex` → Claude (paid)

For existing projects with work already done, mark completed work as "Phase 0 (done)" and new work starts at Phase 1.

### Complexity Tagging Rules
- Default everything to `standard` unless it genuinely requires architectural thinking or AI logic
- `standard`: CRUD, UI components, boilerplate, repetitive logic, tests, styling, config
- `complex`: architecture decisions, AI/ML logic, cross-cutting integration, ambiguous requirements, security-critical code

### Planning Detail Level
Plan to the level of **intent**, not implementation. Specify:
- Function names and purpose
- Input and output types
- Business logic rules
- Which library to use and why
- Edge cases that must be handled

Do NOT specify: variable names, control flow, file structure, or how to call libraries. If your plan reads like pseudocode, it is too detailed. The executor agent owns implementation decisions.

## Step 4: Produce contracts.md

Fill in `docs/contracts.md` with interface definitions for each component boundary:
- Name and purpose
- Request/input shape
- Response/output shape
- Error cases
- Which agent owns this component

## Step 5: Produce test-cases.md

Fill in `docs/test-cases.md` with test cases per feature:
- Test ID, feature being tested, input, expected output, edge cases, pass criteria

## Step 6: Update briefing.md

Update `docs/briefing.md` with:
- Current phase and first task to execute
- Agent assignment for next task
- Known blockers (from log.md)
- Quota budget summary

## Step 7: Log and Next Steps

Append to `docs/log.md`:
```
## YYYY-MM-DD — [Agent] [progress]
- **Task completed:** Project plan created
- **Files modified:** docs/plan.md, docs/contracts.md, docs/test-cases.md, docs/briefing.md
- **Next task:** Run /frugent-execute to start Phase 1
```

Tell the user:
- Summary of phases and task count
- How many tasks are `standard` (free) vs `complex` (paid)
- "Run **/frugent-execute** to start executing. Use Gemini/Codex for standard tasks (free), Claude for complex tasks."
