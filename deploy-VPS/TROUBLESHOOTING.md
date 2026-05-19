# Troubleshooting Guide - TJRJ Precatórios VPS

## 🔍 Current Issue Analysis

### Problem Identified

**Status**: ❌ Streamlit is NOT running on VPS
**Root Cause**: Application stopped (not a port conflict)
**Port 8501**: ✅ FREE (no conflicts)

### Diagnostic Results (May 13, 2026)

```
✓ VPS is online and accessible (209.126.12.243)
✓ SSH connection working
✓ Python environment exists
✓ Streamlit installed
✓ Port 8501 is FREE
✓ Port 8502 is FREE
✓ Port 8503 is FREE
✗ Streamlit is NOT running
✗ No screen sessions found
```

---

## 🚀 Quick Solutions

### Option 1: Start with Default Port (8501) - RECOMMENDED

**From your local machine:**

```bash
bash deploy-VPS/remote_start.sh
```

**From the VPS:**

```bash
ssh root@209.126.12.243
cd /root/charles/totality-precatorios
bash deploy-VPS/start_custom.sh
```

Access: http://209.126.12.243:8501

---

### Option 2: Start with Custom Port

**From your local machine:**

```bash
# Use port 8502
bash deploy-VPS/remote_start.sh 8502

# Or port 8503
bash deploy-VPS/remote_start.sh 8503
```

**From the VPS:**

```bash
ssh root@209.126.12.243
cd /root/charles/totality-precatorios
bash deploy-VPS/start_custom.sh 8502  # or any port
```

Access: http://209.126.12.243:PORT

---

### Option 3: Manual Start (for debugging)

```bash
# SSH into VPS
ssh root@209.126.12.243

# Navigate to project
cd /root/charles/totality-precatorios

# Start screen session
screen -S charles

# Activate environment and run
source venv/bin/activate
streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0

# Press Ctrl+A, then D to detach
```

---

## 🔧 Diagnostic Tools

### Run Full Diagnostics

```bash
bash deploy-VPS/diagnose.sh
```

This will check:
- VPS connectivity
- Project directory
- Python environment
- Streamlit installation
- Running processes
- Port availability
- Screen sessions
- Recent logs

### Quick Status Check

```bash
bash deploy-VPS/check_vps_status.sh
```

Shows:
- HTTP endpoints status
- System services
- Docker containers
- Python processes
- Disk and memory usage

---

## 📋 Common Issues & Solutions

### Issue 1: "Port is already in use"

**Symptoms:**
```
Error: Address already in use
```

**Solution A:** Kill the process

```bash
# Find what's using the port
ssh root@209.126.12.243 "lsof -i :8501"

# Kill the process
ssh root@209.126.12.243 "pkill -f streamlit"

# Or use the remote start script (it handles this automatically)
bash deploy-VPS/remote_start.sh
```

**Solution B:** Use a different port

```bash
bash deploy-VPS/remote_start.sh 8502
```

---

### Issue 2: "Cannot connect to VPS"

**Symptoms:**
```
ssh: connect to host 209.126.12.243 port 22: Connection refused
```

**Check:**
1. VPS is online
2. SSH service is running
3. Firewall allows SSH (port 22)
4. Credentials are correct

**Solution:**
```bash
# Try manual SSH first
ssh root@209.126.12.243

# If that works, credentials are fine
# If not, check VPS provider's dashboard
```

---

### Issue 3: "Streamlit starts but is not accessible"

**Symptoms:**
- Streamlit runs on VPS
- Cannot access from browser

**Check:**

```bash
# Check if Streamlit is listening on correct interface
ssh root@209.126.12.243 "lsof -i :8501"

# Should show:
# COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# python  12345  root    5u  IPv4  ...           TCP *:8501 (LISTEN)
```

**Solution:** Ensure firewall allows the port

```bash
ssh root@209.126.12.243

# UFW
sudo ufw allow 8501/tcp
sudo ufw reload

# Or iptables
sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
sudo iptables-save
```

---

### Issue 4: "Streamlit crashes on startup"

**Check logs:**

```bash
# View Streamlit logs
ssh root@209.126.12.243 "tail -f /root/charles/totality-precatorios/logs/streamlit.log"

# View screen session (if running)
ssh root@209.126.12.243
screen -r charles
```

