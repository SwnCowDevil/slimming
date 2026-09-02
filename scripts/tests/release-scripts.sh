#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SCRIPT_DIR/test-lib.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

deploy_plan=$("$PROJECT_ROOT/scripts/deploy-backend.sh" --dry-run)
assert_contains "$deploy_plan" "DRY RUN"
assert_contains "$deploy_plan" "迁移成功后再启动"
assert_contains "$deploy_plan" "https://slimming.sunks.cc"
assert_contains "$deploy_plan" "127.0.0.1:8001"
assert_contains "$("$PROJECT_ROOT/scripts/upload-miniprogram.sh" --help)" "WECHAT_DEVTOOLS_CLI_TOKEN"
assert_fails "$PROJECT_ROOT/scripts/upload-miniprogram.sh" --version 0.1.0 --description test
assert_fails "$PROJECT_ROOT/scripts/deploy-backend.sh" --execute

runtime=$(mktemp -d)
trap 'rm -rf "$runtime"' EXIT INT TERM
mkdir -p "$runtime/bin"
cat >"$runtime/bin/capture-command" <<'EOF'
#!/bin/sh
printf '%s' "${0##*/}" >>"$DEPLOY_CALLS"
for argument in "$@"; do printf '\t%s' "$argument" >>"$DEPLOY_CALLS"; done
printf '\n' >>"$DEPLOY_CALLS"
EOF
chmod +x "$runtime/bin/capture-command"
ln -s capture-command "$runtime/bin/rsync"
ln -s capture-command "$runtime/bin/ssh"
DEPLOY_CALLS="$runtime/calls" PATH="$runtime/bin:$PATH" \
  DEPLOY_HOST=server.example DEPLOY_USER=deploy DEPLOY_DIR=/opt/slimming \
  "$PROJECT_ROOT/scripts/deploy-backend.sh" --execute
deploy_calls=$(cat "$runtime/calls")
tab=$(printf '\t')
assert_contains "$deploy_calls" "--exclude${tab}.env"
assert_contains "$deploy_calls" "/etc/slimming/slimming-api.env"
assert_contains "$deploy_calls" "127.0.0.1:8001"

for script in build-backend-image deploy-backend open-wechat-devtools preview-miniprogram upload-miniprogram; do
  sh -n "$PROJECT_ROOT/scripts/$script.sh"
done
echo "release script tests passed"
