#!/bin/sh
set -eu
SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SLIM_SCRIPT_DIR/local-service-lib.sh"
if test "$#" -lt 2 || test "$#" -gt 3; then echo "用法：$0 DATASET_JSON VERSION [--execute]" >&2; exit 2; fi
slim_dataset=$1; slim_version=$2; slim_mode=${3:---dry-run}
test -f "$slim_dataset" || { echo "数据文件不存在：$slim_dataset" >&2; exit 1; }
case "$slim_mode" in --dry-run|--execute) ;; *) echo "模式必须是 --dry-run 或 --execute" >&2; exit 2 ;; esac
case "$slim_version" in *[!A-Za-z0-9._-]*) echo "版本号只能包含字母、数字、点、下划线和连字符。" >&2; exit 1 ;; esac
slim_import_root=${SLIMMING_TKA_IMPORT_ROOT:-$BACKEND_DIR/data/imports}
case "$slim_import_root" in /*) ;; *) slim_import_root="$BACKEND_DIR/${slim_import_root#./}" ;; esac
mkdir -p "$slim_import_root"
slim_cleanup=false
if test "$slim_mode" = "--execute"; then slim_import_file="$slim_import_root/tka-$slim_version.json"; else slim_import_file=$(mktemp "$slim_import_root/tka-preview.XXXXXX.json"); slim_cleanup=true; fi
cleanup_import_preview(){ if test "$slim_cleanup" = true; then rm -f "$slim_import_file"; fi; }
trap cleanup_import_preview EXIT INT TERM
cp "$slim_dataset" "$slim_import_file"
slim_admin_key=${SLIMMING_ADMIN_IMPORT_KEY:-}
if test -z "$slim_admin_key" && test -f "$BACKEND_DIR/.env"; then slim_admin_key=$(sed -n 's/^SLIMMING_ADMIN_IMPORT_KEY=//p' "$BACKEND_DIR/.env" | tail -n 1); fi
test -n "$slim_admin_key" || { echo "缺少 SLIMMING_ADMIN_IMPORT_KEY。" >&2; exit 1; }
slim_auth=$(curl -fsS -X POST "$API_URL/api/v1/auth/dev" -H 'content-type: application/json' -d '{"user_id":"local-data-operator"}')
slim_token=$("$BACKEND_DIR/.venv/bin/python" -c 'import json,sys; print(json.loads(sys.argv[1])["access_token"])' "$slim_auth")
slim_dry_run=true; if test "$slim_mode" = "--execute"; then slim_dry_run=false; fi
slim_payload=$("$BACKEND_DIR/.venv/bin/python" -c 'import json,sys; print(json.dumps({"path":sys.argv[1],"version":sys.argv[2],"dry_run":sys.argv[3]=="true"}))' "$slim_import_file" "$slim_version" "$slim_dry_run")
curl -fsS -X POST "$API_URL/api/v1/admin/foods/import" -H "Authorization: Bearer $slim_token" -H "X-Admin-Import-Key: $slim_admin_key" -H 'content-type: application/json' -d "$slim_payload"
printf '\n'
