# Deploy TJRJ Scraper V5 on VPS

## Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: 4GB+ recommended (for 12 workers)
- **CPU**: 2+ cores
- **Disk**: 10GB+ free space
- **Port**: 8501 open for Streamlit UI

## Quick Install

```bash
# 1. SSH into your VPS
ssh user@your-vps-ip

# 2. Download and run install script
curl -sSL https://raw.githubusercontent.com/ian-iania/totality-precatorios/main/deploy-VPS/install.sh | sudo bash
```

## Manual Install

```bash
# 1. Clone repository
sudo git clone https://github.com/ian-iania/totality-precatorios.git /opt/charles

# 2. Run install script
cd /opt/charles/deploy-VPS
sudo bash install.sh
```

## Service Management

```bash
# Start service
sudo systemctl start charles

# Stop service
sudo systemctl stop charles

# Restart service
sudo systemctl restart charles

# Check status
sudo systemctl status charles

# View logs
sudo journalctl -u charles -f

# View scraper logs
tail -f /opt/charles/logs/scraper_v3.log
```

## Update to Latest Version

```bash
cd /opt/charles/deploy-VPS
sudo bash update.sh
```

## Access UI

Open in browser: `http://YOUR_VPS_IP:8501`

## Firewall Configuration

If using UFW:
```bash
sudo ufw allow 8501/tcp
sudo ufw reload
```

If using iptables:
```bash
sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u charles -n 50

# Check if port is in use
sudo lsof -i :8501
```

### Playwright issues
```bash
# Reinstall browser dependencies
cd /opt/charles
sudo ./venv/bin/playwright install-deps
```

### Permission issues
```bash
# Fix ownership
sudo chown -R charles:charles /opt/charles
```

## Files Structure on VPS

```
/opt/charles/
├── app/                    # Streamlit UI
├── src/                    # Core scraper
├── main_v5_all_entities.py # V5 script
├── logs/                   # Logs directory
│   ├── scraper_v3.log     # Main log
│   └── screenshots/       # Debug screenshots
├── output/                 # CSV outputs
└── venv/                   # Python environment
```

## Security Notes

- The service runs as non-root user `charles`
- Consider using nginx reverse proxy with SSL for production
- Restrict port 8501 access via firewall if needed
