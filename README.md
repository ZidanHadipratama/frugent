# Frugent

**Frugal + Agent** — Multi-agent coordination for solo developers.

Route tasks to the right AI agent based on complexity and dynamic role mapping. Use free tiers (Gemini CLI, Codex) for standard work and paid tiers (Claude Code) for complex architecture. Coordinate through shared markdown documents with **Elite Prompting** guardrails.

## v2.2 Upgrade: Elite Prompting
Frugent now uses advanced prompting techniques inspired by GSD and Google's best practices:
- **XML Task Contracts:** Removing ambiguity with structured `<task>`, `<action>`, and `<verify>` blocks.
- **Dynamic Role Mapping:** Assign any tool (Claude, Gemini, etc.) to any role (Planner, Executor, Integrator) per project.
- **Behavioral Guardrails:** Strict anti-paralysis, no-stub, and 3-attempt limit rules built into every session.
- **Conversational Init:** "Dream Extraction" process to align agents with your vision before planning.
- **Google-Optimized:** Native Gemini support with mandatory Chain-of-Thought (`<thinking>`) and context grounding.

## Install

```bash
git clone https://github.com/ZidanHadipratama/frugent.git
cd frugent
bash setup.sh
```

This installs slash commands, skill files, and templates into `~/.claude/`, `~/.gemini/`, and `~/.codex/`.

Requires Python 3.6+. No pip installs needed.

## Usage

Open any project in Claude Code, Gemini CLI (with native auto-complete), or Codex and use the slash commands:

### 1. Initialize a project
```
/frugent-init
```
Performs a conversational "Dream Extraction" to understand your vision, scans your project, and scaffolds `docs/` with coordination templates.

### 2. Create the plan
```
/frugent-plan
```
Produces an execution plan with **context-capped phases** (3-5 tasks) and **XML task contracts**. Sets up the **Role Mapping Table** for the project.

### 3. Execute tasks
```
/frugent-execute
```
Picks up the next task and executes it with strict behavioral guardrails. Includes a mandatory **Self-Check** phase to verify goals are met.

### 4. Check status
```
/frugent-status
```
Shows grounded status based on documentation, including quota usage, phase progress, and open blockers.

## Documents

All coordination happens through markdown files in `docs/`:

| File | Purpose | Written by |
|------|---------|-----------|
| `plan.md` | Phases, XML tasks, Role Mapping | Planner |
| `contracts.md` | Interface and logic definitions | Planner |
| `briefing.md` | Session bootstrap & active assignment | Any agent |
| `log.md` | Structured progress, handoffs, lessons | Any agent |
| `test-cases.md` | Goal-driven verification specs | Planner |
| `qa-report.md` | Test results | QA |
| `codebase-analysis.md` | Project scan & tech stack | Init agent |

## Supported Agents

| Agent | Role (Configurable) | Format |
|-------|------|------|
| **Claude Code** | Planner / Integrator / Complex Executor | `.md` |
| **Gemini CLI** | Standard Executor (Native Auto-complete) | `.toml` |
| **Codex** | QA / Standard Executor | `.md` |

## What Gets Installed

```
~/.claude/commands/frugent-*.md    ← slash commands (Markdown)
~/.gemini/commands/frugent-*.toml  ← slash commands (Native TOML)
~/.codex/commands/frugent-*.md     ← slash commands (Markdown)
~/.claude/CLAUDE.md                ← session rules
~/.gemini/GEMINI.md                ← session rules
~/.codex/CODEX.md                  ← session rules
~/.frugent/tracker.py              ← quota tracker
~/.frugent/templates/              ← document templates
```

## License

MIT
