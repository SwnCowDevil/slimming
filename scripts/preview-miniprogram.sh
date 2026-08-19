#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WECHAT_CLI=${WECHAT_CLI:-/Applications/wechatwebdevtools.app/Contents/MacOS/cli}
slim_mode=${1:---dry-run}
case "$slim_mode" in --dry-run) echo "DRY RUN — 将构建 npm 并生成预览二维码：$PROJECT_ROOT/miniprogram"; exit 0 ;; --execute) ;; *) echo "用法：$0 [--dry-run|--execute]" >&2; exit 2 ;; esac
test -x "$WECHAT_CLI" || { echo "找不到微信开发者工具 CLI。" >&2; exit 1; }
"$WECHAT_CLI" build-npm --project "$PROJECT_ROOT/miniprogram"
"$WECHAT_CLI" preview --project "$PROJECT_ROOT/miniprogram"
