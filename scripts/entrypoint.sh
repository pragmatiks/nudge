#!/bin/bash
set -e

DATA_DIR="${NUDGE_DATA_DIR:-/opt/nudge/data}"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Ensure data directories exist
mkdir -p "$DATA_DIR/claude-mem/logs"
mkdir -p "$DATA_DIR/proton-pass"
mkdir -p "$DATA_DIR/sessions"
mkdir -p "$DATA_DIR/nudges"
mkdir -p "$DATA_DIR/browser-profile"

# Symlink so claude-mem finds its data regardless of how it resolves home
ln -sfn "$DATA_DIR/claude-mem" "$HOME/.claude-mem"

# Write claude-mem settings
cat > "$DATA_DIR/claude-mem/settings.json" <<EOF
{
  "CLAUDE_MEM_DATA_DIR": "$DATA_DIR/claude-mem",
  "CLAUDE_MEM_WORKER_PORT": "37777",
  "CLAUDE_MEM_WORKER_HOST": "127.0.0.1",
  "CLAUDE_MEM_PROVIDER": "claude",
  "CLAUDE_MEM_CLAUDE_AUTH_METHOD": "cli",
  "CLAUDE_MEM_MODEL": "claude-sonnet-4-5",
  "CLAUDE_MEM_LOG_LEVEL": "INFO",
  "CLAUDE_MEM_MODE": "code"
}
EOF

# Start claude-mem worker in background
echo "Starting claude-mem worker..."
cd "$APP_DIR/vendor/claude-mem/scripts" && \
CLAUDE_MEM_DATA_DIR="$DATA_DIR/claude-mem" \
CLAUDE_MEM_WORKER_PORT=37777 \
  bun worker-service.cjs &
cd "$APP_DIR"

# Wait for worker to be healthy
echo "Waiting for claude-mem worker..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:37777/api/health > /dev/null 2>&1; then
    echo "claude-mem worker ready"
    break
  fi
  sleep 0.5
done

# Start the bot
echo "Starting Nudge bot..."
exec uv run python -m src.main
