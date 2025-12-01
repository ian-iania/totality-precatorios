#!/bin/bash
# Start Streamlit in background using screen
cd /root/charles/totality-precatorios
screen -dmS charles ./venv/bin/streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0
echo "✅ Streamlit started in background (screen session: charles)"
echo "   View: screen -r charles"
echo "   Detach: Ctrl+A, D"
echo "   Access: http://YOUR_VPS_IP:8501"
