#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
slim_mode=--dry-run
if test "${1:-}" = "--execute"; then slim_mode=--execute; elif test "${1:-}" = "--dry-run" || test "$#" -eq 0; then :; else echo "用法：$0 [--dry-run|--execute]" >&2; exit 2; fi
slim_host=${DEPLOY_HOST:-<DEPLOY_HOST>}; slim_user=${DEPLOY_USER:-<DEPLOY_USER>}; slim_dir=${DEPLOY_DIR:-/opt/slimming}
if test "$slim_mode" = "--dry-run"; then echo "DRY RUN — 不会连接服务器"; echo "目标：$slim_user@$slim_host:$slim_dir"; echo "将同步 backend 与 deploy 配置，由 Docker Compose 构建镜像，迁移成功后再启动服务。"; exit 0; fi
test -n "${DEPLOY_HOST:-}" && test -n "${DEPLOY_USER:-}" && test -n "${DEPLOY_DIR:-}" || { echo "执行部署前必须设置 DEPLOY_HOST、DEPLOY_USER、DEPLOY_DIR。" >&2; exit 1; }
case "$DEPLOY_HOST$DEPLOY_USER" in *[!A-Za-z0-9._@-]*) echo "部署主机或用户包含非法字符。" >&2; exit 1 ;; esac
case "$DEPLOY_DIR" in /*) ;; *) echo "DEPLOY_DIR 必须是绝对路径。" >&2; exit 1 ;; esac
rsync -az --delete --exclude '.venv' --exclude 'data' "$PROJECT_ROOT/backend/" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_DIR/backend/"
rsync -az "$PROJECT_ROOT/deploy/" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_DIR/deploy/"
ssh "$DEPLOY_USER@$DEPLOY_HOST" "cd '$DEPLOY_DIR' && docker compose -f deploy/docker-compose.backend.yml build slimming-api && docker compose -f deploy/docker-compose.backend.yml run --rm slimming-api alembic upgrade head && docker compose -f deploy/docker-compose.backend.yml up -d slimming-api"
