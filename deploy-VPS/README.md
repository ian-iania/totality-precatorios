# Deploy TJRJ Scraper V5 on VPS

## Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: 4GB+ recommended (for 12 workers)
- **CPU**: 2+ cores
- **Disk**: 10GB+ free space
- **Port**: 8501 open for Streamlit UI

## Quick Setup (Existing Clone)

If you already have the repo cloned at `/root/charles/totality-precatorios`:

```bash
cd /root/charles/totality-precatorios
bash deploy-VPS/setup.sh
```

## First Time Install

```bash
# 1. SSH into your VPS
ssh root@your-vps-ip

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

Open in browser: `http://YOUR_VPS_IP:8501`

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
├── app/                    # Streamlit UI
├── src/                    # Core scraper
├── main_v5_all_entities.py # V5 script
├── deploy-VPS/             # Deploy scripts
├── logs/                   # Logs directory
│   ├── scraper_v3.log     # Main log
│   └── screenshots/       # Debug screenshots
├── output/                 # CSV outputs
└── venv/                   # Python environment
```
