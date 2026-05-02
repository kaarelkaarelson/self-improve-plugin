---
name: si:create
description: "Create a skill empirically — interview, trial, auth-wall detection, then codify what worked. Use when adding to ~/.claude/skills/."
argument-hint: "[optional: skill name, description, or topic]"
disable-model-invocation: true
allowed-tools: AskUserQuestion, Bash, Read, Write, Grep, Glob, Agent
---

# Create Skill

Create a new personal Claude Code skill in `~/.claude/skills/` by empirically validating the workflow before codifying it. Interview first, attempt second, write third.

## Step 0: Setup check

Read setup state through the shared `si:setup` helper:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
python3 "$MAIN_REPO/skills/si:setup/scripts/state.py" status
```

If the output is `missing`, print:

```
Run /si:setup first — it wires CLAUDE-si.md into your config (takes ~30 seconds).
Then re-run /si:create.
```

Then stop. Do not proceed.

If `ok`, hold `claude_root`, `claude_md`, `claude_si_md`, and `skills_dir` from the JSON in memory. Use these in place of any re-detected paths in subsequent steps.

## Step 1: Resolve config root

```bash
CLAUDE_ROOT=$(readlink -f ~/.claude 2>/dev/null || realpath ~/.claude 2>/dev/null || echo "$HOME/.claude")
SKILLS_DIR="$CLAUDE_ROOT/skills"
echo "Skills dir: $SKILLS_DIR"
```

If Step 0 returned setup state, use its `claude_root` and `skills_dir` values instead of re-detecting. Otherwise use the resolved `CLAUDE_ROOT` for all file operations throughout this skill.

## Step 2: Intake

Read `$ARGUMENTS`. Extract any skill name, description, or topic provided.

Print to chat:
```
Context from arguments: <what was extracted, or "none">
```

## Step 3: Research (if context given)

If context was extracted in Step 2, before interviewing:

1. List existing skills to check for overlap:
   ```bash
   ls "$SKILLS_DIR"
   ```
2. If any existing skill name looks related, read its SKILL.md briefly.
3. Note overlap or gaps.

Print one line: `"Found similar: X"` or `"No existing skill covers this."` Then continue.

## Step 4: Interview

Use `AskUserQuestion` — one call per question. Skip questions already answered by `$ARGUMENTS`.

Ask in order:

1. **Purpose**: "What should this skill do, and what would make you invoke it?"
2. **Name**: "What's a good short name? (lowercase, hyphens only — e.g. `process-invoices`)"
3. **Verifiability**: "Does this skill produce a concrete, checkable result — something you can verify worked? For example: a file is created, a query returns rows, an API responds successfully."
4. **Auto-invoke**: "Should Claude automatically add this skill as a trigger rule in CLAUDE-si.md so it self-invokes when conditions match — without you typing the command? (yes / no)"

   Hold the resolved value (`true` or `false`) in memory as `auto_invoke` for Step 8.

Hold all interview answers in memory for all remaining steps.

## Step 5: Classify and plan

Based on the interview answers:

**Verifiable** — the skill has a concrete, checkable output:
→ Proceed to Step 6 (empirical trial).

**Non-verifiable** — style guide, best-practice reference, judgment-based workflow:
→ Skip Step 6. Note in the SKILL.md body which testing approach fits best:
  - Forward-test with a subagent evaluator (agent attempts the task, output is reviewed for quality)
  - User review after first use

Print to chat:
```
Skill type:  verifiable / non-verifiable
Trial:       will run / skipping (<reason>)
```

## Step 6: Empirical trial (verifiable skills only)

Attempt the workflow step by step to discover what actually works — including auth walls, ordering constraints, and non-obvious dependencies.

### Protocol

For each step in the workflow:
1. Attempt it with Bash or the appropriate tool.
2. Record the outcome: success, error, or wall.
3. If it fails with a resolvable error (wrong flag, missing package), fix it and retry.
4. If an auth wall or external blocker is hit, stop and ask the user:

```
AskUserQuestion: "The trial hit a wall at step N: [describe wall]
How should I proceed?
A) Resolve it now — tell me what to do
B) Document it as a setup prerequisite and continue past it
C) Abort — this skill isn't ready to be created yet"
```

### Trial log

Maintain a running log in memory:

| Step | Action | Outcome | Notes |
|------|--------|---------|-------|
| 1 | … | success / error / wall | … |

Print the completed trial log to chat before continuing.

### Outcome

- **All steps succeeded**: Proceed to Step 7.
- **Some walls documented (user chose B)**: Proceed to Step 7; walls become `setup.md`.
- **Aborted (user chose C)**: Stop. Print what was learned. Do not create a skill.

## Step 7: Read authoring standard

Before writing anything, read:
```bash
cat "$SKILLS_DIR/writing-claude-skill/SKILL.md"
```

Apply its audit checklist when writing the skill in Step 8.

## Step 8: Write the skill

### Create directory

```bash
mkdir -p "$SKILLS_DIR/<name>"
```

### Write SKILL.md

Create `$SKILLS_DIR/<name>/SKILL.md` using:
- **Frontmatter**:
  - `name`: the chosen slug
  - `description`: under 130 chars, third person, front-load trigger keywords, include both what and when
  - `disable-model-invocation: true`
  - `allowed-tools`: list only tools the skill actually needs
- **Body** (imperative form):
  - Steps in the empirically proven order
  - Trial-discovered prerequisites before step 1
  - Failed approaches omitted — keep only what worked
  - Under 500 lines

### Register trigger in CLAUDE.md (if auto_invoke is true)

If the remembered `auto_invoke` value is `true`:

1. Derive the trigger condition from the skill's purpose (interview Step 4, question 1). One line, trigger-action format.

2. Run `scripts/register_trigger.py` from this skill's directory:

```bash
python3 "$SKILLS_DIR/si:create/scripts/register_trigger.py" "<trigger-condition>" "<skill-name>"
```

### Create setup.md (if walls were hit)

If the trial uncovered auth walls or required setup steps, create `$SKILLS_DIR/<name>/setup.md`:
- One section per wall: what it is, exact steps to resolve, credentials or URLs needed
- Reference it from SKILL.md: `"Complete [setup.md](setup.md) before first use."`

## Step 9: Forward-test (verifiable skills only)

Launch an isolated subagent to validate the skill from a fresh context:

```
Agent(
  description: "Forward-test: <skill-name>",
  prompt: "Use the skill file at <SKILLS_DIR>/<name>/SKILL.md to <concrete task that matches what the skill does>.

Report what you did step by step and whether it worked."
)
```

Do not tell the subagent it is being tested. Do not give it the expected output.

Evaluate the result:
- **Pass**: Task completed without errors. No unnecessary or empty steps. Workflow is the shortest path to the result.
- **Fail**: Errors occurred, steps were skipped, or output was incomplete. Update SKILL.md to fix the gap. Re-test once.

Print:
```
Forward-test: pass / fail / skipped (non-verifiable)
Reason: <one line>
```

## Step 10: Report

Print to chat:

```
Skill created: ~/.claude/skills/<name>/SKILL.md
Setup docs:   ~/.claude/skills/<name>/setup.md  (if applicable)

Trial:         <N steps attempted, M walls documented>  (or "skipped — non-verifiable")
Forward-test:  pass / fail / skipped

Invoke with:  /<name>
```

Show the full SKILL.md content so the user can verify it looks right.
