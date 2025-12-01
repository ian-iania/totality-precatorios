#!/bin/bash
# Stop Streamlit and cleanup
pkill -f streamlit || true
pkill -f chromium || true
screen -X -S charles quit 2>/dev/null || true
echo "✅ Streamlit stopped"
