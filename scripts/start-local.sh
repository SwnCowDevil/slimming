#!/bin/sh
set -eu
SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SLIM_SCRIPT_DIR/local-service-lib.sh"

mkdir -p "$RUNTIME_DIR"
if is_backend_running; then echo "本地后端已经运行：${API_URL}（PID $(recorded_pid)）"; exit 0; fi
remove_stale_pid
if port_in_use; then echo "无法启动：端口 $LOCAL_PORT 已被其他进程占用。可设置 LOCAL_PORT 使用其他端口。" >&2; exit 1; fi
if test ! -x "$UVICORN_BIN" || test ! -x "$ALEMBIC_BIN"; then echo "缺少 backend/.venv，请先执行：python3.12 -m venv backend/.venv && backend/.venv/bin/pip install -e 'backend[dev]'" >&2; exit 1; fi
if test ! -f "$BACKEND_DIR/.env"; then echo "缺少 backend/.env，请复制 backend/.env.example 并填写微信配置。" >&2; exit 1; fi

echo "正在升级本地数据库..."
(cd "$BACKEND_DIR" && "$ALEMBIC_BIN" upgrade head)
echo "正在启动 FastAPI..."
SLIM_ORIGINAL_DIR=$(pwd)
cd "$BACKEND_DIR"
SLIMMING_ENABLE_DEV_AUTH=true nohup "$UVICORN_BIN" app.main:app --host 127.0.0.1 --port "$LOCAL_PORT" --workers 1 >"$LOG_FILE" 2>&1 &
slim_server_pid=$!
cd "$SLIM_ORIGINAL_DIR"
printf '%s\n' "$slim_server_pid" >"$PID_FILE"

slim_attempt=0
while test "$slim_attempt" -lt 30; do
  if is_backend_running && curl -fsS "$API_URL/health" >/dev/null 2>&1; then echo "本地后端启动成功：$API_URL"; echo "日志：$LOG_FILE"; exit 0; fi
  if test "$slim_attempt" -ge 4 && ! is_backend_running; then break; fi
  slim_attempt=$((slim_attempt + 1)); sleep 0.5
done
echo "本地后端启动失败。" >&2
if is_backend_running; then kill "$(recorded_pid)" 2>/dev/null || true; fi
rm -f "$PID_FILE"; show_log_tail; exit 1
