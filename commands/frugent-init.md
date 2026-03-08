# Frugent Init

You are initializing this project for the Frugent multi-agent workflow.

## Step 1: Check Quota

Run `python ~/.frugent/tracker.py status` and report the result. If any quota is at 80%+, warn the user and suggest using a different agent.

## Step 2: Scan Project

- Check for existing `docs/` folder with frugent files (plan.md, log.md, briefing.md, contracts.md). If found, stop and tell the user: "This project already has frugent docs. Use /frugent-plan or /frugent-execute instead."
- Check for PRD/SRS in project root and `docs/`. Report what you find.
- Check for existing CLAUDE.md in project root. If found, back it up to `docs/old-CLAUDE.md` and report it.
- Scan project root: read config files (package.json, requirements.txt, pyproject.toml, Cargo.toml, go.mod, etc.), folder structure, and README.

## Step 3: Scaffold Documents

Copy templates from `~/.frugent/templates/` into `docs/`. Create the `docs/` directory if needed. The templates are:
- plan.md, contracts.md, briefing.md, log.md, test-cases.md, qa-report.md, codebase-analysis.md

Do NOT overwrite existing files in `docs/`.

## Step 4: Understand the Project

If a PRD or SRS exists, read them thoroughly.
If `docs/old-CLAUDE.md` exists, read it — it contains the previous project context (architecture, tech stack, conventions).
If neither exists, ask the user: "Want me to generate a PRD from your code, or will you add your own?"

## Step 5: Fill Initial Documents

Based on what you've learned:

1. Fill in `docs/codebase-analysis.md` with: tech stack, project structure, modules/components and their status, existing interfaces, existing tests, dependencies, git state, and what's built vs missing.

2. Fill in `docs/briefing.md` with:
   - Project name and summary
   - Current state (what exists, what's missing)
   - PRD/SRS location (if any)
   - Tech stack overview

3. Append to `docs/log.md`:
   ```
   ## YYYY-MM-DD — [Agent] [progress]
   - **Task completed:** Frugent initialized
   - **Files modified:** docs/ (all templates scaffolded, briefing and codebase-analysis filled)
   - **Next task:** Run /frugent-plan to create the project plan
   ```

## Step 6: Next Steps

Tell the user:
- "Project initialized. Run **/frugent-plan** to create the execution plan."
- If the codebase is large and you only did a surface scan, suggest: "For a deeper analysis, you can run /frugent-init in Gemini CLI (free) to get a more thorough codebase scan, then run /frugent-plan in Claude."
