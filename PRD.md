# PRD — Frugent v2.1
**Product Requirements Document**
Version: 2.1
Status: Draft
Author: Mochamad Zidan Hadipratama

---

## 1. Overview

**Frugent** is a lightweight, multi-agent development operating system that helps solo developers and resource-constrained builders get the most out of free and low-cost AI tools. It works by routing development tasks to the right AI agent (Claude Code, Gemini CLI, or others) based on a **dynamic role mapping** defined by the user. Coordination is managed through a shared set of markdown documents and global skill files.

The name comes from **frugal + agent** — the core philosophy is doing more with less, not doing less.

---

## 2. Problem

AI coding tools are powerful but expensive when used without discipline. Most developers:

- Use one tool for everything, ignoring free-tier alternatives.
- Waste expensive quota on tasks that don't need it.
- Lose context between sessions, forcing agents to re-orient from scratch.
- Have no structured handoff between agents, causing incompatible outputs.
- Run out of quota mid-task with no recovery plan.

Existing solutions are too automated, too token-heavy, and designed for single-tool workflows. Frugent provides a lightweight, multi-tool, cost-aware system built for solo developers on a budget.

---

## 3. Target Users

- Solo developers and indie hackers.
- Students and bootcamp graduates.
- Any developer wanting to reduce AI tool costs without sacrificing quality.

**Primary persona:** A developer with a paid "Pro" agent (e.g., Claude Code) and a free "Executor" agent (e.g., Gemini CLI) who wants to build real projects without exhausting paid quota.

---

## 4. Goals

1. **Maximize Free Tiers:** Use free AI tiers for standard tasks before touching paid quota.
2. **Dynamic Roles:** Allow users to assign specific tools to roles (Planner vs. Executor) per project.
3. **Shared Context:** Maintain context across sessions with minimal token cost via markdown docs.
4. **Structured Handoff:** Ensure clear protocols so agents produce compatible outputs.
5. **Simplicity:** Be simple enough to understand, modify, and own entirely.

---

## 5. Non-Goals (v1)

- Dashboard or progress visualization UI.
- MCP (Model Context Protocol) integration.
- Automated agent spawning or orchestration scripts.
- Any paid tooling or SaaS layer.

---

## 6. Core Workflow (v2.1)

### Phase 0 — Init (The "Handshake")
The developer runs `/frugent-init` inside an agent terminal.
- **Quick init:** Fast scan of project root and scaffolding of `docs/`.
- **Deep init:** For large codebases. One agent (e.g., Gemini) performs a full scan to produce `codebase-analysis.md`, which the primary planner then reads to build the plan.

### Phase 1 — Planning (The "Role Assignment")
The **Planner** (typically the high-tier agent) reads the PRD/SRS and `codebase-analysis.md`, then produces:
- `plan.md` — Phases, features, and tasks with complexity tags (`standard` / `complex`).
- **Role Mapping:** A table defining which tool is assigned to which role for this project.
- `contracts.md` — Agreed interfaces and component boundaries.
- `briefing.md` — The session bootstrap file that tells the *next* agent exactly what to do.

### Phase 2 — Execution (The "Workhorse")
The developer assigns an **Executor** (typically a free-tier agent) to tasks. The agent:
- Reads `briefing.md` and checks the **Role Mapping** to confirm its responsibilities.
- Runs `python ~/.frugent/tracker.py status` to check its current quota.
- Appends progress, blockers, and handoffs to a unified `log.md`.

### Phase 3 — QA & Integration
Features are tested against `test-cases.md`. If complex integration is needed, a high-tier agent is assigned as the **Integrator** to merge work and resolve conflicts.

---

## 7. Dynamic Cost Routing

Frugent uses a **Role Mapping Table** located in `docs/briefing.md` (or `plan.md`). This allows the user to decide which tool is the "high-tier" vs "low-tier" agent.

### Default Role Mapping (Example)
| Role | Recommended Tool | Tier | Responsibility |
|---|---|---|---|
| **Planner** | Claude Code | Paid | Architecture, Planning, Complex logic |
| **Executor** | Gemini CLI | Free | Standard implementation, Boilerplate, Tests |
| **QA** | Codex / Gemini | Free | Testing and reporting |

### Routing Rules:
1. **Executor First:** Default all `standard` tasks to the free-tier Executor.
2. **Escalate Don't Guess:** If an Executor encounters an architectural decision not in the plan, it must stop and raise a `[blocker]` for the Planner.
3. **Intent vs. Implementation:** The Planner specifies *what* and *why* (contracts/logic). The Executor decides *how* (naming/structure). If a plan reads like pseudocode, it is too detailed.

---

## 8. Usage Tracker

Frugent includes `tracker.py` to monitor cross-session usage.
- **Claude Code:** Tracks active query intervals from local JSONL logs.
- **Gemini CLI:** Tracks tokens via OpenTelemetry telemetry (automatic).
- **Codex:** Tracks usage via session logs (if available).

Agents invoke `python ~/.frugent/tracker.py status` at the start of every session as part of their **Global Skill** instructions.

---

## 9. Success Criteria

- Project initialized and scaffolded in under 2 minutes via `/frugent-init`.
- Free-tier agents handle at least 60% of execution tasks.
- Shared context (Briefing/Log) prevents "re-orientation" token waste.
- Usage tracker warns user before hitting 80% of any daily/weekly quota.
