#!/bin/bash
# =============================================================================
# TJRJ Precatórios - Start Streamlit with Custom Port
# =============================================================================
# Starts Streamlit in background with flexible port configuration
# Usage:
#   bash deploy-VPS/start_custom.sh           (uses default port 8501)
#   bash deploy-VPS/start_custom.sh 8502      (uses custom port)
# =============================================================================

# Configuration
DEFAULT_PORT=8501
PORT="${1:-$DEFAULT_PORT}"
APP_DIR="/root/charles/totality-precatorios"
SCREEN_NAME="charles"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validate port number
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    echo -e "${RED}Error: Invalid port number: $PORT${NC}"
    echo "Port must be between 1024 and 65535"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting Streamlit UI               ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running on VPS or locally
if [ -d "$APP_DIR" ]; then
    # Running on VPS
    cd "$APP_DIR" || exit 1
    IS_VPS=true
else
    # Running from local machine - use SSH
    echo "This script should be run ON the VPS, not locally."
    echo ""
    echo "To run on VPS:"
    echo "  1. SSH into VPS:"
    echo "     ${BLUE}ssh root@209.126.12.243${NC}"
    echo ""
    echo "  2. Navigate to project:"
    echo "     ${BLUE}cd /root/charles/totality-precatorios${NC}"
    echo ""
    echo "  3. Run this script:"
    echo "     ${BLUE}bash deploy-VPS/start_custom.sh $PORT${NC}"
    echo ""
    exit 1
fi

# Check if port is already in use
if lsof -i ":$PORT" &>/dev/null; then
    echo -e "${YELLOW}Warning: Port $PORT is already in use${NC}"
    PROCESS=$(lsof -i ":$PORT" | tail -1 | awk '{print $1, $2}')
    echo "  In use by: $PROCESS"
    echo ""
    read -p "Kill the process and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -i ":$PORT" | tail -1 | awk '{print $2}')
        echo "Killing process $PID..."
        kill -9 "$PID" 2>/dev/null
        sleep 1
    else
        echo "Aborted."
        echo "Try a different port: bash deploy-VPS/start_custom.sh <PORT>"
        exit 1
    fi
fi

# Stop existing Streamlit processes
echo -e "${YELLOW}[1/4] Stopping existing Streamlit processes...${NC}"
pkill -f "streamlit run" 2>/dev/null && echo "  ✓ Stopped" || echo "  ○ No processes to stop"

# Kill existing screen session if exists
if screen -ls | grep -q "$SCREEN_NAME"; then
    echo -e "${YELLOW}[2/4] Killing existing screen session...${NC}"
    screen -X -S "$SCREEN_NAME" quit 2>/dev/null
    sleep 1
    echo "  ✓ Killed old session"
else
    echo -e "${YELLOW}[2/4] No existing screen session${NC}"
fi

# Ensure logs directory exists
mkdir -p logs

# Start Streamlit in screen
echo -e "${YELLOW}[3/4] Starting Streamlit on port $PORT...${NC}"
screen -dmS "$SCREEN_NAME" bash -c "
    cd $APP_DIR
    source venv/bin/activate
    streamlit run app/app_v2.py --server.port $PORT --server.address 0.0.0.0 2>&1 | tee logs/streamlit.log
"

# Wait a bit for startup
sleep 3

# Verify it started
if pgrep -f "streamlit run" > /dev/null; then
    echo -e "  ${GREEN}✓ Streamlit started successfully${NC}"
else
    echo -e "  ${RED}✗ Failed to start Streamlit${NC}"
    echo ""
    echo "Check logs:"
    echo "  tail -f logs/streamlit.log"
    exit 1
fi

# Get public IP
echo -e "${YELLOW}[4/4] Getting public IP address...${NC}"
PUBLIC_IP=$(curl -4 -s icanhazip.com 2>/dev/null | tr -d '\n')
if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP="209.126.12.243"  # Fallback
fi
echo "  Public IP: $PUBLIC_IP"

# Success message
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Streamlit Started Successfully!     ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Access URL: ${BLUE}http://${PUBLIC_IP}:${PORT}${NC}"
echo ""
echo "Screen session: $SCREEN_NAME"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View session:  ${BLUE}screen -r $SCREEN_NAME${NC}"
echo "  Detach:        ${BLUE}Ctrl+A, then D${NC}"
echo "  Stop:          ${BLUE}bash deploy-VPS/stop.sh${NC}"
echo "  View logs:     ${BLUE}tail -f logs/streamlit.log${NC}"
echo ""

# Check firewall
if command -v ufw &>/dev/null; then
    if ! ufw status | grep -q "$PORT.*ALLOW"; then
        echo -e "${YELLOW}Note: Port $PORT is not open in firewall${NC}"
        echo "To allow access, run:"
        echo "  ${BLUE}ufw allow $PORT/tcp${NC}"
        echo ""
    fi
fi

echo -e "${GREEN}========================================${NC}"
