#!/bin/bash
# =============================================================================
# TJRJ Precatórios - VPS Diagnostic Tool
# =============================================================================
# Diagnoses why Streamlit is not running and provides solutions
# Usage: bash deploy-VPS/diagnose.sh
# =============================================================================

# Configuration
VPS_IP="209.126.12.243"
VPS_USER="root"
VPS_PASS="Mark3tf0ld2025"
APP_DIR="/root/charles/totality-precatorios"
DEFAULT_PORT=8501

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  TJRJ Precatórios - VPS Diagnostics  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "VPS: $VPS_IP"
echo "Time: $(date)"
echo ""

# Function to run SSH command
ssh_cmd() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "$1" 2>/dev/null
}

# 1. Check VPS connectivity
echo -e "${YELLOW}[1/8] Checking VPS connectivity...${NC}"
if ssh_cmd "echo 'connected'" &>/dev/null; then
    echo -e "  ${GREEN}✓ VPS is accessible via SSH${NC}"
else
    echo -e "  ${RED}✗ Cannot connect to VPS${NC}"
    echo "  Please check:"
    echo "    - VPS is online"
    echo "    - SSH credentials are correct"
    echo "    - Network connectivity"
    exit 1
fi

# 2. Check project directory
echo -e "\n${YELLOW}[2/8] Checking project directory...${NC}"
if ssh_cmd "test -d $APP_DIR && echo 'exists'"; then
    echo -e "  ${GREEN}✓ Project directory exists: $APP_DIR${NC}"
else
    echo -e "  ${RED}✗ Project directory not found: $APP_DIR${NC}"
    echo "  Run first-time setup: bash deploy-VPS/setup.sh"
    exit 1
fi

# 3. Check virtual environment
echo -e "\n${YELLOW}[3/8] Checking Python virtual environment...${NC}"
if ssh_cmd "test -f $APP_DIR/venv/bin/python && echo 'exists'"; then
    echo -e "  ${GREEN}✓ Virtual environment exists${NC}"
    PYTHON_VERSION=$(ssh_cmd "$APP_DIR/venv/bin/python --version")
    echo "  Python: $PYTHON_VERSION"
else
    echo -e "  ${RED}✗ Virtual environment not found${NC}"
    echo "  Run: bash deploy-VPS/setup.sh"
    exit 1
fi

# 4. Check Streamlit installation
echo -e "\n${YELLOW}[4/8] Checking Streamlit installation...${NC}"
if ssh_cmd "$APP_DIR/venv/bin/streamlit --version" &>/dev/null; then
    STREAMLIT_VERSION=$(ssh_cmd "$APP_DIR/venv/bin/streamlit --version 2>&1")
    echo -e "  ${GREEN}✓ Streamlit installed${NC}"
    echo "  Version: $STREAMLIT_VERSION"
else
    echo -e "  ${RED}✗ Streamlit not installed${NC}"
    echo "  Installing Streamlit..."
    ssh_cmd "cd $APP_DIR && ./venv/bin/pip install streamlit"
fi

# 5. Check if Streamlit is running
echo -e "\n${YELLOW}[5/8] Checking if Streamlit is running...${NC}"
STREAMLIT_PIDS=$(ssh_cmd "pgrep -f 'streamlit run' | tr '\n' ' '")
if [ -n "$STREAMLIT_PIDS" ]; then
    echo -e "  ${GREEN}✓ Streamlit is running${NC}"
    echo "  PIDs: $STREAMLIT_PIDS"

    # Check which port it's using
    for pid in $STREAMLIT_PIDS; do
        PORT=$(ssh_cmd "lsof -p $pid 2>/dev/null | grep LISTEN | awk '{print \$9}' | cut -d':' -f2 | head -1")
        if [ -n "$PORT" ]; then
            echo "  Port: $PORT"
        fi
    done
else
    echo -e "  ${RED}✗ Streamlit is NOT running${NC}"
fi

# 6. Check screen sessions
echo -e "\n${YELLOW}[6/8] Checking screen sessions...${NC}"
SCREEN_OUTPUT=$(ssh_cmd "screen -ls 2>&1")
if echo "$SCREEN_OUTPUT" | grep -q "charles"; then
    echo -e "  ${GREEN}✓ Screen session 'charles' exists${NC}"
    echo "$SCREEN_OUTPUT" | grep "charles"
elif echo "$SCREEN_OUTPUT" | grep -q "No Sockets"; then
    echo -e "  ${YELLOW}○ No screen sessions found${NC}"
else
    echo -e "  ${YELLOW}○ No 'charles' session${NC}"
    echo "  Available sessions:"
    echo "$SCREEN_OUTPUT" | grep -v "No Sockets" || echo "    (none)"
fi

# 7. Check port availability
echo -e "\n${YELLOW}[7/8] Checking port availability...${NC}"
for port in 8501 8502 8503 8500; do
    if ssh_cmd "lsof -i :$port" &>/dev/null; then
        PROCESS=$(ssh_cmd "lsof -i :$port | tail -1 | awk '{print \$1}'")
        echo -e "  Port $port: ${RED}✗ IN USE${NC} (by $PROCESS)"
    else
        echo -e "  Port $port: ${GREEN}✓ FREE${NC}"
    fi
done

# 8. Check app files
echo -e "\n${YELLOW}[8/8] Checking application files...${NC}"
if ssh_cmd "test -f $APP_DIR/app/app_v2.py && echo 'exists'"; then
    echo -e "  ${GREEN}✓ app/app_v2.py exists${NC}"
else
    echo -e "  ${RED}✗ app/app_v2.py not found${NC}"
    echo "  Please check if files are properly deployed"
fi

# Check recent logs
echo -e "\n${YELLOW}Checking recent Streamlit logs...${NC}"
if ssh_cmd "test -f $APP_DIR/logs/streamlit.log && echo 'exists'"; then
    echo -e "  Last 5 lines from streamlit.log:"
    ssh_cmd "tail -5 $APP_DIR/logs/streamlit.log 2>/dev/null" | sed 's/^/    /'
else
    echo "  (No streamlit.log file found)"
fi

# Summary and recommendations
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SUMMARY & RECOMMENDATIONS           ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ -z "$STREAMLIT_PIDS" ]; then
    echo -e "${YELLOW}ISSUE FOUND:${NC} Streamlit is not running"
    echo ""
    echo -e "${GREEN}SOLUTIONS:${NC}"
    echo ""
    echo "  1. Start Streamlit with default port (8501):"
    echo "     ${BLUE}bash deploy-VPS/start.sh${NC}"
    echo ""
    echo "  2. Start Streamlit with custom port:"
    echo "     ${BLUE}bash deploy-VPS/start_custom.sh 8502${NC}"
    echo ""
    echo "  3. Manual start with screen:"
    echo "     ${BLUE}ssh root@$VPS_IP${NC}"
    echo "     ${BLUE}cd $APP_DIR${NC}"
    echo "     ${BLUE}screen -S charles${NC}"
    echo "     ${BLUE}./venv/bin/streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0${NC}"
    echo "     (Press Ctrl+A, D to detach)"
    echo ""
else
    echo -e "${GREEN}STATUS:${NC} Streamlit is running!"
    echo ""
    echo "Access URL: ${BLUE}http://$VPS_IP:$DEFAULT_PORT${NC}"
    echo ""
    echo "To view logs:"
    echo "  ${BLUE}screen -r charles${NC}"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo ""
