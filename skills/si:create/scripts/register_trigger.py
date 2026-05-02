#!/usr/bin/env python3
"""Append a skill trigger rule to ~/.claude/CLAUDE.md under ## Custom skills."""

import os
import re
import sys

if len(sys.argv) != 3:
    print("Usage: register_trigger.py <trigger-condition> <skill-name>")
    sys.exit(1)

trigger_condition = sys.argv[1]
skill_name = sys.argv[2]
trigger_line = f"WHEN {trigger_condition}, you MUST invoke `/{skill_name}`"

claude_si = os.path.expanduser("~/.claude/CLAUDE-si.md")

if not os.path.exists(claude_si):
    with open(claude_si, "w") as f:
        f.write("## Custom skills @self-improve\n\n")

with open(claude_si) as f:
    content = f.read()

SECTION = "## Custom skills @self-improve"

if trigger_line in content:
    print(f"Already registered: {trigger_line}")
    sys.exit(0)

if SECTION not in content:
    content = content.rstrip("\n") + f"\n\n{SECTION}\n\n" + trigger_line + "\n"
else:
    content = re.sub(
        r"(## Custom skills @self-improve\n)",
        r"\1\n" + trigger_line + "\n",
        content,
        count=1,
    )

with open(claude_si, "w") as f:
    f.write(content)

print(f"Registered: {trigger_line}")
