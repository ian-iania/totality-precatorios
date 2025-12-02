# DuckDNS + Caddy Reverse Proxy Setup

Documenta o processo completo para expor o Streamlit da VPS via `https://tjrj.duckdns.org` com TLS automático.

## 1. Pré-requisitos
- Acesso root à VPS (Ubuntu 24.04).
- Porta 8501 já servindo o Streamlit (`screen -dmS charles ./venv/bin/streamlit run app/app_v2.py --server.port 8501`).
- Conta no [duckdns.org](https://www.duckdns.org/) com subdomínio `tjrj` apontando para o IP público.
- Token DuckDNS: `13f2518c-b0b5-414b-94e6-121d03b817d6` (trocar se for regenerado).

## 2. Atualização automática de IP (DuckDNS)
1. Criar script e diretório:
   ```bash
   mkdir -p /root/duckdns
   cat <<'EOF' >/root/duckdns/update.sh
   #!/usr/bin/env bash
   DOMAIN="tjrj"
   TOKEN="13f2518c-b0b5-414b-94e6-121d03b817d6"
   curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=" \
     >/var/log/duckdns.log
   EOF
   chmod +x /root/duckdns/update.sh
   ```
2. Adicionar ao cron (executa a cada 5 min):
   ```bash
   (crontab -l 2>/dev/null; echo "*/5 * * * * /root/duckdns/update.sh >/dev/null 2>&1") | crontab -
   ```
3. Testar:
   ```bash
   /root/duckdns/update.sh && cat /var/log/duckdns.log  # espera "OK"
   ```

## 3. Instalar Caddy (repositório oficial)
> O pacote padrão do Ubuntu (2.6.2) possui bug no ACME. Use o repo oficial (>=2.8).
```bash
systemctl stop caddy 2>/dev/null || true
apt remove -y caddy || true

apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/deb/debian/dists/debian/Release.gpg' \
  | gpg --dearmor >/usr/share/keyrings/caddy-stable-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] \
https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" \
  >/etc/apt/sources.list.d/caddy-stable.list

apt update
apt install -y caddy
```

## 4. Configurar Caddyfile
```bash
cat <<'EOF' >/etc/caddy/Caddyfile
tjrj.duckdns.org {
    reverse_proxy 127.0.0.1:8501
}
EOF
systemctl enable --now caddy
```

## 5. Liberar portas 80/443
```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload
```
Se houver firewall externo (Contabo, AWS etc.), liberar também por lá.

## 6. Verificar emissão TLS
```bash
journalctl -u caddy -n 100 -f
```
Mensagem esperada:
```
... http.acme_client ... validations succeeded
... tls.obtain ... certificate obtained successfully
```

## 7. Testes finais
```bash
curl -I http://tjrj.duckdns.org       # deve retornar 308 -> https
curl -I https://tjrj.duckdns.org      # deve retornar 200.
```
Abrir no navegador: `https://tjrj.duckdns.org`.

## 8. Manutenção
- Logs DuckDNS: `/var/log/duckdns.log`.
- Logs Caddy: `journalctl -u caddy -f`.
- Renovação TLS é automática (Caddy renova ~30 dias antes do vencimento).
- Para alterar o domínio ou porta interna, editar `/etc/caddy/Caddyfile` e `systemctl restart caddy`.
