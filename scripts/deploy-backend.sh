#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
slim_mode=--dry-run
if test "${1:-}" = "--execute"; then slim_mode=--execute; elif test "${1:-}" = "--dry-run" || test "$#" -eq 0; then :; else echo "用法：$0 [--dry-run|--execute]" >&2; exit 2; fi
slim_host=${DEPLOY_HOST:-<DEPLOY_HOST>}; slim_user=${DEPLOY_USER:-<DEPLOY_USER>}; slim_dir=${DEPLOY_DIR:-/opt/slimming}
slim_public_url=${DEPLOY_PUBLIC_URL:-https://slimming.sunks.cc}
slim_bind_port=${DEPLOY_BIND_PORT:-8001}
slim_env_file=${DEPLOY_ENV_FILE:-/etc/slimming/slimming-api.env}
slim_ssh_key=${DEPLOY_SSH_KEY:-}
if test "$slim_mode" = "--dry-run"; then
  echo "DRY RUN — 不会连接服务器"
  echo "目标：$slim_user@$slim_host:$slim_dir"
  echo "公网：$slim_public_url → 127.0.0.1:$slim_bind_port"
  echo "生产环境文件：$slim_env_file"
  echo "将排除本机 .env 与数据目录，同步 backend 与 deploy 配置，使用服务器持久化 Python 3.12 运行时构建 Docker 镜像，迁移成功后再启动服务。"
  exit 0
fi
test -n "${DEPLOY_HOST:-}" && test -n "${DEPLOY_USER:-}" && test -n "${DEPLOY_DIR:-}" || { echo "执行部署前必须设置 DEPLOY_HOST、DEPLOY_USER、DEPLOY_DIR。" >&2; exit 1; }
case "$DEPLOY_HOST$DEPLOY_USER" in *[!A-Za-z0-9._@-]*) echo "部署主机或用户包含非法字符。" >&2; exit 1 ;; esac
case "$DEPLOY_DIR" in /*) ;; *) echo "DEPLOY_DIR 必须是绝对路径。" >&2; exit 1 ;; esac
case "$slim_env_file" in /*) ;; *) echo "DEPLOY_ENV_FILE 必须是绝对路径。" >&2; exit 1 ;; esac
case "$slim_bind_port" in ''|*[!0-9]*) echo "DEPLOY_BIND_PORT 必须是数字端口。" >&2; exit 1 ;; esac
test "$slim_bind_port" -ge 1 && test "$slim_bind_port" -le 65535 || { echo "DEPLOY_BIND_PORT 超出有效范围。" >&2; exit 1; }
if test -n "$slim_ssh_key"; then
  case "$slim_ssh_key" in /*) ;; *) slim_ssh_key="$PROJECT_ROOT/$slim_ssh_key" ;; esac
  test -f "$slim_ssh_key" || { echo "DEPLOY_SSH_KEY 指定的文件不存在。" >&2; exit 1; }
fi

deploy_ssh() {
  if test -n "$slim_ssh_key"; then ssh -i "$slim_ssh_key" "$@"; else ssh "$@"; fi
}

deploy_scp() {
  if test -n "$slim_ssh_key"; then scp -i "$slim_ssh_key" "$@"; else scp "$@"; fi
}

deploy_ssh "$DEPLOY_USER@$DEPLOY_HOST" "set -eu; test -f '$slim_env_file' || { echo '缺少生产环境文件：$slim_env_file' >&2; exit 1; }; test -x '$slim_dir/.runtime/python3.12/bin/python3.12' || { echo '缺少服务器持久化 Python 3.12 运行时：$slim_dir/.runtime/python3.12' >&2; exit 1; }; command -v docker >/dev/null; command -v curl >/dev/null; mkdir -p '$slim_dir/backend/data' '$slim_dir/backups' '$slim_dir/deploy'; chown -R 10001:10001 '$slim_dir/backend/data'"
slim_release_dir=$(mktemp -d)
trap 'rm -rf "$slim_release_dir"' EXIT INT TERM
slim_archive="$slim_release_dir/slimming-release.tar.gz"
slim_remote_archive="/tmp/slimming-release-$$.tar.gz"
COPYFILE_DISABLE=1 tar --no-xattrs -C "$PROJECT_ROOT" -czf "$slim_archive" \
  --exclude='backend/.env' \
  --exclude='backend/.venv' \
  --exclude='backend/data' \
  --exclude='backend/.pytest_cache' \
  --exclude='backend/**/__pycache__' \
  --exclude='deploy/backend.env' \
  .dockerignore backend deploy
deploy_scp "$slim_archive" "$DEPLOY_USER@$DEPLOY_HOST:$slim_remote_archive"
deploy_ssh "$DEPLOY_USER@$DEPLOY_HOST" "set -eu; tar -xzf '$slim_remote_archive' -C '$slim_dir'; rm -f '$slim_remote_archive'; find '$slim_dir/backend' '$slim_dir/deploy' -name '._*' -type f -delete"
deploy_ssh "$DEPLOY_USER@$DEPLOY_HOST" "set -eu; cd '$slim_dir'; docker build --file deploy/Dockerfile.backend --tag slimming-api:local .; if test -f '$slim_dir/backend/data/slimming.db'; then command -v sqlite3 >/dev/null; timestamp=\$(date +%Y%m%d-%H%M%S); sqlite3 '$slim_dir/backend/data/slimming.db' \".backup '$slim_dir/backups/slimming-\$timestamp.db'\"; fi; docker run --rm --env-file '$slim_env_file' -v '$slim_dir/backend/data:/app/data:rw' slimming-api:local alembic upgrade head; docker rm -f slimming-api >/dev/null 2>&1 || true; docker run -d --name slimming-api --env-file '$slim_env_file' --restart unless-stopped -p '127.0.0.1:$slim_bind_port:8000' -v '$slim_dir/backend/data:/app/data:rw' slimming-api:local >/dev/null; attempt=0; until curl -fsS 'http://127.0.0.1:$slim_bind_port/health'; do attempt=\$((attempt + 1)); test \$attempt -lt 30 || exit 1; sleep 1; done"
