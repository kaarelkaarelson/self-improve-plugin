#!/bin/bash
# Exits 0 if si:root cache is valid, 1 if missing or stale.
CACHE="$HOME/.claude/skills/si:root/cache.sh"
[ -f "$CACHE" ] && source "$CACHE" && [ -d "$SI_SKILLS_DIR" ] && exit 0 || exit 1
