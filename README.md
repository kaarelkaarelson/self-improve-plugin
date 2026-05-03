# self-improve

[![CI](https://github.com/kaarelkaarelson/self-improve-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/kaarelkaarelson/self-improve-plugin/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Never let your Claude Code make the same mistake twice.

## Philosophy

Error correction is the foundational principle behind every reliable computing system. TCP allowed the internet to reliably transmit information by detecting and retransmitting every lost packet. Quantum Error Correction (QEC) made reliable quantum computing possible by correcting the noise that makes physical qubits fail. LLM coding agents have no equivalent. Mistakes surface, get corrected, and vanish.

Your Claude Code agent makes more mistakes than you notice. A task done in 15 tool calls that should have taken 2. A correction you gave last session, forgotten by the next. These mistakes cost real tokens — wasting >10,000 per day on work the agent should already know how to do. None of it gets fixed automatically.

`self-improve` closes the loop: at the end of a session, it extracts every friction event, scans your Claude config for what's missing or wrong, surgically updates your skills and CLAUDE.md, and generates new skills for hard-won workflows — so the same failure class doesn't recur.

Inspired by [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin), but focused on one narrower loop: turning agent mistakes into durable local Claude Code instructions.

## Skills

| Skill | What it does | When to run |
|-------|-------------|-------------|
| `/si:root` | Resolves `~/.claude` to its canonical path (symlink or not) and caches `SI_CLAUDE_ROOT` and `SI_SKILLS_DIR`. Required by all other skills. | Once after install; re-run if you move your dotfiles |
| `/si:setup` | Wires `CLAUDE-si.md` into your config. Safe to re-run. | Once after install |
| `/si:errors` | Extracts tool failures, rejections, interrupts, and user corrections from the current session transcript | Before `/si:improve` |
| `/si:improve` | Analyzes failures, scans your config for gaps, proposes minimal surgical fixes, and applies approved changes | After any session with friction |
| `/si:create` | Interviews you about a workflow, trials it live, and codifies what worked as a reusable skill | When you want to capture a new workflow |
| `/si:verify` | Replays a failure checkpoint in an isolated subagent to confirm a fix works. Called automatically by `/si:improve`; can also be run standalone. | After `/si:improve`, or with `<session-id> <message-index>` |

## Quick Example

Run setup once:

```bash
/si:setup
```

After a session with friction:

```bash
/si:errors
/si:improve
/si:verify
```

`/si:errors` extracts the failure signals. `/si:improve` proposes and applies minimal changes to your Claude config or skills. `/si:verify` replays the failure shape in isolation to check that the fix actually helps.

A synthetic fixture is included in `examples/session-with-friction.jsonl`:

```bash
python skills/si:errors/scripts/extract_session_failures.py examples/session-with-friction.jsonl --json
```

## Install

Claude Code is the primary supported target:

```bash
claude plugin install https://github.com/kaarelkaarelson/self-improve-plugin
```

Then run `/si:setup` once to wire the plugin into your Claude config. Setup writes `~/.si-state.json`, which `/si:create` and `/si:improve` use to detect whether setup has been completed before they proceed.

## Support Status

Claude Code is supported today. `self-improve` setup targets `~/.claude/CLAUDE.md` and `~/.claude/CLAUDE-si.md`, and `/si:errors` expects Claude Code session JSONL.

Other harnesses are coming soon. The repo already includes experimental Cursor, Codex, and agents marketplace manifests so the same skill payload can be discovered by those runtimes, following the packaging pattern used by Compound Engineering. Runtime setup for those harnesses still needs provider detection, provider-specific config paths, and provider-specific transcript parsing.

## What gets improved

- Your global or project CLAUDE.md — missing rules and wrong assumptions that caused friction
- Existing skill files — incomplete or incorrect instructions
- New skills for hard-won workflows, registered in `## Custom skills @self-improve` in your CLAUDE.md

## What Gets Changed

`self-improve` is allowed to touch only the local files needed to make future Claude Code sessions better:

- `~/.claude/CLAUDE.md`
- `~/.claude/CLAUDE-si.md`
- `~/.claude/skills/`
- `~/.si-state.json`
- `~/.si-errors/`

The plugin should make small, reviewable edits. It should not rewrite unrelated config, remove user files, or change project code as part of setup.

## What Never Leaves Your Machine

The plugin is local-first. It does not intentionally upload transcripts, extracted failures, generated skills, or Claude configuration to a remote service.

Claude transcripts can contain private code, commands, paths, and secrets. Do not commit real transcripts. Use synthetic fixtures like the examples in this repo when reporting bugs.

## Safety Model

The safe default is reversible, surgical config change:

- Extract failure evidence before changing instructions.
- Prefer editing the smallest relevant skill or CLAUDE.md section.
- Preserve existing user content.
- Avoid duplicate imports and duplicate trigger rules.
- Verify fixes against the failure shape when possible.

## Data

Setup state is written to `~/.si-state.json`. Error logs are written to `~/.si-errors/<session-id>.json`. Local only, not committed to any repo.

## Local Development

Run the test suite:

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE)
