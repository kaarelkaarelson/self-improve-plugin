---
name: si:setup
description: Set up or reconfigure the self-improve plugin. Detects Claude root and wires CLAUDE-si.md import into CLAUDE.md. Run once after install or to reconfigure.
disable-model-invocation: true
allowed-tools: AskUserQuestion, Bash, Read, Write
---

# Self-Improve Setup

Initialize or reconfigure the self-improve plugin. Safe to re-run — all steps are idempotent.

## Step 0: Reset check

Detect whether setup has already been run by checking if the SI import block is present in CLAUDE.md:

```bash
python3 -c "
import os
claude_md = os.path.expanduser('~/.claude/CLAUDE.md')
try:
    content = open(claude_md).read()
    print('configured' if '<!-- SI:IMPORT:START -->' in content else 'fresh')
except FileNotFoundError:
    print('fresh')
"
```

If the output is `configured`, use `AskUserQuestion` to ask:

> "Self-improve is already configured. What would you like to do?
>
> (1) Re-run / modify settings
> (2) Reset — removes all si:setup state (si-preferences.json, CLAUDE-si.md, SI import from CLAUDE.md)"

If the user chooses **reset**, run:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
python3 "$MAIN_REPO/skills/si:setup/scripts/reset.py"
```

Then stop — print "Reset complete. Run /si:setup again to reconfigure." and exit.

If the user chooses **re-run / modify**, continue to Step 1.

If the output is `fresh`, proceed directly to Step 1 without asking.

## Step 1: Detect Claude root

```bash
CLAUDE_ROOT=$(readlink -f ~/.claude 2>/dev/null || realpath ~/.claude 2>/dev/null || echo "$HOME/.claude")
SKILLS_DIR="$CLAUDE_ROOT/skills"
echo "Claude root: $CLAUDE_ROOT"
echo "Skills dir: $SKILLS_DIR"
```

Hold `CLAUDE_ROOT` in memory.

Print to chat: `✅ Claude root: <resolved path>`

## Step 2: Create CLAUDE-si.md

```bash
python3 -c "
import os
path = os.path.expanduser('~/.claude/CLAUDE-si.md')
if not os.path.exists(path):
    with open(path, 'w') as f:
        f.write('## Custom skills @self-improve\n\n')
    print('Created: ' + path)
else:
    print('Already exists: ' + path)
"
```

## Step 3: Wire import into CLAUDE.md

```bash
python3 -c "
import os
MARKER = '<!-- SI:IMPORT:START -->'
BLOCK = '\n<!-- SI:IMPORT:START -->\n@CLAUDE-si.md\n<!-- SI:IMPORT:END -->\n'
claude_md = os.path.expanduser('~/.claude/CLAUDE.md')
with open(claude_md) as f:
    content = f.read()
if MARKER in content:
    print('SI import already present — skipping.')
else:
    with open(claude_md, 'w') as f:
        f.write(content.rstrip('\n') + BLOCK)
    print('Injected @CLAUDE-si.md import into CLAUDE.md.')
"
```

After each of Steps 2 and 3, print a one-line status to chat immediately after the bash command completes:
- Step 2 success: `✅ CLAUDE-si.md created` or `✅ CLAUDE-si.md already exists`
- Step 2 failure: `❌ CLAUDE-si.md: <error>`
- Step 3 success: `✅ CLAUDE.md import wired` or `✅ CLAUDE.md import already present`
- Step 3 failure: `❌ CLAUDE.md import: <error>`

## Step 3b: Write state file

Write `~/.si-state.json` with the resolved config paths so other skills can read setup state without re-detecting:

```bash
python3 -c "
import json, os, subprocess

claude_root = None
for cmd in ['readlink -f ~/.claude', 'realpath ~/.claude']:
    try:
        result = subprocess.check_output(cmd, shell=True, text=True).strip()
        if result:
            claude_root = result
            break
    except Exception:
        pass
if not claude_root:
    claude_root = os.path.expanduser('~/.claude')

state = {
    'setup_complete': True,
    'claude_root': claude_root,
    'claude_md': os.path.join(claude_root, 'CLAUDE.md'),
    'skills_dir': os.path.join(claude_root, 'skills'),
}
path = os.path.expanduser('~/.si-state.json')
with open(path, 'w') as f:
    json.dump(state, f, indent=2)
print('State written: ' + path)
"
```

Print `✅ ~/.si-state.json written` on success, `❌ state file: <error>` on failure.

## Step 4: Report

Print to chat:

```
Self-Improve Setup Complete

Claude root:      <resolved path>
CLAUDE-si.md:     ~/.claude/CLAUDE-si.md  (created / already existed)
CLAUDE.md import: wired / already present

Run /si:create to create your first skill.
Run /si:improve at the end of any session to improve your agent harness — refine your existing skills and suggest new ones.
```
