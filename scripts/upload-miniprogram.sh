#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WECHAT_CLI=${WECHAT_CLI:-/Applications/wechatwebdevtools.app/Contents/MacOS/cli}
slim_version=""; slim_description=""; slim_execute=false
usage(){ echo "用法：$0 --version VERSION --description TEXT [--execute]"; echo "环境：WECHAT_APP_ID、WECHAT_DEVTOOLS_CLI_TOKEN（可选；也可使用已登录且开启服务端口的开发者工具）"; echo "默认仅 dry-run；只有 --execute 才上传。"; }
while test "$#" -gt 0; do case "$1" in --version) slim_version=${2:-}; shift 2 ;; --description) slim_description=${2:-}; shift 2 ;; --execute) slim_execute=true; shift ;; --help|-h) usage; exit 0 ;; *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;; esac; done
test -n "$slim_version" && test -n "$slim_description" || { usage >&2; exit 2; }
test -n "${WECHAT_APP_ID:-}" || { echo "缺少 WECHAT_APP_ID。" >&2; exit 1; }
test -x "$WECHAT_CLI" || { echo "找不到微信开发者工具 CLI。" >&2; exit 1; }
slim_project_config="$PROJECT_ROOT/miniprogram/project.config.json"
test -f "$slim_project_config" || { echo "缺少 miniprogram/project.config.json，请在微信开发者工具中导入项目并填写 AppID。" >&2; exit 1; }
slim_config_app_id=$(node -e 'const p=require(process.argv[1]); process.stdout.write(p.appid||"")' "$slim_project_config")
test "$slim_config_app_id" != "touristappid" || { echo "project.config.json 仍是 touristappid，禁止上传。" >&2; exit 1; }
test "$slim_config_app_id" = "$WECHAT_APP_ID" || { echo "WECHAT_APP_ID 与 project.config.json 的 appid 不一致，已停止上传。" >&2; exit 1; }
if test "$slim_execute" != true; then echo "DRY RUN — 将上传 ${WECHAT_APP_ID} 版本 ${slim_version}：${slim_description}"; exit 0; fi
"$WECHAT_CLI" build-npm --project "$PROJECT_ROOT/miniprogram"
"$WECHAT_CLI" upload --project "$PROJECT_ROOT/miniprogram" --version "$slim_version" --desc "$slim_description"
