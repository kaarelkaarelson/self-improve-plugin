---
name: si:verify
description: Verify a si:improve fix by replaying from the failure checkpoint in a fresh subagent. Reports pass/fail without touching the current session. Use after si:improve, or standalone with a session ID and message index.
argument-hint: "<session-id> <message-index>"
disable-model-invocation: true
allowed-tools: Bash, Read, Agent
---

# SI Verify

Replay a session failure point in an isolated subagent — with the si:improve fix already on disk — and verify the workflow now completes correctly.

## Step 0: Resolve config root

```bash
if bash "${CLAUDE_SKILL_DIR}/../si:root/scripts/check.sh"; then
  source "$HOME/.claude/skills/si:root/cache.sh"
else
  echo "Root not resolved — invoke /si:root first."
  exit 1
fi
```

## Step 1: Load inputs

Parse `$ARGUMENTS`:

```bash
SESSION_ID=$(echo "$ARGUMENTS" | awk '{print $1}')
MESSAGE_INDEX=$(echo "$ARGUMENTS" | awk '{print $2}')
echo "Session: $SESSION_ID"
echo "Checkpoint: message $MESSAGE_INDEX"
```

If `SESSION_ID` is empty, stop and ask the user for `<session-id> <message-index>`.

If `MESSAGE_INDEX` is empty, check `~/.si-errors/${SESSION_ID}-checkpoints.json` for the most recent entry and use its `messageIndex`. If still missing, stop and report.

## Step 2: Locate session JSONL

```bash
SESSION_JSONL=$(find "$SI_CLAUDE_ROOT/projects" -name "${SESSION_ID}.jsonl" 2>/dev/null | head -1)
if [ -z "$SESSION_JSONL" ]; then
  echo "ERROR: Session JSONL not found for $SESSION_ID"
  exit 1
fi
echo "Transcript: $SESSION_JSONL"
```

## Step 3: Extract conversation context

Read the JSONL up to `MESSAGE_INDEX` and extract the last 30 meaningful turns:

```bash
python3 - <<PYEOF
import json, sys

jsonl_path = "$SESSION_JSONL"
stop_at = $MESSAGE_INDEX

lines = []
with open(jsonl_path) as f:
    for i, line in enumerate(f):
        if i > stop_at:
            break
        try:
            lines.append(json.loads(line.strip()))
        except Exception:
            pass

turns = []
for obj in lines[-30:]:
    t = obj.get("type")
    if t == "user":
        msg = obj.get("message", {})
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        if isinstance(content, str) and content.strip():
            text = content.strip()
            if not text.startswith("<command-") and not text.startswith("Base directory"):
                turns.append({"role": "user", "text": text[:600]})
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    text = c.get("text", "").strip()
                    if text and not text.startswith("<command-") and not text.startswith("Base directory"):
                        turns.append({"role": "user", "text": text[:600]})
    elif t == "assistant":
        msg = obj.get("message", {})
        content = msg.get("content", []) if isinstance(msg, dict) else []
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                    turns.append({"role": "assistant", "text": c["text"].strip()[:600]})
                    break

print(json.dumps(turns, indent=2))
PYEOF
```

From the extracted turns, synthesize three things in memory:
1. **User intent** — what was the user trying to accomplish?
2. **Failure** — what went wrong? (last error or friction before the checkpoint)
3. **Workflow** — what skill, command, or step was being attempted?

If the context is too sparse to synthesize these, report `skipped: insufficient context at checkpoint` and stop.

## Step 4: Launch replay subagent

Build a prompt using the synthesized context. Do not pass raw JSONL, the current session, or any hint that this is a test.

```
Agent(
  description: "Verify: <workflow>",
  prompt: "Prior context: A user was working on the following task.

<paste the last 5-8 user turns as a brief narrative, e.g.:
  'The user wanted to [intent]. They ran /some-skill and encountered [failure description].'
>

A fix has since been applied. Your task: attempt the same workflow now and report whether it works.

Task: <restate the user intent as a concrete action>

Report each step you take. If it succeeds, say so clearly. If it fails, describe the error."
)
```

The subagent has full access to all skills and CLAUDE.md on disk. The fix is already in place — do not apply anything yourself.

## Step 5: Evaluate result

Review the subagent's report:

**Pass** — all of:
- The action completed without errors.
- No unnecessary or empty steps (not retrying things that should work, not asking for already-known info).
- The workflow is the shortest path to the outcome.

**Fail** — any of:
- An error occurred.
- The subagent got stuck, looped, or took roundabout steps.
- The output was incomplete or incorrect.

**Skipped** — when:
- Context was too sparse to synthesize a meaningful replay prompt.
- The applied fix was non-verifiable (style change, wording tweak with no checkable output).

## Step 6: Save checkpoint and report

Save the result to `~/.si-errors/${SESSION_ID}-checkpoints.json`:

```bash
python3 - <<PYEOF
import json, os
from datetime import datetime, timezone

path = os.path.expanduser(f"~/.si-errors/$SESSION_ID-checkpoints.json")
existing = []
if os.path.exists(path):
    with open(path) as f:
        try:
            existing = json.load(f)
        except Exception:
            existing = []

existing.append({
    "sessionId": "$SESSION_ID",
    "messageIndex": $MESSAGE_INDEX,
    "verifiedAt": datetime.now(timezone.utc).isoformat(),
    "outcome": "OUTCOME_PLACEHOLDER",
    "reason": "REASON_PLACEHOLDER"
})

with open(path, "w") as f:
    json.dump(existing, f, indent=2)
print(f"Checkpoint saved: {path}")
PYEOF
```

Replace `OUTCOME_PLACEHOLDER` and `REASON_PLACEHOLDER` with the actual outcome and reason before writing.

Print the final result so `si:improve` can include it in its Step 6 summary:

```
si:verify result
  Session:    <session-id>
  Checkpoint: message <index>
  Outcome:    pass / fail / skipped
  Reason:     <one line>
```
