#!/bin/sh
set -eu
SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SLIM_SCRIPT_DIR/local-service-lib.sh"
if ! is_backend_running; then remove_stale_pid; echo "本地后端未运行。"; exit 0; fi
slim_pid=$(recorded_pid); echo "正在停止本地后端（PID ${slim_pid}）..."; kill "$slim_pid"
slim_attempt=0
while kill -0 "$slim_pid" 2>/dev/null && test "$slim_attempt" -lt 20; do slim_attempt=$((slim_attempt + 1)); sleep 0.5; done
if kill -0 "$slim_pid" 2>/dev/null; then echo "进程未在 10 秒内退出，请检查：$LOG_FILE" >&2; exit 1; fi
rm -f "$PID_FILE"; echo "本地后端已停止。"
