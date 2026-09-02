#!/bin/sh
set -eu
SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SLIM_SCRIPT_DIR/local-service-lib.sh"
if is_backend_running; then slim_health="异常"; if curl -fsS "$API_URL/health" >/dev/null 2>&1; then slim_health="正常"; fi; echo "本地后端：运行中（PID $(recorded_pid)）"; echo "API：$API_URL"; echo "健康检查：$slim_health"; echo "日志：$LOG_FILE"; exit 0; fi
remove_stale_pid; echo "本地后端：未运行"; echo "启动命令：$PROJECT_ROOT/scripts/start-local.sh"
