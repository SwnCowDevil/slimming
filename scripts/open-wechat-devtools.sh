#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WECHAT_CLI=${WECHAT_CLI:-/Applications/wechatwebdevtools.app/Contents/MacOS/cli}
test -x "$WECHAT_CLI" || { echo "找不到微信开发者工具 CLI：$WECHAT_CLI" >&2; exit 1; }
"$WECHAT_CLI" open --project "$PROJECT_ROOT/miniprogram"
