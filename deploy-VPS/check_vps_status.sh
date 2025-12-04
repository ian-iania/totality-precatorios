#!/bin/bash
# =============================================================================
# VPS Status Check Script
# Run from local machine to verify VPS services
# =============================================================================

# Configuration
VPS_IP="209.126.12.243"
VPS_USER="root"
VPS_PASS="Mark3tf0ld2025"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== VPS Status Check ==="
echo "VPS: $VPS_IP"
echo "Time: $(date)"
echo ""

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    local status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null)
    if [ "$status" = "200" ] || [ "$status" = "302" ]; then
        echo -e "  $name: ${GREEN}✓ OK${NC} (HTTP $status)"
    else
        echo -e "  $name: ${RED}✗ FAIL${NC} (HTTP $status)"
    fi
}

# Function to run SSH command
ssh_cmd() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$VPS_USER@$VPS_IP" "$1" 2>/dev/null
}

echo -e "${YELLOW}[HTTP Endpoints]${NC}"
check_http "Streamlit (direct)" "http://$VPS_IP:8501"
check_http "TJRJ DuckDNS" "https://tjrj.duckdns.org"
check_http "Marketfold DuckDNS" "https://marketfold.duckdns.org"

echo ""
echo -e "${YELLOW}[System Services]${NC}"
CADDY=$(ssh_cmd "systemctl is-active caddy")
if [ "$CADDY" = "active" ]; then
    echo -e "  Caddy: ${GREEN}✓ active${NC}"
else
    echo -e "  Caddy: ${RED}✗ $CADDY${NC}"
fi

DOCKER=$(ssh_cmd "systemctl is-active docker")
if [ "$DOCKER" = "active" ]; then
    echo -e "  Docker: ${GREEN}✓ active${NC}"
else
    echo -e "  Docker: ${RED}✗ $DOCKER${NC}"
fi

echo ""
echo -e "${YELLOW}[Docker Containers]${NC}"
ssh_cmd "docker ps --format '  {{.Names}}: {{.Status}}' | head -5"

echo ""
echo -e "${YELLOW}[Python Processes]${NC}"
STREAMLIT=$(ssh_cmd "pgrep -f streamlit" | wc -l)
if [ "$STREAMLIT" -gt 0 ]; then
    echo -e "  Streamlit: ${GREEN}✓ running${NC}"
else
    echo -e "  Streamlit: ${RED}✗ not running${NC}"
fi

ORCHESTRATOR=$(ssh_cmd "pgrep -f 'main_v6_orchestrator\|main_v5'" | wc -l)
if [ "$ORCHESTRATOR" -gt 0 ]; then
    echo -e "  Extraction: ${GREEN}✓ running${NC}"
else
    echo -e "  Extraction: ${YELLOW}○ idle${NC}"
fi

echo ""
echo -e "${YELLOW}[Disk Usage]${NC}"
ssh_cmd "df -h / | tail -1 | awk '{print \"  Root: \" \$3 \" / \" \$2 \" (\" \$5 \" used)\"}'"
ssh_cmd "du -sh /root/charles/totality-precatorios/output 2>/dev/null | awk '{print \"  Output files: \" \$1}'"

echo ""
echo -e "${YELLOW}[Memory]${NC}"
ssh_cmd "free -h | grep Mem | awk '{print \"  RAM: \" \$3 \" / \" \$2 \" used\"}'"

echo ""
echo "=== Check Complete ==="
