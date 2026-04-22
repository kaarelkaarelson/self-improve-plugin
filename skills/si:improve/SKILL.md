---
name: si:improve
description: Analyze session failures and compound learnings into skill and CLAUDE.md improvements. Prevents repeating the same mistake twice. Use after encountering errors, workarounds, or friction during a session.
argument-hint: "[optional: focus area or failure description]"
disable-model-invocation: true
---

# Self-Improve

Analyze the current session for failures, errors, and friction, then surgically update skills and CLAUDE.md files so the same mistakes never happen again.

**Principle:** Never make the same mistake twice. Every session failure is an opportunity to compound knowledge into durable instructions.

## Step 1: Discovery

Resolve the canonical Claude config root before doing anything else. `~/.claude` may be a symlink (e.g. to `~/dotfiles/claude`). Always resolve it — never assume the path. Use the resolved root in place of `~/.claude` for all file reads, writes, and searches throughout this skill.

Also check for a project CLAUDE.md at `.claude/CLAUDE.md` relative to the current working directory.

Print both resolved paths to the chat before proceeding:

```
Global CLAUDE.md: <resolved path>
Project CLAUDE.md: <resolved path or "None">
```

Hold both in memory and use whichever is appropriate in subsequent steps. Searches in Step 3 must cover both.

## Step 2: Failure Analysis

### Step 2a: Load collected errors

Run `/si:errors` first if it hasn't been run yet.

Check the current session context for a path printed by `/si:errors` (format: `Error log saved: ~/.si-errors/<session-id>.json`). If found, use that path directly.

If not found, derive the session ID and look for the file:

```bash
PROJECT_DIR=$(find ~/.claude/projects -maxdepth 1 -type d -name "*$(basename $PWD)*" | head -1)
SESSION_JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$SESSION_JSONL" .jsonl)
ERROR_LOG=~/.si-errors/"$SESSION_ID".json
echo "Error log: $ERROR_LOG"
```

Read the JSON file. It contains structured events covering the entire session including parts lost to context compaction.

### Step 2b: Analyze the timeline

Work through the timeline chronologically. For each event, classify it:

- **Corrections and steering** (highest value): user redirected the approach, said something was wrong or too specific, rejected a tool call, or provided information that should have been known. These represent judgment failures.
- **Technical failures**: commands that errored, wrong CLI flags, shell quoting issues. These are usually one-off and obvious.
- **Hard-won workflows**: multi-step tasks that required significant trial-and-error or user steering to complete — where the general pattern would be valuable to remember.

Prioritize corrections over technical errors. The natural bias is to report technical failures because they're unambiguous, but user steering is where the compoundable learning lives.

### Step 2c: Extract findings

For each friction event worth compounding, extract:
- **What happened**: the concrete error or friction event
- **Root cause**: why it happened (missing knowledge, wrong assumption, missing guard, etc.)
- **What would have prevented it**: the specific instruction or check that would eliminate this class of failure

### Step 2d: Output findings as a table

Print the findings to the chat before proceeding:

| # | What happened | Root cause | What would have prevented it | Worth improving? |
|---|---------------|------------|------------------------------|-----------------|
| 1 | …             | …          | …                            | Yes / No        |

**Worth improving?** rubric:
- **Yes** — repeated pattern, cost meaningful time, or caused the user to steer/correct course
- **No** — one-off (typo, wrong flag, context-specific mistake unlikely to recur)

This table is required output — do not skip it or collapse it into prose. Only rows marked **Yes** proceed to Step 3. **No** rows are logged here and skipped entirely.

## Step 3: Harness Scan (parallel)

For each row marked **Yes** in the Step 2d table, launch one harness-scanner subagent in parallel. All agents run simultaneously — do not wait for one before launching the next.

**Subagents return text data only. They must not write, edit, or create any files.**

### Prompt for each subagent

Pass each agent:
1. The issue row (what happened, root cause, what would have prevented it)
2. The canonical config root resolved in Step 1
3. The project CLAUDE.md path resolved in Step 1 (or None)

Instruct each agent to search the entire canonical config root for any content related to this issue — CLAUDE.md and its includes, rules, skills, and plugins — and also search the project CLAUDE.md if it exists.

Return a structured text report:
- **Related files found**: list of file paths and the relevant excerpt
- **Verdict**: one of:
  - `missing` — the harness has nothing about this; the failure is completely unguided
  - `partial` — something exists but is incomplete, ambiguous, or missing the specific guard that would have prevented this
  - `wrong` — an existing instruction actively steered toward the wrong behavior
- **Notes**: any cross-issue overlaps noticed (e.g. two issues pointing at the same skill file)

### Orchestrator classification

Once all subagent reports are returned, classify each issue into exactly one bucket using the verdict as a guide:

| Verdict | Likely bucket |
|---------|--------------|
| `missing` | Bucket 2 (global rule) or Bucket 3 (new skill) |
| `partial` or `wrong` | Bucket 1 (edit existing skill or CLAUDE.md) |

Cross-compare all reports before finalising — if two issues point at the same file, group them into one change.

For each classified issue, draft the minimal proposed fix: the smallest surgical change that would have prevented the failure.

## Step 4: User Review

Present findings using AskUserQuestion. For each failure:

1. State the failure concisely (1-2 sentences)
2. State the proposed fix and where it goes (which file, what change)
3. Ask whether to apply, skip, or modify

Group related failures into a single question when they target the same file.

**Format for each finding:**

```
Failure: [what went wrong]
Root cause: [why]
Proposed fix: [bucket type] — [target file]
Change: [the specific text to add/modify]
```

Ask one AskUserQuestion with up to 4 findings at a time. If there are more than 4, batch them across multiple rounds.

For each finding, the options are:
- **Apply** — make the change as proposed
- **Skip** — not worth compounding
- **Modify** — user will provide adjusted wording

## Step 5: Apply Changes

For each approved change, read the target file and apply the minimal surgical edit — a fix, improvement, or new workflow as needed. Only touch what is necessary to solve the issue. Do not restructure or modify surrounding content unless it is absolutely required to make the change work.

When the approved change introduces a new workflow skill, check both the global and project CLAUDE.md (if it exists) for a `## Custom skills @self-improve` section. Add the one-line invocation rule to whichever is most appropriate — project CLAUDE.md if the skill is project-specific, global otherwise. Create the section at the bottom of the target file if it doesn't exist.

## Step 6: Report

Print a summary to the chat:

```
Self-Improve Complete

Applied:
  - [file]: [one-line description of change]

Skipped:
  - [failure]: [reason]

Session failures analyzed:  N
Existing skills improved:   N
Global CLAUDE.md improved:  N
Local CLAUDE.md improved:   N
New skills created:         N
```

## Rules

1. Never edit a file without reading it first — both for understanding and to respect writing-claude-md/skill guidelines
2. Minimal edits only — do not restructure, reformat, or "improve" surrounding content (Chesterton's Fence)
3. Every proposed change must trace back to a concrete session failure — no speculative improvements
4. Trigger-action format for all CLAUDE.md additions — "WHEN X, do Y" not vague principles
5. Do not add rules that Claude already follows by default — only add what failed
6. If a failure is trivial (typo, one-off mistake), skip it — only compound patterns worth preventing
7. Prefer skill edits over CLAUDE.md edits — skills load on demand and do not consume instruction budget
8. When in doubt about bucket classification, prefer Bucket 1 > Bucket 2 > Bucket 3 (edit existing > global rule > new skill)
