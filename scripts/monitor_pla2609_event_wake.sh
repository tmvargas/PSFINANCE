#!/usr/bin/env bash
set -euo pipefail

# Observa o coletor somente leitura da PLA-2609 e acorda o GDSIS apenas quando
# existe uma ocorrência verificável. O deadline permanece no executionPolicy
# nativo do Paperclip; amostras saudáveis não geram chamadas à API.

monitor_unit=${PLA2609_MONITOR_UNIT:-psfinance-staging-monitor-pla2609.service}
state_file=${PLA2609_STATE_FILE:-/run/psfinance-staging-monitor-pla2609.state}
log_file=${PLA2609_LOG_FILE:-/var/log/psfinance-staging-monitor-pla2609.log}
event_log=${PLA2609_EVENT_LOG:-/var/log/psfinance-staging-monitor-pla2609-event.log}
event_marker=${PLA2609_EVENT_MARKER:-/run/psfinance-staging-monitor-pla2609-event.sent}
credential_file=${PLA2609_PAPERCLIP_CREDENTIAL_FILE:-/run/psfinance-staging-monitor-pla2609-paperclip.env}
interval_seconds=${PLA2609_EVENT_INTERVAL_SECONDS:-120}
stale_after_seconds=${PLA2609_STALE_AFTER_SECONDS:-300}
watch_once=${PLA2609_WATCH_ONCE:-0}

expected_routes=(health gate home extrato titulos analise)
baseline_restarts=""
last_checked_sample=0

log_event() {
  local kind=$1
  local detail=$2
  printf 'timestamp_utc=%s kind=%s detail=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$kind" "$detail" >>"$event_log"
}

read_state_value() {
  local key=$1
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$state_file"
}

restart_total() {
  systemctl show psfinance-staging psfinance-staging-gate -p NRestarts --value | \
    awk 'NF {total += $1} END {print total + 0}'
}

notify_paperclip() {
  local reason=$1

  if [[ -f "$event_marker" ]]; then
    return 0
  fi
  if [[ ! -r "$credential_file" ]]; then
    log_event wake_error credential_file_unavailable
    return 1
  fi

  # O arquivo e criado operacionalmente com modo 0600 e nunca e versionado.
  # shellcheck disable=SC1090
  source "$credential_file"
  if [[ -z "${PAPERCLIP_API_URL:-}" || -z "${PAPERCLIP_API_KEY:-}" || -z "${PAPERCLIP_ISSUE_ID:-}" ]]; then
    log_event wake_error credential_fields_unavailable
    return 1
  fi

  if curl --fail --silent --show-error --max-time 30 \
    -X POST \
    -H "Authorization: Bearer ${PAPERCLIP_API_KEY}" \
    -H 'Content-Type: application/json' \
    -o /dev/null \
    "${PAPERCLIP_API_URL%/}/api/issues/${PAPERCLIP_ISSUE_ID}/monitor/check-now"; then
    umask 077
    printf 'timestamp_utc=%s\nreason=%s\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$reason" >"$event_marker"
    log_event wake_sent "$reason"
    return 0
  fi

  log_event wake_error api_request_failed
  return 1
}

latest_sample_block() {
  local sample=$1
  awk -v sample="$sample" '
    index($0, "=== sample=" sample " ") == 1 {inside = 1}
    inside {print}
    $0 == "=== sample_fim=" sample " ===" {exit}
  ' "$log_file"
}

check_sample() {
  local sample=$1
  local block
  local route
  local route_count
  local current_restarts

  block=$(latest_sample_block "$sample")
  if ! grep -q "^=== sample_fim=${sample} ===$" <<<"$block"; then
    printf '%s' sample_incomplete
    return 1
  fi

  route_count=$(grep -c '^route=' <<<"$block" || true)
  if (( route_count != ${#expected_routes[@]} )); then
    printf 'route_count_%s' "$route_count"
    return 1
  fi

  for route in "${expected_routes[@]}"; do
    if ! grep -Eq "^route=${route} http=200( |$)" <<<"$block"; then
      printf 'route_%s_not_200' "$route"
      return 1
    fi
  done

  if grep -Eq '^(ActiveState|SubState)=' <<<"$block" && \
    grep -Eq '^(ActiveState|SubState)=(failed|inactive|dead|exited|deactivating|activating)$' <<<"$block"; then
    printf '%s' application_unit_not_running
    return 1
  fi

  current_restarts=$(restart_total)
  if [[ -z "$baseline_restarts" ]]; then
    baseline_restarts=$current_restarts
  elif (( current_restarts > baseline_restarts )); then
    printf 'application_restart_%s_to_%s' "$baseline_restarts" "$current_restarts"
    return 1
  fi

  return 0
}

mkdir -p "$(dirname "$event_log")" "$(dirname "$event_marker")"
baseline_restarts=$(restart_total)
log_event watcher_started "unit=${monitor_unit}_baseline_restarts=${baseline_restarts}"

while true; do
  reason=""
  now_epoch=$(date +%s)

  if [[ ! -r "$state_file" || ! -r "$log_file" ]]; then
    reason=collector_evidence_unavailable
  elif ! systemctl is-active --quiet "$monitor_unit"; then
    state_status=$(read_state_value status || true)
    deadline_utc=$(read_state_value deadline_utc || true)
    deadline_epoch=$(date -d "$deadline_utc" +%s 2>/dev/null || printf '0')
    if [[ "$state_status" == completed && "$deadline_epoch" =~ ^[0-9]+$ && "$now_epoch" -ge "$deadline_epoch" ]]; then
      log_event watcher_completed deadline_reached
      exit 0
    fi
    reason=collector_unit_not_active
  else
    updated_utc=$(read_state_value updated_utc || true)
    updated_epoch=$(date -d "$updated_utc" +%s 2>/dev/null || printf '0')
    sample=$(read_state_value sample || true)

    if [[ ! "$updated_epoch" =~ ^[0-9]+$ || "$updated_epoch" -eq 0 ]]; then
      reason=collector_state_timestamp_invalid
    elif (( now_epoch - updated_epoch > stale_after_seconds )); then
      reason=collector_state_stale
    elif [[ ! "$sample" =~ ^[0-9]+$ || "$sample" -eq 0 ]]; then
      reason=collector_sample_invalid
    elif (( sample > last_checked_sample )); then
      if ! reason=$(check_sample "$sample"); then
        :
      else
        reason=""
      fi
      last_checked_sample=$sample
    fi
  fi

  if [[ -n "$reason" ]]; then
    log_event occurrence "$reason"
    if notify_paperclip "$reason"; then
      exit 0
    fi
  elif [[ "$watch_once" == 1 ]]; then
    log_event watcher_completed healthy_once
    exit 0
  fi

  sleep "$interval_seconds"
done
