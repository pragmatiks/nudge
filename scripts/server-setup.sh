#!/usr/bin/env bash
set -euo pipefail

# One-time server provisioning for Nudge on Ubuntu 24.04 (ARM)
# Usage: ssh root@<IP> 'bash -s' < scripts/server-setup.sh

REPO_URL="https://github.com/pragmatiks/nudge.git"
INSTALL_DIR="/opt/nudge"

echo "==> Installing Docker"
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> Enabling Docker on boot"
systemctl enable docker
systemctl start docker

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

echo ""
echo "========================================="
echo "  Server provisioned successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Copy your .env file:"
echo "     scp .env root@$(hostname -I | awk '{print $1}'):$INSTALL_DIR/.env"
echo ""
echo "  2. Build and start:"
echo "     cd $INSTALL_DIR && docker compose up -d --build"
echo ""
echo "  3. Verify:"
echo "     docker compose -f $INSTALL_DIR/docker-compose.yml ps"
echo ""
