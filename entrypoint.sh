#!/usr/bin/env bash

set -u

: "${NUXT_API_PROXY_BASE:=http://${API_HOST}:${API_PORT}}"
export NUXT_API_PROXY_BASE HOST="$UI_HOST" PORT="$UI_PORT"

api_pid=
ui_pid=
shutdown_done=0

shutdown() {
  if [ "$shutdown_done" -eq 1 ]; then
    return
  fi

  shutdown_done=1
  trap - TERM INT

  if [ -n "$api_pid" ]; then
    kill -TERM "$api_pid" 2>/dev/null || true
  fi
  if [ -n "$ui_pid" ]; then
    kill -TERM "$ui_pid" 2>/dev/null || true
  fi

  # Wait for FastAPI first so its lifespan closes DuckDB before the container exits.
  if [ -n "$api_pid" ]; then
    wait "$api_pid" 2>/dev/null || true
  fi
  if [ -n "$ui_pid" ]; then
    wait "$ui_pid" 2>/dev/null || true
  fi
}

wait_for_api() {
  local attempts="${API_READINESS_ATTEMPTS:-60}"
  local interval="${API_READINESS_INTERVAL:-1}"
  local health_url="http://127.0.0.1:${API_PORT}/health"

  while [ "$attempts" -gt 0 ]; do
    if ! kill -0 "$api_pid" 2>/dev/null; then
      echo "FastAPI exited before becoming ready" >&2
      return 1
    fi

    if node -e 'fetch(process.argv[1]).then(response => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))' "$health_url"; then
      return 0
    fi

    attempts=$((attempts - 1))
    sleep "$interval"
  done

  echo "FastAPI did not become ready at $health_url" >&2
  return 1
}

trap 'shutdown; exit 143' TERM
trap 'shutdown; exit 130' INT

cd /app/api
fastapi run main.py --host "$API_HOST" --port "$API_PORT" &
api_pid=$!

if ! wait_for_api; then
  shutdown
  exit 1
fi

node /app/ui/.output/server/index.mjs &
ui_pid=$!

wait "$ui_pid"
status=$?
shutdown
exit "$status"
