#!/bin/bash
# =============================================================================
# TJRJ Precatórios Scraper V5 - VPS Installation Script
# =============================================================================
# Usage: sudo bash install.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TJRJ Scraper V5 - VPS Installation   ${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
APP_DIR="/opt/charles"
APP_USER="charles"
REPO_URL="https://github.com/ian-iania/totality-precatorios.git"
PYTHON_VERSION="3.11"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo bash install.sh)${NC}"
    exit 1
fi

# 1. Update system
echo -e "\n${YELLOW}[1/8] Updating system...${NC}"
apt update && apt upgrade -y

# 2. Install system dependencies
echo -e "\n${YELLOW}[2/8] Installing system dependencies...${NC}"
apt install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    git \
    curl \
    wget \
    unzip \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2

# 3. Create app user (if not exists)
echo -e "\n${YELLOW}[3/8] Creating app user...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash $APP_USER
    echo -e "${GREEN}User $APP_USER created${NC}"
else
    echo -e "${GREEN}User $APP_USER already exists${NC}"
fi

# 4. Clone repository
echo -e "\n${YELLOW}[4/8] Cloning repository...${NC}"
if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}Directory exists, pulling latest...${NC}"
    cd $APP_DIR
    git pull origin main
else
    git clone $REPO_URL $APP_DIR
fi
chown -R $APP_USER:$APP_USER $APP_DIR

# 5. Setup Python virtual environment
echo -e "\n${YELLOW}[5/8] Setting up Python environment...${NC}"
cd $APP_DIR
sudo -u $APP_USER python${PYTHON_VERSION} -m venv venv
sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
sudo -u $APP_USER ./venv/bin/pip install -r app/requirements.txt

# 6. Install Playwright
echo -e "\n${YELLOW}[6/8] Installing Playwright browsers...${NC}"
sudo -u $APP_USER ./venv/bin/playwright install chromium
./venv/bin/playwright install-deps

# 7. Create directories
echo -e "\n${YELLOW}[7/8] Creating directories...${NC}"
sudo -u $APP_USER mkdir -p $APP_DIR/logs
sudo -u $APP_USER mkdir -p $APP_DIR/logs/screenshots
sudo -u $APP_USER mkdir -p $APP_DIR/output
sudo -u $APP_USER mkdir -p $APP_DIR/output/partial

# 8. Install systemd service
echo -e "\n${YELLOW}[8/8] Installing systemd service...${NC}"
cp $APP_DIR/deploy-VPS/charles.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable charles

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!               ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "To start the service:"
echo -e "  ${YELLOW}sudo systemctl start charles${NC}"
echo -e ""
echo -e "To check status:"
echo -e "  ${YELLOW}sudo systemctl status charles${NC}"
echo -e ""
echo -e "To view logs:"
echo -e "  ${YELLOW}sudo journalctl -u charles -f${NC}"
echo -e ""
echo -e "Access UI at:"
echo -e "  ${YELLOW}http://YOUR_VPS_IP:8501${NC}"
echo -e ""
