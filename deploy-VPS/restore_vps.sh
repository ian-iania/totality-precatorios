#!/bin/bash
# =============================================================================
# VPS Restore Script
# Run from local machine to restore VPS from backup
# Usage: ./restore_vps.sh ./backups/vps_YYYYMMDD_HHMMSS
# =============================================================================

set -e

# Configuration
VPS_IP="209.126.12.243"
VPS_USER="root"
VPS_PASS="Mark3tf0ld2025"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <backup_directory>${NC}"
    echo "Example: $0 ./backups/vps_20251204_120000"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}=== VPS Restore Started ===${NC}"
echo "Restoring from: $BACKUP_DIR"

# Function to run SSH command
ssh_cmd() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

# Function to rsync
rsync_cmd() {
    sshpass -p "$VPS_PASS" rsync -avz --progress -e "ssh -o StrictHostKeyChecking=no" "$@"
}

echo -e "${YELLOW}[1/9] Installing system packages...${NC}"
ssh_cmd "apt update && apt install -y python3 python3-pip python3-venv docker.io docker-compose caddy ufw"

echo -e "${YELLOW}[2/9] Restoring Totality Precatórios...${NC}"
ssh_cmd "mkdir -p /root/charles"
rsync_cmd "$BACKUP_DIR/totality-precatorios/" "$VPS_USER@$VPS_IP:/root/charles/totality-precatorios/"

echo -e "${YELLOW}[3/9] Setting up Python environment...${NC}"
ssh_cmd "cd /root/charles/totality-precatorios && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo -e "${YELLOW}[4/9] Installing Playwright browsers...${NC}"
ssh_cmd "cd /root/charles/totality-precatorios && source venv/bin/activate && playwright install chromium"

echo -e "${YELLOW}[5/9] Restoring Marketfold (deploy-vps)...${NC}"
rsync_cmd "$BACKUP_DIR/deploy-vps/" "$VPS_USER@$VPS_IP:/root/deploy-vps/"
ssh_cmd "cd /root/deploy-vps && docker-compose up -d"

echo -e "${YELLOW}[6/9] Restoring system configuration...${NC}"
sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no "$BACKUP_DIR/system/Caddyfile" "$VPS_USER@$VPS_IP:/etc/caddy/Caddyfile"
rsync_cmd "$BACKUP_DIR/system/duckdns/" "$VPS_USER@$VPS_IP:/root/duckdns/"
ssh_cmd "chmod +x /root/duckdns/update.sh"
ssh_cmd "systemctl restart caddy"

echo -e "${YELLOW}[7/9] Restoring PostgreSQL database...${NC}"
if [ -f "$BACKUP_DIR/postgres_backup.sql" ]; then
    sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no "$BACKUP_DIR/postgres_backup.sql" "$VPS_USER@$VPS_IP:/tmp/"
    ssh_cmd "sleep 10 && docker exec -i deploy-vps-postgres-1 psql -U postgres < /tmp/postgres_backup.sql" || echo "PostgreSQL restore skipped"
fi

echo -e "${YELLOW}[8/9] Setting up crontab...${NC}"
ssh_cmd "echo '*/5 * * * * /root/duckdns/update.sh >/dev/null 2>&1' | crontab -"

echo -e "${YELLOW}[9/9] Configuring firewall and starting services...${NC}"
ssh_cmd "ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 8501/tcp && ufw allow 8080/tcp && ufw --force enable"
ssh_cmd "cd /root/charles/totality-precatorios && source venv/bin/activate && pkill -f streamlit || true && nohup streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit.log 2>&1 &"

echo -e "${GREEN}=== Restore Complete ===${NC}"
echo ""
echo "Services should be available at:"
echo "  - Totality Precatórios: http://$VPS_IP:8501"
echo "  - Totality (DuckDNS): https://tjrj.duckdns.org"
echo "  - Marketfold: https://marketfold.duckdns.org"
echo ""
echo "Run ./check_vps_status.sh to verify all services"