**Common causes:**
1. Missing dependencies
2. Python version mismatch
3. Corrupt virtual environment

**Solution:**

```bash
ssh root@209.126.12.243
cd /root/charles/totality-precatorios

# Reinstall dependencies
./venv/bin/pip install --upgrade -r requirements.txt -r app/requirements.txt

# Or rebuild environment
rm -rf venv
bash deploy-VPS/setup.sh
```

---

### Issue 5: "Screen session is stuck"

**Symptoms:**
```
There is a screen on:
    12345.charles    (Attached)
```

**Solution:**

```bash
# Force kill the session
ssh root@209.126.12.243 "screen -X -S charles quit"

# Or kill all screen sessions
ssh root@209.126.12.243 "pkill screen"

# Then restart
bash deploy-VPS/remote_start.sh
```

---

## 🛠️ Advanced Troubleshooting

### Check System Resources

```bash
ssh root@209.126.12.243 "free -h && df -h"
```

If low on memory or disk:
- Stop other services
- Clean up old logs/files
- Upgrade VPS plan

### Check Python Environment

```bash
ssh root@209.126.12.243 "cd /root/charles/totality-precatorios && ./venv/bin/python --version && ./venv/bin/pip list | grep streamlit"
```

### Check Playwright (if needed)

```bash
ssh root@209.126.12.243 "cd /root/charles/totality-precatorios && ./venv/bin/playwright install chromium && ./venv/bin/playwright install-deps"
```

### View All Logs

```bash
ssh root@209.126.12.243 "cd /root/charles/totality-precatorios && ls -lh logs/"
```

---

## 📝 Port Configuration Reference

### Default Configuration
- **Streamlit UI**: 8501
- **Alternative ports**: 8502, 8503, 8500

### All Available Ports
| Port | Service | Status |
|------|---------|--------|
| 22   | SSH     | ✅ Active |
| 80   | HTTP    | ✅ Active (Caddy) |
| 443  | HTTPS   | ✅ Active (Caddy) |
| 8501 | Streamlit | ✅ Free |
| 8502 | Streamlit (alt) | ✅ Free |

### Changing Default Port

**Method 1:** Use start script with port parameter
```bash
bash deploy-VPS/start_custom.sh 8502
```

**Method 2:** Edit start.sh directly
```bash
# Edit deploy-VPS/start.sh
# Change: --server.port 8501
# To:     --server.port 8502
```

**Method 3:** Use Streamlit config file
```bash
ssh root@209.126.12.243
mkdir -p /root/charles/totality-precatorios/.streamlit
cat > /root/charles/totality-precatorios/.streamlit/config.toml << EOF
[server]
port = 8502
address = "0.0.0.0"
EOF
```

---

## 🔐 Security Notes

### Exposed Credentials
⚠️ **WARNING**: Credentials are exposed in scripts for development convenience.
**Production**: Use SSH keys instead of passwords.

**Setup SSH key authentication:**
```bash
# On your local machine
ssh-keygen -t ed25519 -C "your_email@example.com"
ssh-copy-id root@209.126.12.243

# Then remove password from scripts
```

### Firewall Best Practices
```bash
ssh root@209.126.12.243

# Only allow necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8501/tcp
ufw enable
```

---

## 📞 Quick Reference

### Start Application
```bash
bash deploy-VPS/remote_start.sh [PORT]
```

### Stop Application
```bash
bash deploy-VPS/stop.sh
```

### Check Status
```bash
bash deploy-VPS/check_vps_status.sh
```

### Run Diagnostics
```bash
bash deploy-VPS/diagnose.sh
```

### View Logs
```bash
ssh root@209.126.12.243 "tail -f /root/charles/totality-precatorios/logs/streamlit.log"
```

### Update Code
```bash
bash deploy-VPS/update.sh
```

---

## 🆘 Emergency Recovery

If everything fails:

```bash
# 1. SSH into VPS
ssh root@209.126.12.243

# 2. Kill everything
pkill -f streamlit
pkill -f python
pkill screen

# 3. Fresh start
cd /root/charles/totality-precatorios
git pull origin main
bash deploy-VPS/setup.sh
bash deploy-VPS/start_custom.sh
```

---

**Last Updated**: May 13, 2026
**Diagnosed By**: Claude Code
**Status**: ✅ Solutions Implemented
