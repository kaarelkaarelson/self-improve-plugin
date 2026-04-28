---
date: 2026-04-28
topic: si-create-redesign
---

# si:create Redesign — Empirical Skill Creation

## Problem Frame

The current `si:create` skill is a template filler: ask for a name and purpose, write a SKILL.md, done. Skills produced this way are brittle — they codify the user's intent, not a validated workflow. The result is skills that fail silently or require repeated correction before they work reliably.

The core insight: a skill codified from an empirically attempted workflow is qualitatively better than one written from description alone. Auth walls, missing dependencies, non-obvious ordering constraints — these only surface when you actually try the workflow.

## Requirements

- **R1.** Accept optional `$ARGUMENTS` (skill name, description, or context) upfront. Use whatever is given as a starting point; only ask for what's missing.
- **R2.** Interview the user first — one question at a time — to capture the intended workflow in minimal, generalizable steps before attempting anything.
- **R3.** If context or a topic is given, run a research phase to check whether sufficient documentation, prior skills, or existing patterns already exist.
- **R4.** Classify the skill by verifiability before attempting a trial:
  - **Verifiable** — the skill has a concrete, checkable output (SQL query returns rows, file is created, API responds). Run the full empirical trial.
  - **Non-verifiable** — style guides, best-practice references, judgment-based workflows. The skill self-recommends the most appropriate testing approach (e.g. review by the user, forward-test with a subagent evaluator).
- **R5.** For verifiable skills, attempt the workflow empirically — step by step — before writing any SKILL.md. The trial is the ground truth the skill is built on.
- **R6.** During the trial, detect and document auth walls, setup steps, credential requirements, and ordering constraints. These become the skill's `setup.md` or inline prerequisites section.
- **R7.** When the trial hits a wall it cannot resolve alone, surface it to the user with options: resolve now, skip the wall (document it), or abort.
- **R8.** Learn from trial-and-error: the final SKILL.md must reflect what was actually discovered — including failed paths, dead ends, and the reason the surviving approach was chosen.
- **R9.** After writing the SKILL.md, forward-test it with a fresh subagent context (subagent is given the skill and a real task; does not know it is being tested). The skill must succeed without unnecessary steps.
- **R10.** Present a clean, progressively disclosed UI: one question at a time via `AskUserQuestion`, clear phase labels printed to chat, no walls of text.

## Success Criteria

- A skill created with si:create works end-to-end the first time a user invokes it on a real task.
- Auth walls and setup steps are always documented before the skill is shipped.
- For verifiable skills, the forward-test subagent completes the task without errors and without unnecessary steps.
- The time from invocation to a working skill is no longer than creating one manually — the empirical phase replaces the user's own trial-and-error, not adds to it.

## Scope Boundaries

- si:create does not replace `si:improve`. It creates new skills from scratch; si:improve patches existing ones based on session failures.
- The empirical trial runs in the current session context (not a new terminal). Subagents are used for forward-testing only.
- si:create does not manage skill discovery or the global skills registry — it creates one skill at a time.
- Non-verifiable skills still get a SKILL.md; the empirical trial phase is replaced by a self-recommended alternative (user review, pattern match against existing skills, etc.).

## Key Decisions

- **Interview before trial**: User describes the workflow first; trial validates and extends it. Avoids wasted effort on a dead-end trial.
- **Verifiability gates the trial**: The skill classifies itself by whether its output can be mechanically checked. This avoids forcing expensive empirical runs on reference/knowledge skills.
- **Ask user when trial hits a wall**: No silent fallbacks. The user decides whether to resolve the wall now, document it, or abort.
- **Forward-test is mandatory for verifiable skills**: The skill is not shipped until a fresh subagent can complete the workflow without errors and without empty steps.

## Dependencies / Assumptions

- `writing-claude-skill` skill provides the authoring standard. si:create must invoke it or embed its checklist before writing SKILL.md.
- The `AskUserQuestion` tool must be in `allowed-tools`.
- Trial logs (what was attempted, what failed, what succeeded) should be persisted alongside the skill — either in a `trial-log.md` or embedded as a `setup.md` within the skill directory.

## Outstanding Questions

### Resolve Before Planning

- None.

### Deferred to Planning

- [Affects R6][Technical] Where exactly are trial logs persisted? Options: `<skill-dir>/trial-log.md`, `~/.si-errors/trials/<skill-name>.json`, or embedded as a `setup.md` in the skill directory.
- [Affects R9][Technical] How is the forward-test subagent isolated from the current session context? The subagent must not have access to the trial transcript — it should behave as a fresh user invoking the skill.
- [Affects R4][Needs research] Is there a reliable heuristic for classifying verifiability, or does this always require asking the user?

## Next Steps

→ `/ce:plan` for structured implementation planning
