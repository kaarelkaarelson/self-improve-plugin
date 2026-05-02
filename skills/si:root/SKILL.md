---
name: si:root
description: Resolves ~/.claude to its canonical path (symlink or real directory), writes SI_CLAUDE_ROOT and SI_SKILLS_DIR exports to cache.sh. Idempotent — skips if cache is already valid. Re-run to force refresh.
disable-model-invocation: true
allowed-tools: Bash
---

# si:root

Resolve the canonical Claude config root and cache it so other skills in this plugin don't re-resolve it each time. Idempotent — safe to invoke as a first step from any skill.

## Step 0: Check if already resolved

```bash
if bash "${CLAUDE_SKILL_DIR}/scripts/check.sh"; then
  source "$HOME/.claude/skills/si:root/cache.sh"
  echo "Already valid — skipping."
  cat "$HOME/.claude/skills/si:root/cache.sh"
  exit 0
fi
```

If Step 0 exits early, stop here. No further steps needed.

## Step 1: Resolve and write cache.sh

```bash
TEMPLATE="${CLAUDE_SKILL_DIR}/templates/cache.template.sh"
CACHE="$HOME/.claude/skills/si:root/cache.sh"
CLAUDE_ROOT=$(readlink -f ~/.claude 2>/dev/null || realpath ~/.claude 2>/dev/null || echo "$HOME/.claude")
SKILLS_DIR="$CLAUDE_ROOT/skills"

sed \
  -e "s|__CLAUDE_ROOT__|$CLAUDE_ROOT|g" \
  -e "s|__SKILLS_DIR__|$SKILLS_DIR|g" \
  -e "s|__SOURCED_AT__|$(date -u +%Y-%m-%dT%H:%M:%SZ)|g" \
  "$TEMPLATE" > "$CACHE"

echo "Written: $CACHE"
cat "$CACHE"
```

## Step 2: Verify

```bash
source "$HOME/.claude/skills/si:root/cache.sh"
[ -d "$SI_SKILLS_DIR" ] && echo "OK — $SI_SKILLS_DIR exists" || echo "ERROR — path invalid"
```

Report the three exported values and whether the path is valid.

---

## Usage by other si:* skills

At the start of any bash block that needs the resolved paths:

```bash
if bash "${CLAUDE_SKILL_DIR}/../si:root/scripts/check.sh"; then
  source "$HOME/.claude/skills/si:root/cache.sh"
else
  echo "Root not resolved — invoke /si:root first."
  exit 1
fi
# $SI_CLAUDE_ROOT and $SI_SKILLS_DIR are now set
```

Use `$SI_CLAUDE_ROOT` and `$SI_SKILLS_DIR` in place of `~/.claude` throughout.
