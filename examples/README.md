# Examples

This directory contains a synthetic Claude Code session transcript with a few common friction events:

- A failed tool call
- A user correction
- An interrupted risky command

Run the extractor against it:

```bash
python skills/si:errors/scripts/extract_session_failures.py examples/session-with-friction.jsonl --json
```

Compare the result with `examples/extracted-failures.json`.

The fixture is synthetic. Do not commit real Claude transcripts; they may contain private code, commands, paths, or secrets.
