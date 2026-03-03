#!/usr/bin/env bash
set -euo pipefail

# One-time server provisioning for Nudge on Ubuntu 24.04 (ARM)
# Usage: ssh root@<IP> 'bash -s' < scripts/server-setup.sh

REPO_URL="https://github.com/pragmatiks/nudge.git"
INSTALL_DIR="/opt/nudge"

echo "==> Installing system dependencies"
apt-get update
apt-get install -y curl git build-essential jq

echo "==> Installing mise"
curl https://mise.run | sh
eval "$(/root/.local/bin/mise activate bash)"

echo "==> Installing fail2ban"
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

echo "==> Cloning repo to $INSTALL_DIR"
if [ -d "$INSTALL_DIR" ]; then
  echo "    $INSTALL_DIR already exists, pulling latest"
  git -C "$INSTALL_DIR" pull
else
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

echo "==> Installing runtimes via mise (python, node, bun, uv)"
/root/.local/bin/mise trust "$INSTALL_DIR"
/root/.local/bin/mise install

echo "==> Installing Python dependencies"
eval "$(/root/.local/bin/mise activate bash)"
uv sync

echo "==> Installing global npm tools (playwright-cli, claude-code)"
eval "$(/root/.local/bin/mise activate bash)"
npm install -g @anthropic-ai/claude-code @playwright/cli
npx playwright install --with-deps chromium

echo "==> Installing Proton Pass CLI"
curl -fsSL https://proton.me/download/pass-cli/install.sh | bash
mv /root/.local/bin/pass-cli /usr/local/bin/pass-cli 2>/dev/null || true

echo "==> Creating data directory"
mkdir -p "$INSTALL_DIR/data"

echo "==> Installing systemd service"
cp "$INSTALL_DIR/scripts/nudge.service" /etc/systemd/system/nudge.service
systemctl daemon-reload
systemctl enable nudge

echo ""
echo "========================================="
echo "  Server provisioned successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Copy your .env file:"
echo "     scp .env root@$(hostname -I | awk '{print $1}'):/opt/nudge/.env"
echo ""
echo "  2. Start the service:"
echo "     systemctl start nudge"
echo ""
echo "  3. Check status:"
echo "     systemctl status nudge"
echo "     journalctl -u nudge -f"
echo ""
