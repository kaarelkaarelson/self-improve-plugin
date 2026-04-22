# self-improve

A Claude Code plugin that turns session failures into durable harness improvements.

Extracts friction events from the current session — tool errors, rejections, interrupts, user corrections — scans your Claude config for gaps, and surgically updates skills and CLAUDE.md files so the same mistakes never happen again.

## Skills

### `/si:errors`

Extracts all friction events from the current session JSONL transcript and saves them as structured JSON. Run this before `/si:improve`.

### `/si:improve`

Analyzes the collected failures, launches parallel harness-scanner subagents to check what's already covered in your config, proposes minimal surgical fixes, and applies approved changes to skills and CLAUDE.md files.

## Install

```bash
claude plugin install https://github.com/kaarelkaarelson/self-improve-plugin
```

## Usage

At the end of a session where you hit friction:

```
/si:errors
/si:improve
```

`/si:errors` extracts and saves the event log. `/si:improve` reads it, analyzes it, and walks you through applying improvements.

## Data

Error logs are stored at `~/.si-improve/error-logs/<session-id>.json`. These are shared between the two skills and are not committed to any repo.

## License

MIT
