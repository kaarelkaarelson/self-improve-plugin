# Security Policy

## Reporting a Vulnerability

Please report security issues by emailing `kaarel.kaarelson@gmail.com`.

Include:

- A short description of the issue
- Steps to reproduce it
- The affected file, skill, or script
- Any local configuration that matters

Do not include private Claude transcripts, API keys, tokens, or other secrets in the report. If a transcript is needed to reproduce the issue, redact it first or use a synthetic fixture.

## Scope

`self-improve` reads Claude session transcripts and edits local Claude configuration files during explicit workflows. Security-sensitive areas include:

- Session transcript parsing
- `CLAUDE.md` and `CLAUDE-si.md` edits
- Skill creation and trigger registration
- Any script that reads from or writes to `~/.claude`

## Local-First Design

The plugin is intended to run locally. It should not upload transcripts, logs, or Claude configuration unless a future feature explicitly documents that behavior and asks for user consent.
