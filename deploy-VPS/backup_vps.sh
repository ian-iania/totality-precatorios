#!/bin/bash
# =============================================================================
# VPS Backup Script
# Run from local machine to backup VPS contents
# =============================================================================

set -e

# Configuration
VPS_IP="209.126.12.243"
VPS_USER="root"
VPS_PASS="Mark3tf0ld2025"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_BASE="./backups"
BACKUP_DIR="$BACKUP_BASE/vps_$DATE"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== VPS Backup Started: $DATE ===${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to run SSH command
ssh_cmd() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

# Function to copy files
scp_cmd() {
    sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no "$1" "$2"
}

# Function to rsync
rsync_cmd() {
    sshpass -p "$VPS_PASS" rsync -avz --progress -e "ssh -o StrictHostKeyChecking=no" "$@"
}

echo -e "${YELLOW}[1/6] Backing up Totality Precatórios...${NC}"
rsync_cmd --exclude='venv' --exclude='__pycache__' --exclude='.git' \
    "$VPS_USER@$VPS_IP:/root/charles/totality-precatorios/" \
    "$BACKUP_DIR/totality-precatorios/"

echo -e "${YELLOW}[2/6] Backing up Marketfold (deploy-vps)...${NC}"
rsync_cmd --exclude='node_modules' --exclude='__pycache__' --exclude='.git' --exclude='venv' \
    "$VPS_USER@$VPS_IP:/root/deploy-vps/" \
    "$BACKUP_DIR/deploy-vps/"

echo -e "${YELLOW}[3/6] Backing up System Configuration...${NC}"
mkdir -p "$BACKUP_DIR/system"
scp_cmd "$VPS_USER@$VPS_IP:/etc/caddy/Caddyfile" "$BACKUP_DIR/system/"
rsync_cmd "$VPS_USER@$VPS_IP:/root/duckdns/" "$BACKUP_DIR/system/duckdns/"

echo -e "${YELLOW}[4/6] Backing up PostgreSQL Database...${NC}"
ssh_cmd "docker exec deploy-vps-postgres-1 pg_dump -U postgres > /tmp/postgres_backup.sql 2>/dev/null || echo 'PostgreSQL backup skipped'"
scp_cmd "$VPS_USER@$VPS_IP:/tmp/postgres_backup.sql" "$BACKUP_DIR/" 2>/dev/null || echo "No PostgreSQL backup"

echo -e "${YELLOW}[5/6] Backing up Crontab...${NC}"
ssh_cmd "crontab -l > /tmp/crontab_backup.txt 2>/dev/null || echo 'No crontab'"
scp_cmd "$VPS_USER@$VPS_IP:/tmp/crontab_backup.txt" "$BACKUP_DIR/system/"

echo -e "${YELLOW}[6/6] Creating backup manifest...${NC}"
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
VPS Backup Manifest
===================
Date: $(date)
VPS IP: $VPS_IP
Backup Directory: $BACKUP_DIR

Contents:
- totality-precatorios/ (Streamlit scraper app)
- deploy-vps/ (Marketfold Docker app)
- system/Caddyfile (Reverse proxy config)
- system/duckdns/ (DuckDNS updater)
- system/crontab_backup.txt (Cron jobs)
- postgres_backup.sql (PostgreSQL dump)

To restore, run: ./restore_vps.sh $BACKUP_DIR
EOF

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo -e "${GREEN}=== Backup Complete ===${NC}"
echo "Location: $BACKUP_DIR"
echo "Size: $BACKUP_SIZE"
echo ""
echo "Manifest:"
cat "$BACKUP_DIR/MANIFEST.txt"
