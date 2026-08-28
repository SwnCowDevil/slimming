#!/bin/sh
set -eu
SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SLIM_SCRIPT_DIR/local-service-lib.sh"
slim_mode=${1:---dry-run}
case "$slim_mode" in --dry-run|--execute) ;; *) echo "用法：$0 [--dry-run|--execute]" >&2; exit 2 ;; esac
slim_dataset="$BACKEND_DIR/data/imports/platform-recipes-v1.json"
slim_admin_key=${SLIMMING_ADMIN_IMPORT_KEY:-}
if test -z "$slim_admin_key" && test -f "$BACKEND_DIR/.env"; then slim_admin_key=$(sed -n 's/^SLIMMING_ADMIN_IMPORT_KEY=//p' "$BACKEND_DIR/.env" | tail -n 1); fi
test -n "$slim_admin_key" || { echo "缺少 SLIMMING_ADMIN_IMPORT_KEY。" >&2; exit 1; }
slim_auth=$(curl -fsS -X POST "$API_URL/api/v1/auth/dev" -H 'content-type: application/json' -d '{"user_id":"local-recipe-operator"}')
slim_token=$("$BACKEND_DIR/.venv/bin/python" -c 'import json,sys; print(json.loads(sys.argv[1])["access_token"])' "$slim_auth")
slim_dry_run=true; if test "$slim_mode" = "--execute"; then slim_dry_run=false; fi
slim_payload=$("$BACKEND_DIR/.venv/bin/python" -c 'import json,sys; print(json.dumps({"path":sys.argv[1],"version":"platform-recipes-v1","dry_run":sys.argv[2]=="true"}))' "$slim_dataset" "$slim_dry_run")
curl -fsS -X POST "$API_URL/api/v1/admin/recipes/import" -H "Authorization: Bearer $slim_token" -H "X-Admin-Import-Key: $slim_admin_key" -H 'content-type: application/json' -d "$slim_payload"
printf '\n'
