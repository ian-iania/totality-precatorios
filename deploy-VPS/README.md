# Deploy Totality Precatórios on VPS

## 🌐 Production Access

| Item | Value |
|------|-------|
| **URL** | http://209.126.12.243:8501 |
| **SSH** | `ssh root@209.126.12.243` |
| **Project** | `/root/charles/totality-precatorios` |

## Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: 8GB+ recommended (for 15-20 workers)
- **CPU**: 4+ cores
- **Disk**: 10GB+ free space
- **Port**: 8501 open for Streamlit UI

## Quick Commands

```bash
# SSH into VPS
ssh root@209.126.12.243

# Go to project
cd /root/charles/totality-precatorios

# Update and restart
bash deploy-VPS/update.sh

# Or manually:
git pull origin main
pkill -f streamlit
screen -dmS charles ./venv/bin/streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0
```

## First Time Install

```bash
# 1. SSH into your VPS
ssh root@209.126.12.243

# 2. Create directory and clone
mkdir -p /root/charles
cd /root/charles
git clone https://github.com/ian-iania/totality-precatorios.git

# 3. Run setup
cd totality-precatorios
bash deploy-VPS/setup.sh
```

## Scripts Available

| Script | Description |
|--------|-------------|
| `setup.sh` | First-time setup (dependencies, venv, Playwright) |
| `update.sh` | Pull latest code and restart |
| `start.sh` | Start Streamlit in background |
| `stop.sh` | Stop Streamlit and cleanup |

## Daily Usage

```bash
cd /root/charles/totality-precatorios/deploy-VPS

# Start
bash start.sh

# Stop
bash stop.sh

# Update and restart
bash update.sh
```

## Screen Management

```bash
# View running session
screen -r charles

# Detach (keep running)
# Press Ctrl+A, then D

# List sessions
screen -ls

# Kill session
screen -X -S charles quit
```

## View Logs

```bash
# Scraper logs
tail -f /root/charles/totality-precatorios/logs/scraper_v3.log

# Streamlit output (in screen)
screen -r charles
```

## Access UI

Open in browser: **http://209.126.12.243:8501**

The UI V2 provides:
- Regime selection (ESPECIAL/GERAL)
- Configurable workers (1-20)
- Real-time progress via log polling
- Downloads tab with file filters

## Firewall Configuration

```bash
# UFW
ufw allow 8501/tcp
ufw reload

# iptables
iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
```

## Troubleshooting

### Streamlit won't start
```bash
# Check if port is in use
lsof -i :8501

# Kill stale processes
pkill -f streamlit
pkill -f chromium
```

### Playwright issues
```bash
cd /root/charles/totality-precatorios
./venv/bin/playwright install-deps
```

## Files Structure

```
/root/charles/totality-precatorios/
├── app/
│   ├── app_v2.py           # Streamlit UI V2 (decoupled)
│   ├── app.py              # Legacy UI (deprecated)
│   └── integration.py      # Backend integration
├── src/
│   └── scraper_v3.py       # Core scraper
├── main_v6_orchestrator.py # V6 with gap recovery
├── main_v5_all_entities.py # V5 script
├── gap_recovery.py         # Gap detection/recovery
├── deploy-VPS/             # Deploy scripts
│   ├── setup.sh            # First-time setup
│   ├── update.sh           # Update and restart
│   ├── start.sh            # Start Streamlit
│   └── stop.sh             # Stop all
├── logs/
│   ├── scraper_v3.log      # Main extraction log
│   └── orchestrator_v6.log # Orchestrator log
├── output/                 # CSV/Excel outputs
└── venv/                   # Python environment
```
