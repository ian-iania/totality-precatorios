#!/bin/bash
# =============================================================================
# TJRJ Precatórios Scraper V5 - Quick Update Script
# =============================================================================
# Usage: bash update.sh
# =============================================================================

set -e

APP_DIR="/root/charles/totality-precatorios"

echo "🔄 Stopping Streamlit..."
pkill -f streamlit || true
pkill -f chromium || true
screen -X -S charles quit 2>/dev/null || true

echo "📥 Pulling latest code..."
cd $APP_DIR
git pull origin main

echo "📦 Updating dependencies..."
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -r app/requirements.txt

echo "🧹 Cleaning old logs..."
rm -f $APP_DIR/logs/scraper_v3.log
rm -rf $APP_DIR/logs/screenshots/*.png

echo "🚀 Starting Streamlit V2..."
screen -dmS charles ./venv/bin/streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0

# Get public IPv4 (use ip.me which returns IPv4 by default)
PUBLIC_IP=$(curl -4 -s icanhazip.com 2>/dev/null | tr -d '\n' || echo "209.126.12.243")

echo "✅ Update complete!"
echo ""
echo "View screen: screen -r charles"
echo "Access UI: http://${PUBLIC_IP}:8501"
