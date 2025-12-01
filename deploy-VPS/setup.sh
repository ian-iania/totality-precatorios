#!/bin/bash
# =============================================================================
# TJRJ Precatórios Scraper V5 - Quick Setup for Existing Clone
# =============================================================================
# Usage: bash setup.sh
# Run from: /root/charles/totality-precatorios
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/root/charles/totality-precatorios"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TJRJ Scraper V5 - Quick Setup        ${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Update code
echo -e "\n${YELLOW}[1/5] Pulling latest code...${NC}"
cd $APP_DIR
git pull origin main

# 2. Install system dependencies for Playwright
echo -e "\n${YELLOW}[2/5] Installing system dependencies...${NC}"
apt update
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2

# 3. Setup Python environment
echo -e "\n${YELLOW}[3/5] Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -r app/requirements.txt

# 4. Install Playwright
echo -e "\n${YELLOW}[4/5] Installing Playwright...${NC}"
./venv/bin/playwright install chromium
./venv/bin/playwright install-deps

# 5. Create directories
echo -e "\n${YELLOW}[5/5] Creating directories...${NC}"
mkdir -p logs/screenshots
mkdir -p output/partial

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!                      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To start Streamlit UI:"
echo "  cd $APP_DIR"
echo "  ./venv/bin/streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0"
echo ""
echo "Or use screen for background:"
echo "  screen -S charles"
echo "  ./venv/bin/streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0"
echo "  # Press Ctrl+A, D to detach"
echo ""
