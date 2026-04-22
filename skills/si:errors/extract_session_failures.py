"""Extract failures, corrections, and steering from a Claude Code session JSONL.

Usage:
    python extract_session_failures.py <session.jsonl> [--json]

Default output: human-readable timeline
With --json: structured JSON to stdout (pipe to file as needed)
"""

import json
import sys


def extract_text(content):
    """Pull plain text from a message content field."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return " ".join(parts)
    return ""


def get_tool_use_from_assistant(lines, tool_use_id):
    """Find the assistant tool_use call that matches a tool_use_id."""
    for idx, d in enumerate(lines):
        if d.get("type") != "assistant":
            continue
        msg = d.get("message", {})
        content = msg.get("content", []) if isinstance(msg, dict) else []
        if not isinstance(content, list):
            continue
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("id") == tool_use_id:
                intent = _find_assistant_intent(lines, idx, content)
                return {
                    "tool": c.get("name", ""),
                    "input": c.get("input", {}),
                    "uuid": d.get("uuid", ""),
                    "intent": intent,
                }
    return None


def _find_assistant_intent(lines, tool_use_line_idx, tool_use_content):
    """Get the assistant's text explaining what it's about to do."""
    # Check same message for text blocks before the tool_use
    for c in tool_use_content:
        if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
            return c["text"].strip()[:300]
    # Check the preceding assistant message
    for j in range(tool_use_line_idx - 1, max(tool_use_line_idx - 3, -1), -1):
        d = lines[j]
        if d.get("type") != "assistant":
            continue
        msg = d.get("message", {})
        content = msg.get("content", []) if isinstance(msg, dict) else []
        if not isinstance(content, list):
            continue
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                return c["text"].strip()[:300]
        break
    return None


def find_preceding_tool_context(lines, from_index):
    """Walk backward from an interrupt to find the tool_result and its tool_use."""
    for j in range(from_index - 1, max(from_index - 4, -1), -1):
        d = lines[j]
        if d.get("type") != "user":
            continue
        msg = d.get("message", {})
        content = msg.get("content", []) if isinstance(msg, dict) else []
        if not isinstance(content, list):
            continue
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_result":
                tool_use_id = c.get("tool_use_id", "")
                tool_context = get_tool_use_from_assistant(lines, tool_use_id) if tool_use_id else None
                return {
                    "tool_use_id": tool_use_id,
                    "tool_call": tool_context,
                    "tool_result_content": str(c.get("content", ""))[:500],
                    "was_error": bool(c.get("is_error")),
                }
    return None


def find_next_user_message(lines, from_index):
    """Find the next substantive user message after a given index."""
    for i in range(from_index + 1, min(from_index + 5, len(lines))):
        d = lines[i]
        if d.get("type") != "user":
            continue
        text = extract_text(
            d.get("message", {}).get("content", "") if isinstance(d.get("message"), dict) else d.get("content", "")
        ).strip()
        if len(text) > 10 and not text.startswith("<command-") and not text.startswith("Base directory"):
            return text[:300]
    return None


CORRECTION_SIGNALS = [
    "no ", "not that", "wrong", "stop", "too specific",
    "actually", "wait ", "why not", "why did", "did you",
    "should be", "must be", "I want", "I do not want",
    "is this", "how could", "can you confirm",
]


def extract(path):
    with open(path) as f:
        lines = [json.loads(line) for line in f]

    events = []

    for i, d in enumerate(lines):
        if d.get("type") != "user":
            continue

        msg = d.get("message", {})
        content = msg.get("content", "") if isinstance(msg, dict) else d.get("content", "")
        timestamp = d.get("timestamp", "")

        # --- Tool failures ---
        if isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue

                tool_use_id = c.get("tool_use_id", "")
                tool_context = get_tool_use_from_assistant(lines, tool_use_id) if tool_use_id else None
                follow_up = find_next_user_message(lines, i)

                if c.get("type") == "tool_result" and c.get("is_error"):
                    error_text = str(c.get("content", ""))
                    kind = "REJECTED" if "was rejected" in error_text or "doesn't want to proceed" in error_text else "ERROR"
                    events.append({
                        "line": i,
                        "category": "tool_failure",
                        "kind": kind,
                        "timestamp": timestamp,
                        "error": error_text[:500],
                        "tool_use_id": tool_use_id,
                        "tool_call": tool_context,
                        "tool_use_result": d.get("toolUseResult", ""),
                        "user_follow_up": follow_up,
                    })

                elif c.get("type") == "text" and "Request interrupted" in c.get("text", ""):
                    preceding = find_preceding_tool_context(lines, i)
                    # Deduplicate: if the preceding tool_result already fired as REJECTED/ERROR, skip
                    if preceding and preceding["was_error"] and any(
                        e.get("tool_use_id") == preceding["tool_use_id"] for e in events
                    ):
                        continue
                    event = {
                        "line": i,
                        "category": "tool_failure",
                        "kind": "INTERRUPTED",
                        "timestamp": timestamp,
                        "error": c.get("text", "")[:300],
                        "user_follow_up": follow_up,
                    }
                    if preceding:
                        event["tool_use_id"] = preceding["tool_use_id"]
                        event["tool_call"] = preceding["tool_call"]
                        event["tool_result_content"] = preceding["tool_result_content"]
                    events.append(event)

        # --- User corrections ---
        text = extract_text(content).strip()
        if len(text) < 10:
            continue
        if text.startswith("<command-") or text.startswith("Base directory"):
            continue
        if "tool_result" in str(content) and not any(s in text.lower() for s in CORRECTION_SIGNALS):
            continue

        lower = text.lower()
        if any(signal in lower for signal in CORRECTION_SIGNALS):
            events.append({
                "line": i,
                "category": "user_correction",
                "kind": "CORRECTION",
                "timestamp": timestamp,
                "message": text[:500],
            })

    events.sort(key=lambda x: x["line"])
    return {
        "session_jsonl": path,
        "total_lines": len(lines),
        "total_events": len(events),
        "tool_failures": len([e for e in events if e["category"] == "tool_failure"]),
        "user_corrections": len([e for e in events if e["category"] == "user_correction"]),
        "events": events,
    }


def print_human(result):
    print("=" * 60)
    print(f"Session: {result['session_jsonl']}")
    print(f"Lines: {result['total_lines']} | Events: {result['total_events']} "
          f"(tool: {result['tool_failures']}, corrections: {result['user_corrections']})")
    print("=" * 60)

    for e in result["events"]:
        kind = e["kind"]
        line = e["line"]

        if e["category"] == "tool_failure":
            tool_call = e.get("tool_call")
            tool_desc = ""
            if tool_call:
                tool_name = tool_call.get("tool", "?")
                inp = tool_call.get("input", {})
                if tool_name == "Bash":
                    tool_desc = f" → {tool_name}({inp.get('command', '')[:80]})"
                elif tool_name == "Edit":
                    tool_desc = f" → {tool_name}({inp.get('file_path', '')[:60]})"
                else:
                    tool_desc = f" → {tool_name}"

            print(f"\n  [{kind}] Line {line}{tool_desc}")
            if tool_call and tool_call.get("intent"):
                print(f"    Intent: {tool_call['intent'][:150]}")
            print(f"    Error: {e['error'][:150]}")
            if e.get("user_follow_up"):
                print(f"    User then: {e['user_follow_up'][:120]}")

        elif e["category"] == "user_correction":
            print(f"\n  [{kind}] Line {line}")
            print(f"    {e['message'][:200]}")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <session.jsonl> [--json]")
        sys.exit(1)

    result = extract(sys.argv[1])

    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
