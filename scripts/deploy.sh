#!/usr/bin/env bash
set -euo pipefail

# Deploy Nudge to remote server
# Usage: ./scripts/deploy.sh [server]
#   server: IP or hostname (default: $NUDGE_SERVER env var)

SERVER="${1:-${NUDGE_SERVER:-}}"
REMOTE_DIR="/opt/nudge"

if [ -z "$SERVER" ]; then
  echo "Usage: $0 <server-ip>"
  echo "  or set NUDGE_SERVER env var"
  exit 1
fi

echo "==> Deploying to $SERVER"

echo "==> Pulling latest code"
ssh "root@$SERVER" "cd $REMOTE_DIR && git pull"

echo "==> Building and starting container"
ssh "root@$SERVER" "cd $REMOTE_DIR && docker compose up -d --build"

echo "==> Pruning old images"
ssh "root@$SERVER" "docker image prune -f"

echo "==> Waiting for container to start..."
sleep 5

echo "==> Health check"
if ssh "root@$SERVER" "curl -sf http://localhost:37777/api/health"; then
  echo ""
  echo "  Healthy!"
else
  # Container may need more time — check docker status
  echo ""
  echo "  Health endpoint not ready yet. Container status:"
  ssh "root@$SERVER" "cd $REMOTE_DIR && docker compose ps"
fi

echo ""
echo "==> Recent logs:"
ssh "root@$SERVER" "cd $REMOTE_DIR && docker compose logs --tail=20"

echo ""
echo "Deploy complete."
