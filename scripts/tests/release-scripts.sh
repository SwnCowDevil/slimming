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
assert_contains "$deploy_plan" "服务器持久化 Python 3.12 运行时"
case "$deploy_plan" in
  *"Docker Compose"*) fail "dry-run must not claim Docker Compose is required" ;;
esac
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
if test "${0##*/}" = "scp"; then
  for argument in "$@"; do
    case "$argument" in
      *.tar.gz) if test -f "$argument"; then tar -tzf "$argument" >"$DEPLOY_ARCHIVE_LIST"; fi ;;
    esac
  done
fi
EOF
chmod +x "$runtime/bin/capture-command"
ln -s capture-command "$runtime/bin/rsync"
ln -s capture-command "$runtime/bin/scp"
ln -s capture-command "$runtime/bin/ssh"
touch "$runtime/deploy-key"
: >"$runtime/archive-list"
DEPLOY_CALLS="$runtime/calls" DEPLOY_ARCHIVE_LIST="$runtime/archive-list" PATH="$runtime/bin:$PATH" \
  DEPLOY_HOST=server.example DEPLOY_USER=deploy DEPLOY_DIR=/opt/slimming \
  DEPLOY_SSH_KEY="$runtime/deploy-key" \
  "$PROJECT_ROOT/scripts/deploy-backend.sh" --execute
deploy_calls=$(cat "$runtime/calls")
archive_list=$(cat "$runtime/archive-list")
tab=$(printf '\t')
assert_contains "$deploy_calls" "-i${tab}$runtime/deploy-key"
assert_contains "$deploy_calls" "/etc/slimming/slimming-api.env"
assert_contains "$deploy_calls" "127.0.0.1:8001"
assert_contains "$deploy_calls" "docker build"
assert_contains "$deploy_calls" "docker run"
assert_contains "$deploy_calls" "scp"
assert_contains "$deploy_calls" "/opt/slimming/.runtime/python3.12/bin/python3.12"
assert_contains "$deploy_calls" "find '/opt/slimming/backend' '/opt/slimming/deploy' -name '._*' -type f -delete"
case "$deploy_calls" in
  *"docker compose"*) fail "production deploy must not require Docker Compose" ;;
  *"rsync"*) fail "production deploy must not require rsync" ;;
esac
if printf '%s\n' "$archive_list" | grep -Eq '^backend/\.env$|^backend/data/'; then
  fail "release archive contains local secrets or data"
fi
if printf '%s\n' "$archive_list" | grep -Eq '(^|/)\._'; then
  fail "release archive contains macOS AppleDouble metadata"
fi
if ! printf '%s\n' "$archive_list" | grep -qx '\.dockerignore'; then
  fail "release archive must install .dockerignore on the build host"
fi

dockerfile=$(cat "$PROJECT_ROOT/deploy/Dockerfile.backend")
assert_contains "$dockerfile" "registry.cn-hangzhou.aliyuncs.com/alinux/alinux3:latest"
assert_contains "$dockerfile" "COPY .runtime/python3.12 /opt/python3.12"
assert_contains "$dockerfile" "https://mirrors.aliyun.com/pypi/simple/"
case "$dockerfile" in
  *"FROM python:"*) fail "backend image must not require Docker Hub's Python base image" ;;
esac

for script in build-backend-image deploy-backend open-wechat-devtools preview-miniprogram upload-miniprogram; do
  sh -n "$PROJECT_ROOT/scripts/$script.sh"
done
echo "release script tests passed"
