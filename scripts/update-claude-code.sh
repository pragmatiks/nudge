#!/usr/bin/env bash
set -euo pipefail

# Update Claude Code globally, restart service if updated
# Runs as root (needs npm global + systemctl restart)

LOG_TAG="update-claude-code"

old_version=$(claude --version 2>/dev/null || echo "unknown")
npm update -g @anthropic-ai/claude-code

new_version=$(claude --version 2>/dev/null || echo "unknown")

if [ "$old_version" != "$new_version" ]; then
  logger -t "$LOG_TAG" "Updated Claude Code: $old_version -> $new_version, restarting nudge"
  systemctl restart nudge
else
  logger -t "$LOG_TAG" "Claude Code already up to date ($old_version)"
fi
