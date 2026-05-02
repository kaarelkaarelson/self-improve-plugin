"""Reset si:setup state so the setup can be re-run from scratch."""

import os
import re

def remove_file(path):
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        os.remove(expanded)
        print(f"Removed: {expanded}")
    else:
        print(f"Not found (skipped): {expanded}")

def strip_si_import(claude_md_path):
    expanded = os.path.expanduser(claude_md_path)
    with open(expanded) as f:
        content = f.read()
    cleaned = re.sub(
        r'\n<!-- SI:IMPORT:START -->.*?<!-- SI:IMPORT:END -->\n',
        '',
        content,
        flags=re.DOTALL,
    )
    if cleaned != content:
        with open(expanded, 'w') as f:
            f.write(cleaned)
        print(f"Stripped SI import from: {expanded}")
    else:
        print(f"SI import not found (skipped): {expanded}")

remove_file('~/.claude/si-preferences.json')
remove_file('~/.claude/CLAUDE-si.md')
strip_si_import('~/.claude/CLAUDE.md')
