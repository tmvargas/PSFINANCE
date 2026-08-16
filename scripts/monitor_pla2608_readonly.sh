#!/usr/bin/env bash
set -euo pipefail

# PLA-2608: captura somente leitura, a cada 120 segundos, para correlacionar
# a proxima ocorrencia informada por um usuario. O arquivo gerado nao inclui
# IP, User-Agent, nomes de contas, textos de consultas nem valores de banco.

workspace_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
evidence_file=${1:-"$workspace_dir/docs/evidencias/PLA-2608-monitor-live.log"}
interval_seconds=${PLA2608_INTERVAL_SECONDS:-120}
ssh_alias=${PLA2608_SSH_ALIAS:-plansmart-sistemas-vps69143}

mkdir -p "$(dirname "$evidence_file")"

while true; do
  {
    printf '=== coleta_inicio=%s ===\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    ssh -o BatchMode=yes -o IdentitiesOnly=yes "$ssh_alias" 'bash -s' <<'REMOTE'
set -euo pipefail
date -Is
uptime
systemctl show psfinance-staging psfinance-staging-gate \
  -p Id -p ActiveState -p SubState -p NRestarts -p MainPID \
  -p MemoryCurrent -p CPUUsageNSec
free -m
df -h /
ps -C gunicorn -o pid,ppid,stat,%cpu,%mem,rss,etimes,cmd --no-headers | \
  grep -E 'psfinance|PID' || true
ss -ltnp | grep -E ':(5001|5104|5105)[[:space:]]' || true
sudo -u postgres psql -XAtqc \
  "select now(), count(*) filter (where state = 'active'), count(*) filter (where wait_event is not null), count(*) from pg_stat_activity where datname = 'psfinance_staging'; select count(*) from pg_locks where not granted;"
curl -sS --max-time 30 -o /dev/null \
  -w 'extrato_filtrado http=%{http_code} total=%{time_total} connect=%{time_connect} starttransfer=%{time_starttransfer} bytes=%{size_download}\n' \
  'http://127.0.0.1:5001/staging/psfinance/financeiro/extrato?id_conta=5'
journalctl -u psfinance-staging -u psfinance-staging-gate -u nginx -u postgresql \
  --since '3 minutes ago' --no-pager -o short-iso | tail -n 200
tail -n 200 /var/log/nginx/psfinance_staging_5001_access.log \
  /var/log/nginx/psfinance_staging_80_access.log | \
  grep -E 'financeiro/extrato|" (499|500|502|503|504) ' | \
  tail -n 50 | \
  sed -E 's/^([^ ]+)/[IP]/; s/ "[^"]*"$/ "[USER_AGENT]"/' || true
tail -n 100 /var/log/nginx/psfinance_staging_5001_error.log \
  /var/log/nginx/psfinance_staging_80_error.log | tail -n 100 | \
  sed -E 's/client: [^,]+/client: [IP]/g; s/host: "[^"]+"/host: "[HOST]"/g'
REMOTE
    printf '=== coleta_fim=%s ===\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >>"$evidence_file" 2>&1

  sleep "$interval_seconds"
done
