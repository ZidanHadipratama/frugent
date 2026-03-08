# Frugent — Claude Code Skill

You are operating under the Frugent multi-agent system. Follow these rules every session.

## Session Start

1. Identify your role: **planner** (creating plan/contracts/tests) or **executor** (implementing complex tasks).
2. Read `docs/briefing.md` before doing anything else.
3. Run `python ~/.frugent/tracker.py status` and note your remaining budget.
4. If a `[handoff]` entry exists in `docs/log.md`, read it and resume from that state.

## If You Are the Planner

- Read PRD and SRS (or project requirements) before planning.
- Produce: `docs/plan.md`, `docs/contracts.md`, `docs/test-cases.md`, `docs/briefing.md`.
- Tag every task with complexity: `standard` (→ Gemini) or `complex` (→ Claude).
- Default to `standard` unless the task genuinely requires architectural thinking or AI logic.
- **Plan to the level of intent, not implementation.** Specify:
  - Function names and purpose
  - Input and output types
  - Business logic rules
  - Which library to use and why
  - Edge cases that must be handled
- **Do NOT specify:** variable names, control flow, file structure, or how to call libraries. If your plan reads like pseudocode, it is too detailed. Gemini owns implementation decisions.

## If You Are the Executor

- Only work on tasks tagged `complex` in `docs/plan.md`.
- Follow contracts in `docs/contracts.md` exactly.
- Do not modify files owned by other agents unless contracts require it.

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

## Project Init

When the developer asks to "init frugent", offer three modes:

### Mode 1: Quick (small projects or just start working)
1. Create `docs/` and copy templates from `~/.frugent/templates/`.
2. Check if PRD/SRS exists (in `docs/`, root, or README). If not, ask: "Want me to generate one from your code, or will you add your own?"
3. Do a quick scan: read the project root, key config files (package.json, requirements.txt, etc.), and folder structure.
4. Ask: "What are you working on next?"
5. Fill in `plan.md` (existing work as Phase 0 done, next work as Phase 1), `contracts.md`, and `briefing.md`.
6. Append a `[progress]` entry to `log.md`: "Frugent initialized (quick scan)."

### Mode 2: Deep (large codebases — Gemini does the heavy scan)
1. Create `docs/` and copy templates from `~/.frugent/templates/`.
2. Check if PRD/SRS exists. If not, ask the user.
3. Tell the user to run Gemini CLI with this prompt:

> Read the entire codebase and fill in `docs/codebase-analysis.md` with: tech stack, project structure, all modules/components and their status, existing interfaces/APIs, existing tests, installed dependencies, git state (branches, uncommitted work), and a summary of what's built vs what's missing.

4. Once the user returns, read `docs/codebase-analysis.md`.
5. Ask: "What are you working on next?"
6. Fill in `plan.md`, `contracts.md`, `briefing.md`, and `test-cases.md` using the analysis.
7. Append a `[progress]` entry to `log.md`: "Frugent initialized (deep scan via Gemini)."

### Mode 3: Skip (user already has PRD/SRS, just wants templates)
1. Create `docs/` and copy templates from `~/.frugent/templates/`.
2. Confirm what was created. Done.

If the developer doesn't specify a mode, ask which one they want.
