# PRD — Frugent v1
**Product Requirements Document**
Version: 2.0
Status: Draft
Author: Mochamad Zidan Hadipratama

---

## 1. Overview

**Frugent** is a lightweight, multi-agent development operating system that helps solo developers and resource-constrained builders get the most out of free and low-cost AI tools. It works by routing development tasks to the right AI agent (Claude Code or Gemini CLI) based on task complexity, coordinated through a shared set of markdown documents and skill files.

The name comes from **frugal + agent** — the core philosophy is doing more with less, not doing less.

---

## 2. Problem

AI coding tools like Claude Code and Gemini CLI are powerful but expensive when used without discipline. Most developers:

- Use one tool for everything, ignoring free-tier alternatives
- Waste expensive quota on tasks that don't need it
- Lose context between sessions, forcing agents to re-orient from scratch every time
- Have no structured handoff between agents, causing incompatible outputs
- Run out of quota mid-task with no recovery plan

Existing solutions are too automated, too token-heavy, and designed for single-tool workflows. There is no lightweight, multi-tool, cost-aware system built for solo developers on a budget.

---

## 3. Target Users

- Solo developers and indie hackers
- Students and bootcamp graduates
- Early-stage startup founders
- Any developer wanting to reduce AI tool costs without sacrificing output quality

**Primary persona:** A developer with Claude Pro ($20/month) and Gemini CLI free tier who wants to build real projects without running out of quota mid-way.

---

## 4. Goals

1. Maximize use of free AI tiers before touching paid quota
2. Maintain shared context between agents across sessions with minimal token cost
3. Provide clear handoff protocols so agents don't produce incompatible outputs
4. Give developers visibility into what each agent is doing and what's been done
5. Be simple enough to understand, modify, and own entirely

---

## 5. Non-Goals (v1)

- Dashboard or progress visualization UI
- MCP (Model Context Protocol) integration
- Automated agent spawning or orchestration scripts
- Any paid tooling or SaaS layer
- Support for tools beyond Claude Code and Gemini CLI (Codex support is v2)
- User-facing CLI commands — the developer works entirely within agent terminals

---

## 6. Core Workflow (v1)

### Phase 0 — Init (Developer + Claude Code)

The developer runs "init frugent" inside Claude Code. Three modes are available:

**Quick init** — for small projects or when you want to start immediately. Claude does a fast scan of project root, config files, and folder structure, then scaffolds docs and asks what to work on next.

**Deep init** — for existing codebases that need full understanding. Claude scaffolds docs, then tells the developer to run Gemini CLI to analyze the entire codebase (free). Gemini writes `codebase-analysis.md`. Developer returns to Claude, who reads the analysis and produces the plan.

**Skip init** — for projects that already have PRD/SRS. Just copies templates into `docs/`. No scanning.

In all modes, Claude checks for existing PRD/SRS. If none found, it asks: "Want me to generate one from your code, or will you add your own?"

### Phase 1 — Planning (Claude Code as Planner)
Claude Code reads PRD/SRS (and `codebase-analysis.md` if deep init was used), then produces:
- `plan.md` — phases, features, tasks broken down with complexity tags
- `contracts.md` — agreed interfaces between components
- `test-cases.md` — what QA will test per feature
- `briefing.md` — session bootstrap for the executor agent

For existing projects, prior work is captured as "Phase 0 (done)" and new work starts at Phase 1.

### Phase 2 — Execution (Developer assigns, Agents execute)
Developer tells Gemini CLI (or Claude Code for complex tasks) to start working. Each agent:
- Reads `briefing.md` at session start
- Runs `python ~/.frugent/tracker.py status` to check quota budget
- Clarifies its task before executing
- Appends entries to `log.md` after each task (progress, blockers, handoffs)
- Raises blockers immediately in `log.md` if stuck

### Phase 3 — QA (Developer + Agent)
After a feature is complete, developer tests against `test-cases.md` or asks an agent to run tests. Results go to `qa-report.md`.

### Phase 4 — Retrospective
After each phase, developer writes a short retro entry in `log.md` capturing what worked, what didn't, and what to improve next phase.

---

## 7. Cost Routing Rules

Every task is tagged by complexity: `standard` or `complex`.

| Task type | Routed to | Examples |
|---|---|---|
| `standard` | Gemini CLI (free) | CRUD, UI components, boilerplate, repetitive logic, tests |
| `complex` | Claude Code (paid) | Architecture, AI logic, cross-cutting integration, ambiguous requirements |

**Key rules:**
1. **Gemini first** — default all tasks to Gemini unless tagged complex
2. **Claude for complexity** — architecture, AI logic, integration, and review
3. **Escalate don't guess** — if Gemini encounters something architecturally significant, it stops and raises a blocker in `log.md` rather than deciding alone
4. **Handoff before exhaustion** — any agent approaching quota limits writes a handoff entry in `log.md` before the session ends

**Planning detail level:** Claude plans to the level of intent and contracts — function names, input/output types, business logic rules, libraries to use, and edge cases to handle. If a plan reads like pseudocode, it's too detailed. Gemini retains implementation ownership within the agreed contracts.

---

## 7a. Usage Tracker

Frugent includes a Python script at `~/.frugent/tracker.py` that monitors both Claude Code and Gemini CLI usage, warning before hitting quota limits.

**This is not a user-facing CLI.** Agents invoke it themselves via shell command as instructed by their skill files. The developer can also run it manually if they want, but the primary workflow is agent-invoked.

**Claude Code tracking:**
Reads Claude's local JSONL logs at `~/.claude/projects/` to calculate active query-to-response intervals. Idle time is excluded. Warns at 4 hours of 5-hour window and 35 hours of 40-hour weekly cap.

**Gemini CLI tracking:**
Parses `--output-format json` output from Gemini CLI to get per-model token counts, broken down separately for `gemini-2.5-pro` and `gemini-2.5-flash`. Only Pro tokens are tracked against the daily budget.

**Agent invocation:**
Agents run `python ~/.frugent/tracker.py status` at session start and report the result. Skill files instruct agents to do this automatically.

**Auto-reset:** Weekly counters reset automatically when a new week is detected. No manual reset needed.

**Graceful degradation:** If Claude's JSONL format changes or Gemini's output format changes, the tracker reports "unable to read" rather than crashing or giving wrong numbers.

**Data stored at:** `~/.frugent/usage.json`

**Limitation:** Claude active time is an approximation. Gemini Pro daily budget (~30,000 tokens) is an observed estimate, not an officially published limit.

---

## 8. Success Criteria (v1)

- A developer can set up Frugent globally once and use it on any project
- A full project can be planned, executed, and QA'd using the document system with no custom tooling
- Gemini CLI free tier handles at least 60% of execution tasks
- Claude Code quota is reserved for planning, complex logic, and integration
- No agent ever starts a session without reading its briefing first
- No agent goes silent when stuck — blockers are always raised in log.md
- Usage tracker warns before hitting limits when invoked by agents

---

## 9. Out of Scope but Noted for v2

- Codex agent support and QA skill file
- `dashboard.md` — single status view across all agents
- Automated briefing regeneration after log.md updates
- MCP-based agent-to-agent communication
- Shell scripts for project scaffolding
- Conflict resolution automation
- Codex usage tracking
- User-facing CLI with subcommands
