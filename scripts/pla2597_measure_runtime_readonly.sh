#!/usr/bin/env bash
set -euo pipefail

base_url=${PLA2597_BASE_URL:-http://127.0.0.1:5001}
route='/staging/psfinance/financeiro/extrato?id_empresa=1&id_conta=14&data_ini=2026-08-01&data_fim=2026-08-16'
samples_file=$(mktemp)
responses_file=$(mktemp)
trap 'rm -f "$samples_file" "$responses_file"' EXIT

started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
(
  for _ in $(seq 1 30); do
    app_pids=$(pgrep -d, -f 'gunicorn.*src.app:app' || true)
    if [[ -n "$app_pids" ]]; then
      ps -p "$app_pids" -o %cpu=,rss= | awk '{cpu += $1; rss += $2} END {printf "%.2f %d\n", cpu, rss}'
    fi
    sleep 0.1
  done
) > "$samples_file" &
sampler_pid=$!

seq 1 30 | xargs -P6 -I{} curl -sS -o /dev/null --max-time 10 \
  -w '%{http_code} %{time_total}\n' "${base_url}${route}" > "$responses_file"
wait "$sampler_pid"
finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)

read -r cpu_max rss_max cpu_avg < <(
  awk 'BEGIN {maxcpu=0; maxrss=0} {sum+=$1; count++; if($1>maxcpu)maxcpu=$1; if($2>maxrss)maxrss=$2} END {printf "%.2f %d %.2f\n",maxcpu,maxrss,sum/count}' "$samples_file"
)
read -r response_count errors max_seconds avg_seconds < <(
  awk '{count++; sum+=$2; if($1!=200)errors++; if($2>max)max=$2} END {printf "%d %d %.6f %.6f\n",count,errors+0,max,sum/count}' "$responses_file"
)

database_url=${PSFINANCE_STAGING_DATABASE_URL:-${PSFINANCE_DATABASE_URL:-${DATABASE_URL:-}}}
if [[ -z "$database_url" ]]; then
  echo "URL do PostgreSQL de staging não configurada" >&2
  exit 2
fi
export PGOPTIONS='-c default_transaction_read_only=on'
db_stats=$(/opt/plansmart/sistemas/psfinance/staging/venv/bin/python - <<'PY'
import os
from sqlalchemy import create_engine, text

url = os.environ.get("PSFINANCE_STAGING_DATABASE_URL") or os.environ.get("PSFINANCE_DATABASE_URL") or os.environ["DATABASE_URL"]
engine = create_engine(url, future=True)
with engine.connect() as connection:
    row = connection.execute(text("""
        SELECT current_setting('max_connections'),
               count(*) FILTER (WHERE datname=current_database()),
               count(*) FILTER (WHERE datname=current_database() AND state='active'),
               count(*) FILTER (WHERE datname=current_database() AND wait_event_type='Lock'),
               count(*) FILTER (WHERE datname=current_database() AND state='idle')
          FROM pg_stat_activity
    """)).one()
print("|".join(str(value) for value in row))
PY
)
IFS='|' read -r max_connections db_connections db_active db_lock_waiting db_idle <<< "$db_stats"

cat <<EOF
{
  "started_at": "$started_at",
  "finished_at": "$finished_at",
  "requests": $response_count,
  "concurrency": 6,
  "http_errors": $errors,
  "average_seconds": $avg_seconds,
  "maximum_seconds": $max_seconds,
  "gunicorn_cpu_average_percent": $cpu_avg,
  "gunicorn_cpu_maximum_percent": $cpu_max,
  "gunicorn_rss_maximum_kib": $rss_max,
  "postgres_max_connections": $max_connections,
  "postgres_database_connections_after_load": $db_connections,
  "postgres_active_after_load": $db_active,
  "postgres_lock_waiting_after_load": $db_lock_waiting,
  "postgres_idle_after_load": $db_idle
}
EOF
