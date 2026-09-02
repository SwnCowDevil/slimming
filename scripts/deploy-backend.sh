#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
slim_mode=--dry-run
if test "${1:-}" = "--execute"; then slim_mode=--execute; elif test "${1:-}" = "--dry-run" || test "$#" -eq 0; then :; else echo "用法：$0 [--dry-run|--execute]" >&2; exit 2; fi
slim_host=${DEPLOY_HOST:-<DEPLOY_HOST>}; slim_user=${DEPLOY_USER:-<DEPLOY_USER>}; slim_dir=${DEPLOY_DIR:-/opt/slimming}
slim_public_url=${DEPLOY_PUBLIC_URL:-https://slimming.sunks.cc}
slim_bind_port=${DEPLOY_BIND_PORT:-8001}
slim_env_file=${DEPLOY_ENV_FILE:-/etc/slimming/slimming-api.env}
if test "$slim_mode" = "--dry-run"; then
  echo "DRY RUN — 不会连接服务器"
  echo "目标：$slim_user@$slim_host:$slim_dir"
  echo "公网：$slim_public_url → 127.0.0.1:$slim_bind_port"
  echo "生产环境文件：$slim_env_file"
  echo "将排除本机 .env 与数据目录，同步 backend 与 deploy 配置，由 Docker Compose 构建镜像，迁移成功后再启动服务。"
  exit 0
fi
test -n "${DEPLOY_HOST:-}" && test -n "${DEPLOY_USER:-}" && test -n "${DEPLOY_DIR:-}" || { echo "执行部署前必须设置 DEPLOY_HOST、DEPLOY_USER、DEPLOY_DIR。" >&2; exit 1; }
case "$DEPLOY_HOST$DEPLOY_USER" in *[!A-Za-z0-9._@-]*) echo "部署主机或用户包含非法字符。" >&2; exit 1 ;; esac
case "$DEPLOY_DIR" in /*) ;; *) echo "DEPLOY_DIR 必须是绝对路径。" >&2; exit 1 ;; esac
case "$slim_env_file" in /*) ;; *) echo "DEPLOY_ENV_FILE 必须是绝对路径。" >&2; exit 1 ;; esac
case "$slim_bind_port" in ''|*[!0-9]*) echo "DEPLOY_BIND_PORT 必须是数字端口。" >&2; exit 1 ;; esac
test "$slim_bind_port" -ge 1 && test "$slim_bind_port" -le 65535 || { echo "DEPLOY_BIND_PORT 超出有效范围。" >&2; exit 1; }

ssh "$DEPLOY_USER@$DEPLOY_HOST" "set -eu; test -f '$slim_env_file' || { echo '缺少生产环境文件：$slim_env_file' >&2; exit 1; }; command -v docker >/dev/null; command -v curl >/dev/null; mkdir -p '$slim_dir/backend/data' '$slim_dir/backups' '$slim_dir/deploy'; chown -R 10001:10001 '$slim_dir/backend/data'"
rsync -az --delete --exclude '.venv' --exclude '.env' --exclude 'data' "$PROJECT_ROOT/backend/" "$DEPLOY_USER@$DEPLOY_HOST:$slim_dir/backend/"
rsync -az --exclude 'backend.env' "$PROJECT_ROOT/deploy/" "$DEPLOY_USER@$DEPLOY_HOST:$slim_dir/deploy/"
ssh "$DEPLOY_USER@$DEPLOY_HOST" "set -eu; cd '$slim_dir'; export DEPLOY_ENV_FILE='$slim_env_file' DEPLOY_DATA_DIR='$slim_dir/backend/data' DEPLOY_BIND_PORT='$slim_bind_port'; docker compose -f deploy/docker-compose.backend.yml build slimming-api; if test -f '$slim_dir/backend/data/slimming.db'; then command -v sqlite3 >/dev/null; timestamp=\$(date +%Y%m%d-%H%M%S); sqlite3 '$slim_dir/backend/data/slimming.db' \".backup '$slim_dir/backups/slimming-\$timestamp.db'\"; fi; docker compose -f deploy/docker-compose.backend.yml run --rm slimming-api alembic upgrade head; docker compose -f deploy/docker-compose.backend.yml up -d --force-recreate slimming-api; attempt=0; until curl -fsS 'http://127.0.0.1:$slim_bind_port/health'; do attempt=\$((attempt + 1)); test \$attempt -lt 30 || exit 1; sleep 1; done"
