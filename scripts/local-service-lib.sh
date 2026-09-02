#!/bin/sh

SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
PROJECT_ROOT=${LOCAL_PROJECT_ROOT:-$(CDPATH= cd -- "$SLIM_SCRIPT_DIR/.." && pwd)}
BACKEND_DIR="$PROJECT_ROOT/backend"
RUNTIME_DIR=${LOCAL_RUNTIME_DIR:-$PROJECT_ROOT/.local}
UVICORN_BIN=${LOCAL_UVICORN_BIN:-$BACKEND_DIR/.venv/bin/uvicorn}
ALEMBIC_BIN=${LOCAL_ALEMBIC_BIN:-$BACKEND_DIR/.venv/bin/alembic}
PS_BIN=${LOCAL_PS_BIN:-ps}
LSOF_BIN=${LOCAL_LSOF_BIN:-lsof}
PID_FILE="$RUNTIME_DIR/backend.pid"
LOG_FILE="$RUNTIME_DIR/backend.log"
LOCAL_PORT=${LOCAL_PORT:-8000}
API_URL=${LOCAL_API_URL:-http://127.0.0.1:$LOCAL_PORT}

port_in_use() { "$LSOF_BIN" -nP -iTCP:"$LOCAL_PORT" -sTCP:LISTEN >/dev/null 2>&1; }
recorded_pid() {
  test -f "$PID_FILE" || return 1
  slim_pid=$(sed -n '1p' "$PID_FILE")
  case "$slim_pid" in ''|*[!0-9]*) return 1 ;; esac
  printf '%s\n' "$slim_pid"
}
is_backend_running() {
  slim_pid=$(recorded_pid) || return 1
  kill -0 "$slim_pid" 2>/dev/null || return 1
  slim_command=$($PS_BIN -p "$slim_pid" -o command= 2>/dev/null) || return 1
  case "$slim_command" in *"$UVICORN_BIN"*"app.main:app"*) return 0 ;; *) return 1 ;; esac
}
remove_stale_pid() { if ! is_backend_running; then rm -f "$PID_FILE"; fi; }
show_log_tail() { if test -f "$LOG_FILE"; then echo "最近日志："; tail -n 30 "$LOG_FILE"; fi; }
