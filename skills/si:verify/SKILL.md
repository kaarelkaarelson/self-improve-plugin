---
name: si:verify
description: Verify a si:improve fix by replaying from the failure checkpoint in a fresh subagent. Reports pass/fail without touching the current session. Use after si:improve applies changes, or standalone with a session ID and message index.
argument-hint: "<session-id> <message-index>"
disable-model-invocation: true
allowed-tools: Bash, Read, Agent
---

# SI Verify

Replay a session from a specific failure point in an isolated subagent — with the si:improve fix already on disk — and verify the workflow now completes correctly.

> **Status: stub — full implementation tracked in issue #2.**
> The interface below is stable. Step 4 (subagent injection) is the open implementation question.

## Interface

Called by `si:improve` after Step 5 (Apply Changes):
```
/si:verify <session-id> <message-index>
```

Or standalone by the user to replay any saved checkpoint:
```
/si:verify <session-id> <message-index>
```

## Step 1: Load inputs

Parse `$ARGUMENTS`:
```
SESSION_ID = $ARGUMENTS[0]
MESSAGE_INDEX = $ARGUMENTS[1]
```

If either is missing, check `~/.si-errors/$SESSION_ID-checkpoints.json` for the most recent checkpoint for this session.

If still missing, stop and ask the user for both values.

## Step 2: Locate session JSONL

```bash
SESSION_JSONL=$(find ~/.claude/projects -name "${SESSION_ID}.jsonl" 2>/dev/null | head -1)
echo "Session transcript: $SESSION_JSONL"
```

If not found, stop and report: `"Session JSONL not found for $SESSION_ID"`.

## Step 3: Extract context up to checkpoint

Read the session JSONL and extract all messages up to and including `MESSAGE_INDEX`. This is the context the subagent needs to understand what it was trying to do.

Do not run `si:errors` — the session JSONL is sufficient.

## Step 4: Launch replay subagent

Spawn an Agent with the extracted session context injected as background. The subagent should not know it is being tested.

The subagent's task: attempt the same workflow that failed at `MESSAGE_INDEX`, using whatever skills or CLAUDE.md rules are currently on disk (the fix has already been applied).

> **[Implementation note]**: The exact mechanism for injecting JSONL context into the Agent prompt without leaking the current session is the key open question for issue #2. Options: pass a synthesized summary of the relevant turns, or pass the raw JSONL slice as a context block.

## Step 5: Evaluate result

Verification **passes** when:
- The action completes without errors.
- No unnecessary or empty steps are taken — the workflow is the shortest path to the intended outcome.

Verification **fails** when:
- An error occurs.
- The subagent gets stuck, loops, or takes roundabout steps.
- The output is incomplete.

Verification is **skipped** when:
- The applied fix was to a non-verifiable improvement (style, wording). Report `skipped: non-verifiable change`.

## Step 6: Report

Print the result so `si:improve` can include it in its Step 6 summary:

```
si:verify result
  Session:       <session-id>
  Checkpoint:    message <index>
  Outcome:       pass / fail / skipped
  Reason:        <one line>
```

Save the checkpoint record to `~/.si-errors/<session-id>-checkpoints.json`:

```json
{
  "sessionId": "<session-id>",
  "messageIndex": <index>,
  "verifiedAt": "<ISO timestamp>",
  "outcome": "pass | fail | skipped",
  "reason": "<one line>"
}
```
