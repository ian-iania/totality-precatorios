# 🚀 Quick Start Guide - TJRJ Precatórios

## ✅ App is NOW RUNNING!

**Access URL**: http://209.126.12.243:8501

---

## 📊 Current Status

```
✓ Streamlit: RUNNING on port 8501
✓ VPS: Online (209.126.12.243)
✓ Screen session: charles
✓ HTTP Status: 200 OK
```

---

## 🎯 Quick Commands (Run from Local Machine)

### Start Application
```bash
bash deploy-VPS/remote_start.sh
```

### Start on Different Port
```bash
bash deploy-VPS/remote_start.sh 8502
```

### Check Status
```bash
bash deploy-VPS/check_vps_status.sh
```

### Stop Application
```bash
bash deploy-VPS/stop.sh
```

### Run Diagnostics
```bash
bash deploy-VPS/diagnose.sh
```

---

## 🔍 What Was The Problem?

### Original Issue
The app was **not running** - it wasn't a port conflict.

### Root Cause
- Streamlit process had stopped
- No screen session was active
- Port 8501 was actually free (not in use)

### Solution Implemented
Created management scripts that:
1. Check VPS connectivity
2. Verify port availability
3. Kill any zombie processes
4. Start Streamlit in screen session
5. Verify successful startup

---

## 📁 New Tools Created

### 1. `diagnose.sh` - Full Diagnostic Tool
Checks:
- VPS connectivity
- Project files
- Python environment
- Streamlit installation
- Running processes
- Port availability
- Screen sessions
- Recent logs

**Usage:**
```bash
bash deploy-VPS/diagnose.sh
```

### 2. `remote_start.sh` - Remote Start Tool
Starts Streamlit from your local machine with:
- Automatic port detection
- Process cleanup
- Screen session management
- Success verification

**Usage:**
```bash
bash deploy-VPS/remote_start.sh [PORT]
```

### 3. `start_custom.sh` - VPS-Side Start Tool
Runs on the VPS with:
- Port validation
- Conflict resolution
- Flexible port configuration
- Firewall check

**Usage (on VPS):**
```bash
bash deploy-VPS/start_custom.sh [PORT]
```

### 4. `TROUBLESHOOTING.md` - Complete Guide
Comprehensive documentation covering:
- All common issues
- Step-by-step solutions
- Port configuration
- Security notes
- Emergency recovery

---

## 🛠️ Common Tasks

### View Logs in Real-Time
```bash
ssh root@209.126.12.243 'tail -f /root/charles/totality-precatorios/logs/streamlit.log'
```

### Access Screen Session
```bash
ssh root@209.126.12.243
screen -r charles
# Press Ctrl+A, then D to detach
```

### Update Code and Restart
```bash
bash deploy-VPS/update.sh
```

### Kill Everything and Restart
```bash
ssh root@209.126.12.243
pkill -f streamlit
pkill screen
cd /root/charles/totality-precatorios
bash deploy-VPS/start_custom.sh
```

---

## 🔐 VPS Access

| Item | Value |
|------|-------|
| **IP** | 209.126.12.243 |
| **User** | root |
| **Port** | 8501 |
| **URL** | http://209.126.12.243:8501 |
| **Project** | /root/charles/totality-precatorios |

---

## 📋 Port Reference

| Port | Status | Service |
|------|--------|---------|
| 8501 | ✅ ACTIVE | Streamlit (current) |
| 8502 | ✅ FREE | Available |
| 8503 | ✅ FREE | Available |
| 8500 | ✅ FREE | Available |

---

## 🆘 If App Goes Down Again

**Quick fix from local machine:**
```bash
bash deploy-VPS/remote_start.sh
```

**Or manually:**
```bash
ssh root@209.126.12.243
cd /root/charles/totality-precatorios
screen -S charles
source venv/bin/activate
streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0
# Ctrl+A, D to detach
```

---

## 📞 Script Reference

| Script | Description | Run From |
|--------|-------------|----------|
| `remote_start.sh` | Start from local machine | Local |
| `start_custom.sh` | Start with custom port | VPS |
| `diagnose.sh` | Full diagnostics | Local |
| `check_vps_status.sh` | Quick status check | Local |
| `stop.sh` | Stop all processes | VPS |
| `update.sh` | Update and restart | VPS |

---

**Last Updated**: May 13, 2026
**Status**: ✅ **RESOLVED AND RUNNING**
