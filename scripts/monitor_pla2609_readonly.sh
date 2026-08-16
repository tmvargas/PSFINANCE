#!/usr/bin/env bash
set -euo pipefail

# Monitor somente leitura da PLA-2609. O processo termina após 24 horas por
# padrão e mantém log/estado limitados para não consumir o disco da VPS.

interval_seconds=${PLA2609_INTERVAL_SECONDS:-120}
duration_seconds=${PLA2609_DURATION_SECONDS:-86400}
max_log_bytes=${PLA2609_MAX_LOG_BYTES:-10485760}
log_file=${PLA2609_LOG_FILE:-/var/log/psfinance-staging-monitor-pla2609.log}
state_file=${PLA2609_STATE_FILE:-/run/psfinance-staging-monitor-pla2609.state}
base_url=${PLA2609_BASE_URL:-http://127.0.0.1:5001}
started_epoch=$(date +%s)
deadline_epoch=$((started_epoch + duration_seconds))
sample=0

write_state() {
  local status=$1
  local now_epoch
  local state_tmp
  now_epoch=$(date +%s)
  state_tmp="${state_file}.tmp"
  {
    printf 'status=%s\n' "$status"
    printf 'pid=%s\n' "$$"
    printf 'started_utc=%s\n' "$(date -u -d "@$started_epoch" +%Y-%m-%dT%H:%M:%SZ)"
    printf 'updated_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'deadline_utc=%s\n' "$(date -u -d "@$deadline_epoch" +%Y-%m-%dT%H:%M:%SZ)"
    printf 'sample=%s\n' "$sample"
    printf 'log_file=%s\n' "$log_file"
  } >"$state_tmp"
  mv "$state_tmp" "$state_file"
}

rotate_log_if_needed() {
  local current_bytes=0
  if [[ -f "$log_file" ]]; then
    current_bytes=$(stat -c %s "$log_file")
  fi
  if (( current_bytes >= max_log_bytes )); then
    mv -f "$log_file" "${log_file}.1"
  fi
}

probe() {
  local label=$1
  local path=$2
  local result
  result=$(curl -sS --max-time 30 -o /dev/null \
    -w 'http=%{http_code} total=%{time_total} connect=%{time_connect} starttransfer=%{time_starttransfer} bytes=%{size_download}' \
    "${base_url}${path}" 2>&1) || result="curl_error=${result//$'\n'/ }"
  printf 'route=%s %s\n' "$label" "$result"
}

sanitize_logs() {
  sed -E \
    -e 's/([0-9]{1,3}\.){3}[0-9]{1,3}/[IP]/g' \
    -e 's/client: [^,]+/client: [IP]/g' \
    -e 's/host: "[^"]+"/host: "[HOST]"/g' \
    -e 's/^([^ ]+) ([^ ]+) ([^ ]+)/[IP] [IDENT] [USER]/' \
    -e 's/ "[^"]*"$/ "[USER_AGENT]"/'
}

finish() {
  write_state completed
  printf '=== monitor_fim=%s samples=%s ===\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$sample" >>"$log_file"
}
trap finish EXIT

mkdir -p "$(dirname "$log_file")" "$(dirname "$state_file")"
write_state running

while (( $(date +%s) < deadline_epoch )); do
  sample=$((sample + 1))
  rotate_log_if_needed
  {
    printf '=== sample=%s timestamp_utc=%s monitor_pid=%s ===\n' \
      "$sample" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$$"
    uptime
    systemctl show psfinance-staging psfinance-staging-gate \
      -p Id -p ActiveState -p SubState -p NRestarts -p MainPID \
      -p MemoryCurrent -p CPUUsageNSec
    free -m
    df -h /
    ps -C gunicorn -o pid,ppid,stat,%cpu,%mem,rss,etimes,cmd --no-headers | \
      grep -E 'psfinance|PID' | sanitize_logs || true
    ss -ltnp | grep -E ':(5001|5104|5105)[[:space:]]' | sanitize_logs || true
    sudo -u postgres psql -XAtqc \
      "select now(), count(*) filter (where state = 'active'), count(*) filter (where wait_event is not null), count(*) from pg_stat_activity where datname = 'psfinance_staging'; select count(*) from pg_locks where not granted;"
    probe health '/health'
    probe gate '/gate'
    probe home '/staging/psfinance/financeiro/'
    probe extrato '/staging/psfinance/financeiro/extrato?id_conta=5'
    probe titulos '/staging/psfinance/financeiro/titulos?mes=8&ano=2026'
    probe analise '/staging/psfinance/financeiro/analise?mes=8&ano=2026'
    journalctl -u psfinance-staging -u psfinance-staging-gate -u nginx -u postgresql \
      --since "${interval_seconds} seconds ago" --no-pager -o short-iso | \
      tail -n 200 | sanitize_logs
    tail -n 200 /var/log/nginx/psfinance_staging_5001_access.log \
      /var/log/nginx/psfinance_staging_80_access.log 2>/dev/null | \
      grep -E 'financeiro/(extrato|titulos|analise)|" (499|500|502|503|504) ' | \
      tail -n 80 | sanitize_logs || true
    tail -n 100 /var/log/nginx/psfinance_staging_5001_error.log \
      /var/log/nginx/psfinance_staging_80_error.log 2>/dev/null | \
      tail -n 100 | sanitize_logs || true
    printf '=== sample_fim=%s ===\n\n' "$sample"
  } >>"$log_file" 2>&1
  write_state running
  sleep "$interval_seconds"
done
