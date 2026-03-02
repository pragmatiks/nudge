#!/bin/bash
set -e

# Ensure data directories exist
mkdir -p /data/claude-mem/logs
mkdir -p /data/proton-pass

# Symlink so claude-mem finds its data regardless of how it resolves home
ln -sfn /data/claude-mem "$HOME/.claude-mem"

# Write claude-mem settings
cat > /data/claude-mem/settings.json <<EOF
{
  "CLAUDE_MEM_DATA_DIR": "/data/claude-mem",
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
cd /app/vendor/claude-mem/scripts && \
CLAUDE_MEM_DATA_DIR=/data/claude-mem \
CLAUDE_MEM_WORKER_PORT=37777 \
  bun worker-service.cjs &
cd /app

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
exec python -m src.main
