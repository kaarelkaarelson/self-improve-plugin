# self-improve

> Never let your Claude Code make the same mistake twice.

Your Claude Code agent makes more mistakes than you notice. A task done in 15 tool calls that should have taken 2. A correction you gave last session, forgotten by the next. These mistakes have a price — every redundant tool call, every repeated correction burns tokens, wasting >10,000 tokens per day on work the agent should already know how to do.

None of it gets fixed. The next session starts fresh.

`self-improve` closes the loop. At the end of a session, it extracts every friction event from the transcript, scans your Claude config for what's missing or wrong, and surgically updates your skills and CLAUDE.md so the same failure class doesn't recur.

## Why this matters

Error correction is the foundational principle behind every reliable computing system. TCP allowed the internet to reliably transmit information by detecting and retransmitting every lost packet. Quantum Error Correction (QEC) made reliable quantum computing possible by correcting the noise that makes physical qubits fail.

LLM coding agents have no equivalent layer. Each session is a fresh unreliable component with no accumulated corrections. Mistakes surface, get corrected, and then vanish.

`self-improve` closes the loop for agents.

## Skills

| Skill | What it does | When to run |
|-------|-------------|-------------|
| `/si:errors` | Extracts tool failures, rejections, interrupts, and user corrections from the current session transcript | Before `/si:improve` |
| `/si:improve` | Analyzes failures, scans your config for gaps, proposes minimal surgical fixes, and applies approved changes | After any session with friction |

## Install

```bash
claude plugin install https://github.com/kaarelkaarelson/self-improve-plugin
```

## Usage

At the end of a session, run:

```
/si:errors
/si:improve
```

`/si:errors` extracts and saves the event log. `/si:improve` reads it, analyzes the timeline, and walks you through applying the fixes.

## What gets improved

- Your global or project CLAUDE.md — missing rules and wrong assumptions that caused friction
- Existing skill files — incomplete or incorrect instructions
- New skills for hard-won workflows, registered in `## Custom skills @self-improve` in your CLAUDE.md

## Data

Error logs are written to `~/.si-errors/<session-id>.json`. Local only, not committed to any repo.

## License

MIT
