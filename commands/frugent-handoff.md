# Frugent Handoff

Write a handoff document immediately so another agent or session can resume your work.

## Step 1: Check Current State

Read these files:
1. `docs/plan.md` — what phase and task you're on
2. `docs/log.md` — recent progress entries
3. `docs/briefing.md` — current assignment

## Step 2: Write Handoff

Append a `[handoff]` entry to `docs/log.md`:

```
## YYYY-MM-DD — [Agent] [handoff]
- **Session summary:** what you worked on this session
- **Completed:** list of tasks finished
- **In progress:** exact state of current task (what's done, what's left)
- **Remaining:** tasks still pending from plan.md
- **Files modified:** list every file you changed
- **Known issues:** anything broken, incomplete, or risky
- **Resume instructions:** step-by-step how the next agent should pick up
```

## Step 3: Update Briefing

Update `docs/briefing.md` with:
- Current phase and task state
- Pointer to the handoff entry in log.md
- What the next agent should do first

## Step 4: Confirm

Tell the user: "Handoff written to docs/log.md. Safe to end this session. Next agent should read docs/briefing.md to resume."
