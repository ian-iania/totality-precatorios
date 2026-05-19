#!/bin/bash
# =============================================================================
# TJRJ Precatórios - Remote Start (from Local Machine)
# =============================================================================
# Starts Streamlit on VPS remotely from your local machine
# Usage:
#   bash deploy-VPS/remote_start.sh           (uses default port 8501)
#   bash deploy-VPS/remote_start.sh 8502      (uses custom port)
# =============================================================================

# Configuration
VPS_IP="209.126.12.243"
VPS_USER="root"
VPS_PASS="Mark3tf0ld2025"
APP_DIR="/root/charles/totality-precatorios"
DEFAULT_PORT=8501
PORT="${1:-$DEFAULT_PORT}"
SCREEN_NAME="charles"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validate port
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    echo -e "${RED}Error: Invalid port number: $PORT${NC}"
    echo "Port must be between 1024 and 65535"
    exit 1
fi

# Check if sshpass is installed
if ! command -v sshpass &>/dev/null; then
    echo -e "${RED}Error: sshpass is not installed${NC}"
    echo ""
    echo "Install it with:"
    echo "  macOS: brew install sshpass"
    echo "  Ubuntu/Debian: apt install sshpass"
    echo "  CentOS/RHEL: yum install sshpass"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Remote Start - Streamlit on VPS     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "VPS: $VPS_IP"
echo "Port: $PORT"
echo ""

# Function to run SSH command
ssh_cmd() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "$1"
}

# 1. Check VPS connectivity
echo -e "${YELLOW}[1/5] Checking VPS connectivity...${NC}"
if ssh_cmd "echo 'connected'" &>/dev/null; then
    echo -e "  ${GREEN}✓ Connected${NC}"
else
    echo -e "  ${RED}✗ Cannot connect to VPS${NC}"
    exit 1
fi

# 2. Check if port is in use
echo -e "${YELLOW}[2/5] Checking port availability...${NC}"
if ssh_cmd "lsof -i :$PORT" &>/dev/null; then
    echo -e "  ${YELLOW}⚠ Port $PORT is in use${NC}"
    PROCESS=$(ssh_cmd "lsof -i :$PORT | tail -1 | awk '{print \$1, \$2}'")
    echo "  Process: $PROCESS"

    read -p "Kill the process and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(ssh_cmd "lsof -i :$PORT | tail -1 | awk '{print \$2}'")
        echo "  Killing process $PID..."
        ssh_cmd "kill -9 $PID" 2>/dev/null
        sleep 1
        echo -e "  ${GREEN}✓ Process killed${NC}"
    else
        echo "Aborted. Try a different port."
        exit 1
    fi
else
    echo -e "  ${GREEN}✓ Port $PORT is free${NC}"
fi

# 3. Stop existing Streamlit
echo -e "${YELLOW}[3/5] Stopping existing Streamlit...${NC}"
ssh_cmd "pkill -f 'streamlit run'" 2>/dev/null && echo -e "  ${GREEN}✓ Stopped${NC}" || echo "  ○ None running"

# 4. Kill existing screen session
echo -e "${YELLOW}[4/5] Managing screen sessions...${NC}"
if ssh_cmd "screen -ls | grep -q '$SCREEN_NAME'"; then
    ssh_cmd "screen -X -S $SCREEN_NAME quit" 2>/dev/null
    sleep 1
    echo -e "  ${GREEN}✓ Killed old session${NC}"
else
    echo "  ○ No existing session"
fi

# 5. Start Streamlit
echo -e "${YELLOW}[5/5] Starting Streamlit...${NC}"
ssh_cmd "cd $APP_DIR && mkdir -p logs && screen -dmS $SCREEN_NAME bash -c 'source venv/bin/activate && streamlit run app/app_v2.py --server.port $PORT --server.address 0.0.0.0 2>&1 | tee logs/streamlit.log'"

# Wait for startup
sleep 3

# Verify
if ssh_cmd "pgrep -f 'streamlit run'" > /dev/null; then
    echo -e "  ${GREEN}✓ Started successfully${NC}"
else
    echo -e "  ${RED}✗ Failed to start${NC}"
    echo ""
    echo "Check logs on VPS:"
    echo "  ${BLUE}ssh root@$VPS_IP${NC}"
    echo "  ${BLUE}tail -f $APP_DIR/logs/streamlit.log${NC}"
    exit 1
fi

# Success
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Success! Streamlit is Running       ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Access URL: ${BLUE}http://${VPS_IP}:${PORT}${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo ""
echo "  View logs:"
echo "    ${BLUE}ssh root@$VPS_IP 'tail -f $APP_DIR/logs/streamlit.log'${NC}"
echo ""
echo "  View screen session:"
echo "    ${BLUE}ssh root@$VPS_IP${NC}"
echo "    ${BLUE}screen -r $SCREEN_NAME${NC}"
echo ""
echo "  Stop Streamlit:"
echo "    ${BLUE}bash deploy-VPS/stop.sh${NC}"
echo ""
echo "  Check status:"
echo "    ${BLUE}bash deploy-VPS/check_vps_status.sh${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
