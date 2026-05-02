#!/usr/bin/env python3
"""Inject @CLAUDE-si.md import into ~/.claude/CLAUDE.md if not already present."""

import os

MARKER = "<!-- SI:IMPORT:START -->"
BLOCK = "\n<!-- SI:IMPORT:START -->\n@CLAUDE-si.md\n<!-- SI:IMPORT:END -->\n"

claude_md = os.path.expanduser("~/.claude/CLAUDE.md")

with open(claude_md) as f:
    content = f.read()

if MARKER in content:
    print("SI import already present — skipping.")
else:
    with open(claude_md, "w") as f:
        f.write(content.rstrip("\n") + BLOCK)
    print("Injected @CLAUDE-si.md import into CLAUDE.md.")
