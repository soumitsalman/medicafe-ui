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

trap 'shutdown; exit 143' TERM
trap 'shutdown; exit 130' INT

cd /app/api
fastapi run main.py --host "$API_HOST" --port "$API_PORT" &
api_pid=$!

node /app/ui/.output/server/index.mjs &
ui_pid=$!

wait -n "$api_pid" "$ui_pid"
status=$?
shutdown
exit "$status"
