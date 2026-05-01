# self-improve

> Never let your Claude Code make the same mistake twice.

Your Claude Code agent makes more mistakes than you notice. A task done in 15 tool calls that should have taken 2. A correction you gave last session, forgotten by the next. These mistakes cost real tokens — wasting >10,000 per day on work the agent should already know how to do. None of it gets fixed automatically.

Error correction is the foundational principle behind every reliable computing system. TCP allowed the internet to reliably transmit information by detecting and retransmitting every lost packet. Quantum Error Correction (QEC) made reliable quantum computing possible by correcting the noise that makes physical qubits fail. LLM coding agents have no equivalent. Mistakes surface, get corrected, and vanish. `self-improve` closes the loop: at the end of a session, it extracts every friction event, scans your Claude config for what's missing or wrong, and surgically updates your skills and CLAUDE.md so the same failure class doesn't recur.

## Skills

| Skill | What it does | When to run |
|-------|-------------|-------------|
| `/si:root` | Resolves `~/.claude` to its canonical path (symlink or not) and caches `SI_CLAUDE_ROOT` and `SI_SKILLS_DIR`. Required by all other skills. | Once after install; re-run if you move your dotfiles |
| `/si:errors` | Extracts tool failures, rejections, interrupts, and user corrections from the current session transcript | Before `/si:improve` |
| `/si:improve` | Analyzes failures, scans your config for gaps, proposes minimal surgical fixes, and applies approved changes | After any session with friction |
| `/si:verify` | Replays a failure checkpoint in an isolated subagent to confirm a fix works. Called automatically by `/si:improve`; can also be run standalone. | After `/si:improve`, or with `<session-id> <message-index>` |

## Install

```bash
claude plugin install https://github.com/kaarelkaarelson/self-improve-plugin
```

After installing, run once to resolve your config root:

```
/si:root
```


## What gets improved

- Your global or project CLAUDE.md — missing rules and wrong assumptions that caused friction
- Existing skill files — incomplete or incorrect instructions
- New skills for hard-won workflows, registered in `## Custom skills @self-improve` in your CLAUDE.md

## Data

Error logs are written to `~/.si-errors/<session-id>.json`. Local only, not committed to any repo.

## License

MIT
