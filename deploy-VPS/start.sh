#!/bin/bash
# Start Streamlit in background using screen
cd /root/charles/totality-precatorios
screen -dmS charles ./venv/bin/streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_VPS_IP")

echo "✅ Streamlit V2 started in background (screen session: charles)"
echo "   View: screen -r charles"
echo "   Detach: Ctrl+A, D"
echo "   Access: http://${PUBLIC_IP}:8501"
