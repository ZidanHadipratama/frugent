# Frugent

**Frugal + Agent** — a lightweight multi-agent coordination system for solo developers who want to get the most out of free and low-cost AI tools.

Frugent routes development tasks between Claude Code (paid, for planning and complex work) and Gemini CLI (free, for implementation), coordinated through shared markdown documents. No runtime, no server, no UI — just skill files, templates, and conventions.

## Why

- You're paying $20/month for Claude Pro and don't want to waste quota on boilerplate
- Gemini CLI is free but needs clear instructions to produce good results
- You lose context between sessions and agents start from scratch every time
- There's no structured handoff when you hit quota limits mid-task

Frugent fixes all of this with a set of markdown files that agents read and write.

## Install

```bash
git clone git@github.com:ZidanHadipratama/frugent.git /tmp/frugent
bash /tmp/frugent/setup.sh
```

This installs:
- `~/.claude/CLAUDE.md` — planner skill for Claude Code
- `~/.gemini/GEMINI.md` — executor skill for Gemini CLI
- `~/.frugent/tracker.py` — usage tracker (agent-invoked)
- `~/.frugent/templates/` — document templates

Requires Python 3.6+. No pip installs needed.

## Quick Start

### New project

1. Open Claude Code in your project directory
2. Say: **"Init frugent for this project"**
3. Claude will ask which mode you want:
   - **Quick** — fast scan of your project, scaffolds docs, ready to work
   - **Deep** — Gemini scans the full codebase first (free), Claude plans from the analysis
   - **Skip** — just copy the templates, you'll fill them in yourself
4. Claude produces `plan.md`, `contracts.md`, `briefing.md`, and `test-cases.md` in `docs/`
5. Open Gemini CLI and start working on tasks tagged `standard` in the plan

### Existing project

Same as above. Use **deep init** for large codebases — Gemini does the heavy analysis for free, then Claude reads the result and plans from it.

## How It Works

```
Developer → Claude Code (planner) → docs/plan.md, contracts.md, briefing.md
         → Gemini CLI (executor) → reads briefing, implements, updates log.md
         → Claude Code (complex) → handles tasks tagged "complex"
```

### Documents (in `docs/`)

| File | Purpose | Written by |
|---|---|---|
| `plan.md` | Phases, tasks, assignments, complexity tags | Claude (planner) |
| `contracts.md` | Interfaces between components | Claude (planner) |
| `briefing.md` | Session bootstrap — what to work on, budget, blockers | Claude (planner) |
| `log.md` | Append-only log: progress, blockers, handoffs, suggestions | Any agent |
| `test-cases.md` | What to test per feature | Claude (planner) |
| `qa-report.md` | Test results | QA agent or developer |
| `codebase-analysis.md` | Full codebase scan (deep init only) | Gemini CLI |

### Cost Routing

Every task is tagged `standard` or `complex`:

| Tag | Routed to | Examples |
|---|---|---|
| `standard` | Gemini CLI (free) | CRUD, UI components, boilerplate, tests |
| `complex` | Claude Code (paid) | Architecture, AI logic, ambiguous requirements |

### Usage Tracking

Agents automatically check quota at session start by running:
```bash
python ~/.frugent/tracker.py status
```

Output:
```
CLAUDE CODE
  5-hour window: 2h 30m of ~5h (50%) — OK
  Weekly: 18h 00m of ~40h (45%) — 22h 00m remaining

GEMINI CLI
  Pro tokens today: 12,000 of ~30,000 (40%) — OK
  Flash tokens: 45,000 (no limit concern)
  Source: telemetry
```

**How tracking works:**
- **Claude:** Reads Claude Code's local JSONL logs (already written by Claude) to calculate active time
- **Gemini:** `setup.sh` configures Gemini CLI's built-in OpenTelemetry to write token usage to `~/.frugent/gemini-telemetry.jsonl` — fully automatic, no wrapper needed
- **Fallback:** If telemetry is unavailable, you can manually record usage with `tracker.py record-gemini '<json>'`

When limits approach, agents write a `[handoff]` entry in `log.md` so the next session can resume without losing progress.

## Project Structure

```
frugent/
├── setup.sh                ← installer
├── skills/
│   ├── CLAUDE.md           ← planner skill
│   └── GEMINI.md           ← executor skill
├── tracker/
│   └── tracker.py          ← usage tracker
├── templates/              ← document templates (7 files)
├── PRD.md                  ← product requirements
└── SRS.md                  ← software requirements
```

## Requirements

- Python 3.6+
- Claude Code (Claude Pro subscription)
- Gemini CLI (free tier)

## License

MIT
