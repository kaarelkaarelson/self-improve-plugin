# Privacy

`self-improve` is local-first.

The plugin analyzes Claude Code session transcripts to find tool failures, rejected actions, interruptions, and user corrections. It uses those signals to improve local Claude configuration and skills.

## Data Written Locally

- Setup state: `~/.si-state.json`
- Error summaries: `~/.si-errors/<session-id>.json`
- Claude config updates: `~/.claude/CLAUDE.md` and `~/.claude/CLAUDE-si.md`
- Generated skills: `~/.claude/skills/`

## Data Sharing

The plugin does not intentionally send transcripts, extracted failures, generated skills, or Claude configuration to a remote service.

Your normal Claude Code environment may still involve model calls and tool use outside this plugin. This document only describes the behavior of `self-improve` itself.

## Sensitive Data

Claude transcripts can contain private code, commands, file paths, secrets, and personal information. Review extracted failure logs before sharing them. Prefer synthetic fixtures for bug reports and examples.
