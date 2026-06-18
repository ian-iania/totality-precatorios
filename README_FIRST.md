# README FIRST - TJRJ Precatórios Production

Read this first when the app appears to be offline.

Last verified: 2026-06-18

## What Runs In Production

- App type: Streamlit
- Entry point: `app/app_v2.py`
- VPS: `209.126.12.243`
- SSH: `ssh root@209.126.12.243`
- Remote path: `/root/charles/totality-precatorios`
- Direct URL: `http://209.126.12.243:8501`
- Public URL via Caddy/DuckDNS: `https://tjrj.duckdns.org`
- Runtime session: detached `screen` session named `charles`
- Expected port: `8501`

Do not put passwords or secrets in this file.

## 1. Check If The App Is Online

From this local project directory:

```bash
bash deploy-VPS/check_vps_status.sh
```

Healthy output should show:

- `Streamlit (direct): OK (HTTP 200)`
- `TJRJ DuckDNS: OK (HTTP 200)`
- `Streamlit: running`

Manual HTTP checks:

```bash
curl -I --max-time 15 http://209.126.12.243:8501
curl -I --max-time 15 https://tjrj.duckdns.org
```

Both endpoints should return `HTTP 200`.

## 2. Fast Restart

From this local project directory:

```bash
bash deploy-VPS/remote_start.sh
```

Then check again:

```bash
bash deploy-VPS/check_vps_status.sh
```

## 3. Manual Restart If The Script Hangs

SSH into the VPS:

```bash
ssh root@209.126.12.243
```

Run:

```bash
cd /root/charles/totality-precatorios
mkdir -p logs
screen -X -S charles quit >/dev/null 2>&1 || true
screen -dmS charles bash -lc 'cd /root/charles/totality-precatorios && exec ./venv/bin/streamlit run app/app_v2.py --server.port 8501 --server.address 0.0.0.0 >> logs/streamlit.log 2>&1'
```

Validate on the VPS:

```bash
screen -ls
lsof -i :8501
curl -I --max-time 15 http://127.0.0.1:8501
```

Validate externally from the local machine:

```bash
curl -I --max-time 15 http://209.126.12.243:8501
curl -I --max-time 15 https://tjrj.duckdns.org
```

Expected runtime state:

- `screen` shows a detached session named `charles`
- `lsof -i :8501` shows Streamlit listening on `*:8501`
- local and external HTTP checks return `HTTP 200`

## 4. Debugging Commands

View Streamlit logs:

```bash
ssh root@209.126.12.243 'tail -f /root/charles/totality-precatorios/logs/streamlit.log'
```

Attach to the running screen session:

```bash
ssh root@209.126.12.243
screen -r charles
```

Detach from `screen` without stopping the app:

```text
Ctrl+A, then D
```

## 5. Known Incident: 2026-06-18

Symptoms:

- VPS was online
- Caddy was active
- Docker was active
- `http://209.126.12.243:8501` was unreachable
- `https://tjrj.duckdns.org` returned `502`
- no Streamlit process was running
- no `screen` session existed

Cause:

- The Streamlit process had stopped.

Recovery:

- Started `app/app_v2.py` in a detached `screen` session named `charles`.
- Confirmed Streamlit listening on `*:8501`.
- Confirmed both direct IP and DuckDNS returned `HTTP 200`.

