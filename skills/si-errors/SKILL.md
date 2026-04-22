---
name: si:errors
description: Collect all friction events (tool failures, rejections, interrupts, user corrections) from the current session's JSONL transcript. Run before si:improve.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# SI Errors

Extract friction events from the current session transcript, save them as structured JSON, and display a human-readable summary.

## Step 1 — Find the session JSONL

```bash
PROJECT_DIR=$(find ~/.claude/projects -maxdepth 1 -type d -name "*$(basename $PWD)*" | head -1)
SESSION_JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$SESSION_JSONL" .jsonl)
echo "Session: $SESSION_JSONL"
echo "ID: $SESSION_ID"
```

## Step 2 — Extract and save

```bash
mkdir -p ~/.si-improve/error-logs
OUTPUT_PATH=~/.si-improve/error-logs/"$SESSION_ID".json
python3 "${CLAUDE_SKILL_DIR}/extract_session_failures.py" "$SESSION_JSONL" --json \
  > "$OUTPUT_PATH"
echo "Saved: $OUTPUT_PATH"
```

## Step 3 — Display results

```bash
python3 "${CLAUDE_SKILL_DIR}/extract_session_failures.py" "$SESSION_JSONL"
```

Display the human-readable output directly. If no events found, say so.

The structured JSON is saved at `~/.si-improve/error-logs/<session-id>.json` for use by `/si:improve`.
