#!/bin/bash
# SessionStart hook: install Python + frontend deps so lint/typecheck/test work
# in cloud sandboxes, local CLI sessions, and worktree-isolated subagents.
#
# Idempotent: uv sync --locked and npm install are no-ops when caches are warm.
# Stderr passes through so failures are visible; stdout is suppressed except
# for the final success line.
set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

uv sync --extra dev --locked >/dev/null

(cd app && npm install --no-audit --no-fund --silent)

echo "✓ nudge deps ready (uv + npm)"
