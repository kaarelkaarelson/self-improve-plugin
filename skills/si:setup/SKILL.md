---
name: si:setup
description: Set up or reconfigure the self-improve plugin. Detects Claude root, wires CLAUDE-si.md import, and collects skill preferences. Run once after install or to reconfigure.
disable-model-invocation: true
allowed-tools: AskUserQuestion, Bash, Read, Write
---

# Self-Improve Setup

Initialize or reconfigure the self-improve plugin. Safe to re-run — all steps are idempotent.

## Step 1: Detect Claude root

```bash
CLAUDE_ROOT=$(readlink -f ~/.claude 2>/dev/null || realpath ~/.claude 2>/dev/null || echo "$HOME/.claude")
SKILLS_DIR="$CLAUDE_ROOT/skills"
echo "Claude root: $CLAUDE_ROOT"
echo "Skills dir: $SKILLS_DIR"
```

Hold `CLAUDE_ROOT` in memory.

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

## Step 4: Collect preferences

Check current `auto_invoke` preference:

```bash
python3 -c "
import json, os
path = os.path.expanduser('~/.claude/si-preferences.json')
if os.path.exists(path):
    d = json.load(open(path))
    print('current auto_invoke=' + str(d.get('auto_invoke', 'unset')))
else:
    print('current auto_invoke=unset')
"
```

Use `AskUserQuestion` to ask:

> "Should Claude automatically add new skills as trigger rules in CLAUDE-si.md so they self-invoke when conditions match — without you typing the command?
>
> Current setting: `<value from above, or 'not set'>`
>
> (yes / no)"

Save the answer:

```bash
python3 -c "
import json, os
path = os.path.expanduser('~/.claude/si-preferences.json')
prefs = json.load(open(path)) if os.path.exists(path) else {}
prefs['auto_invoke'] = True  # set False for 'no'
with open(path, 'w') as f:
    json.dump(prefs, f, indent=2)
print('Saved auto_invoke=' + str(prefs['auto_invoke']))
"
```

## Step 5: Report

Print to chat:

```
Self-Improve Setup Complete

Claude root:     <resolved path>
CLAUDE-si.md:    ~/.claude/CLAUDE-si.md  (created / already existed)
CLAUDE.md import: wired / already present
auto_invoke:     true / false

Run /si:create to create your first skill.
```
