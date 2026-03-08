# SRS — Frugent v2.1
**Software Requirements Specification**
Version: 2.1
Status: Draft
Author: Mochamad Zidan Hadipratama

---

## 1. System Overview

Frugent is a **file-based multi-agent coordination system**. It has no runtime or server. It consists of:

- **Skill Files:** Markdown instructions installed globally in agent config folders.
- **Slash Commands:** Markdown files with detailed execution steps for agent tools.
- **Shared Documents:** A `docs/` folder containing the project's coordination documents.
- **Tracker:** A Python script to monitor cross-session usage.

---

## 2. System Architecture

```
~/.frugent/
├── tracker.py               ← Usage tracker script
├── frugent.py               ← Update and status utility
├── templates/               ← Markdown document templates
└── usage.json               ← Usage tracking database

~/.claude/CLAUDE.md          ← Planner/Complex Executor skill
~/.gemini/GEMINI.md          ← Standard Executor skill
~/.claude/commands/          ← Slash command instruction files
~/.gemini/commands/          ← Slash command instruction files

your-project/
└── docs/
    ├── plan.md              ← Unified plan and role mapping table
    ├── briefing.md          ← Next task and current assignment
    ├── log.md               ← Unified progress, blockers, and handoffs
    ├── contracts.md         ← Interface and logic contracts
    ├── codebase-analysis.md ← Deep scan results (from Init)
    ├── test-cases.md        ← Specification for QA
    └── qa-report.md         ← Results from QA runs
```

---

## 3. Skill File Requirements

Agents must adhere to these rules regardless of which tool is used.

- **Identity Check:** At the start of every session, identify your **Role** (Planner, Executor, or Integrator) and **Cost Tier** by reading `docs/plan.md` and `docs/briefing.md`.
- **Quota Check:** Run `python ~/.frugent/tracker.py status` at session start. If a model's budget is > 80% used, warn the developer and suggest a handoff.
- **Read Briefing First:** Never start work without reading the current task in `docs/briefing.md`.
- **Unified Log:** After every task, append a `[progress]` entry to `docs/log.md`.
- **Immediate Blockers:** If you are stuck or encounter an unplanned architectural decision, append a `[blocker]` entry to `docs/log.md` and stop.
- **Handoff Before Exhaustion:** If your context window or quota is low, write a `[handoff]` entry and stop.

---

## 4. Slash Command Specifications

Slash commands are instruction sets for agents to perform specific Frugent workflows.

### `/frugent-init` (Project Setup)
1. **Quota Check:** Run `python ~/.frugent/tracker.py status`. Warn if limits are near.
2. **Detection:** Scan project root for stack, PRD/SRS, and existing `docs/`.
3. **Scaffold:** Create `docs/` and copy templates from `~/.frugent/templates/`.
4. **Initial Scan:** Perform a surface scan of the codebase to populate `codebase-analysis.md`.
5. **Briefing:** Create initial `briefing.md` for the Planner.
6. **Git:** Initialize git if not already present.

### `/frugent-plan` (Planning)
1. **Requirements:** Read PRD/SRS and `codebase-analysis.md`.
2. **Plan Generation:** Create `plan.md` with features, tasks, and complexity tags.
3. **Role Mapping:** Define which tool is assigned to which role in a table within `plan.md`.
4. **Interface Contracts:** Define component boundaries in `contracts.md`.
5. **First Briefing:** Update `briefing.md` for the first feature/task.

### `/frugent-execute` (Task Execution)
1. **Context:** Read the assigned task from `briefing.md`.
2. **Contracts:** Read `contracts.md` to ensure architectural compliance.
3. **Execution:** Implement the task.
4. **Log:** Append a `[progress]` entry to `log.md` with files modified.

### `/frugent-handoff` (Session End)
1. **Summary:** Describe the current state, what was completed, and what remains.
2. **Log:** Append a `[handoff]` entry to `log.md`.
3. **Next Steps:** Update `briefing.md` for the next session/agent to resume correctly.

---

## 5. Document Specifications (Key Files)

### 5.1 plan.md (The Unified Source)
- **Role Mapping Table:** Maps Tools (Claude/Gemini/etc) to Roles (Planner/Executor).
- **Phases:** Features and tasks with complexity tags (`standard` / `complex`).
- **Dependency Map:** Order of task execution.

### 5.2 briefing.md (The "Pulse")
- **Current Task:** Exactly what the agent should work on next.
- **Assignment:** Which role/tool is currently active.
- **Last Completed:** Reference to the most recent entry in `log.md`.

### 5.3 log.md (The History)
- **[progress]:** Daily/Task-based logs of what was done.
- **[blocker]:** Issues preventing progress.
- **[handoff]:** Instructions for the next session.
- **[suggestion]:** Out-of-scope ideas.

---

## 6. Usage Tracker (`tracker.py`)

- **Role:** Central repository for cross-session token and time usage.
- **Claude:** Parses local JSONL session logs (`~/.claude/projects/`).
- **Gemini:** Reads local telemetry logs (`~/.frugent/gemini-telemetry.jsonl`).
- **Data:** Stored in `~/.frugent/usage.json`.

---

## 7. Definition of Done

A task is complete when:
1. Code is implemented and tested locally.
2. `[progress]` entry is recorded in `log.md`.
3. `briefing.md` is updated for the next task or a `[handoff]` is provided.
4. No architectural blockers remain open for that task.
