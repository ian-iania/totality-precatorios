#!/bin/bash
# =============================================================================
# TJRJ Precatórios Scraper V5 - Quick Update Script
# =============================================================================
# Usage: sudo bash update.sh
# =============================================================================

set -e

APP_DIR="/opt/charles"
APP_USER="charles"

echo "🔄 Stopping service..."
systemctl stop charles || true

echo "📥 Pulling latest code..."
cd $APP_DIR
sudo -u $APP_USER git pull origin main

echo "📦 Updating dependencies..."
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
sudo -u $APP_USER ./venv/bin/pip install -r app/requirements.txt

echo "🧹 Cleaning old logs..."
rm -f $APP_DIR/logs/scraper_v3.log
rm -rf $APP_DIR/logs/screenshots/*.png

echo "🚀 Starting service..."
systemctl start charles

echo "✅ Update complete!"
echo ""
echo "Check status: sudo systemctl status charles"
echo "View logs: sudo journalctl -u charles -f"
