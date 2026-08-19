#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SCRIPT_DIR/test-lib.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

assert_contains "$("$PROJECT_ROOT/scripts/deploy-backend.sh" --dry-run)" "DRY RUN"
assert_contains "$("$PROJECT_ROOT/scripts/upload-miniprogram.sh" --help)" "WECHAT_DEVTOOLS_CLI_TOKEN"
assert_fails "$PROJECT_ROOT/scripts/upload-miniprogram.sh" --version 0.1.0 --description test
assert_fails "$PROJECT_ROOT/scripts/deploy-backend.sh" --execute

for script in build-backend-image deploy-backend open-wechat-devtools preview-miniprogram upload-miniprogram; do
  sh -n "$PROJECT_ROOT/scripts/$script.sh"
done
echo "release script tests passed"
