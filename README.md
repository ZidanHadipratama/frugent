# Frugent

**Frugal + Agent** — Multi-agent coordination for solo developers.

Route tasks to the right AI agent based on complexity. Use free tiers (Gemini CLI, Codex) for standard work, paid (Claude Code) for complex work. Coordinate through shared markdown documents.

## Install

```bash
git clone https://github.com/ZidanHadipratama/frugent.git
cd frugent
bash setup.sh
```

This installs slash commands, skill files, and templates into `~/.claude/`, `~/.gemini/`, and `~/.codex/`.

Requires Python 3.6+. No pip installs needed.

## Update

```bash
cd /path/to/frugent
git pull
bash setup.sh
```

## Usage

Open any project in Claude Code, Gemini CLI, or Codex and use the slash commands:

### 1. Initialize a project

```
/frugent-init
```

Scans your project, scaffolds `docs/` with coordination templates, and fills in the initial codebase analysis. Backs up your existing CLAUDE.md if present.

### 2. Create the plan

```
/frugent-plan
```

Reads your PRD/SRS and codebase analysis, then produces:
- `docs/plan.md` — phases, tasks, complexity tags, agent assignments
- `docs/contracts.md` — interface definitions between components
- `docs/test-cases.md` — what to test per feature
- `docs/briefing.md` — session bootstrap for the next agent

### 3. Execute tasks

```
/frugent-execute
```

Picks up the next task from the plan and executes it. Handles:
- Task routing: `standard` tasks → Gemini/Codex (free), `complex` → Claude (paid)
- Progress logging to `docs/log.md`
- Automatic handoff when quota is low
- Resume from previous handoffs

### 4. Check status

```
/frugent-status
```

Shows quota usage (Claude hours + Gemini tokens), phase progress, blockers, and handoffs.

## How It Works

```
/frugent-init          → Scan project, scaffold docs/
/frugent-plan          → PRD/SRS → plan.md, contracts.md, test-cases.md
/frugent-execute       → Pick task → implement → log progress → repeat
/frugent-status        → Quota + progress check
```

**Cost routing:** Every task is tagged `standard` or `complex`.
- `standard` → Gemini CLI or Codex (free) — CRUD, UI, boilerplate, tests
- `complex` → Claude Code (paid) — architecture, AI logic, integration

**Quota tracking:** Agents check `~/.frugent/tracker.py` before and after work. If quota is low, they write a handoff document so the next agent (or session) can pick up.

**Handoff protocol:** When switching agents or running low on quota, the current agent writes a `[handoff]` entry in `docs/log.md` with: what's done, what's in progress, what's remaining, and how to resume.

## Documents

All coordination happens through markdown files in `docs/`:

| File | Purpose | Written by |
|------|---------|-----------|
| `plan.md` | Phases, tasks, assignments | Planner |
| `contracts.md` | Interface definitions | Planner |
| `briefing.md` | Session bootstrap | Any agent |
| `log.md` | Progress, blockers, handoffs | Any agent |
| `test-cases.md` | What to test | Planner |
| `qa-report.md` | Test results | QA |
| `codebase-analysis.md` | Project scan | Init agent |

## Supported Agents

| Agent | Role | Cost |
|-------|------|------|
| Claude Code | Planner + complex executor | Paid |
| Gemini CLI | Standard executor | Free |
| Codex | Standard executor | Free |

## What Gets Installed

```
~/.claude/commands/frugent-*.md    ← slash commands
~/.gemini/commands/frugent-*.md    ← slash commands
~/.codex/commands/frugent-*.md     ← slash commands
~/.claude/CLAUDE.md                ← session rules
~/.gemini/GEMINI.md                ← session rules
~/.codex/CODEX.md                  ← session rules
~/.frugent/tracker.py              ← quota tracker
~/.frugent/templates/              ← document templates
```

## Requirements

- Python 3.6+
- At least one of: Claude Code, Gemini CLI, Codex

## License

MIT
