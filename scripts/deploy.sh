#!/usr/bin/env bash
set -euo pipefail

# Deploy Nudge to remote server
# Usage: ./scripts/deploy.sh [server]

SERVER="${1:-${NUDGE_SERVER:-}}"
REMOTE_DIR="/opt/nudge"

if [ -z "$SERVER" ]; then
  echo "Usage: $0 <server-ip>"
  echo "  or set NUDGE_SERVER in mise.local.toml"
  exit 1
fi

echo "==> Deploying to $SERVER"

echo "==> Pulling latest code"
ssh "root@$SERVER" "cd $REMOTE_DIR && git pull && chown -R nudge:nudge $REMOTE_DIR"

echo "==> Installing runtimes and dependencies"
ssh "root@$SERVER" "su - nudge -c 'cd $REMOTE_DIR && /home/nudge/.local/bin/mise install && eval \"\$(/home/nudge/.local/bin/mise activate bash)\" && uv sync'"

echo "==> Updating Claude Code"
ssh "root@$SERVER" "eval \"\$(/root/.local/bin/mise activate bash)\" && npm update -g @anthropic-ai/claude-code && claude --version"

echo "==> Installing systemd units"
ssh "root@$SERVER" "cp $REMOTE_DIR/scripts/nudge.service /etc/systemd/system/ && cp $REMOTE_DIR/scripts/nudge-update.service /etc/systemd/system/ && cp $REMOTE_DIR/scripts/nudge-update.timer /etc/systemd/system/ && systemctl daemon-reload && systemctl enable nudge-update.timer && systemctl start nudge-update.timer"

echo "==> Restarting service"
ssh "root@$SERVER" "systemctl restart nudge"

echo "==> Waiting for startup..."
sleep 5

echo "==> Health check"
if ssh "root@$SERVER" "curl -sf http://localhost:37777/api/health"; then
  echo ""
  echo "  Healthy!"
else
  echo "  Health endpoint not ready yet, checking service status..."
  ssh "root@$SERVER" "systemctl status nudge --no-pager" || true
fi

echo ""
echo "==> Recent logs:"
ssh "root@$SERVER" "journalctl -u nudge --no-pager -n 20"

echo ""
echo "Deploy complete."
