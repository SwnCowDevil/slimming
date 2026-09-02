#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SCRIPT_DIR/test-lib.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

for script in start-local stop-local status-local restart-backend import-tka-dataset; do
  test -x "$PROJECT_ROOT/scripts/$script.sh" || fail "missing executable scripts/$script.sh"
  sh -n "$PROJECT_ROOT/scripts/$script.sh"
done

runtime=$(mktemp -d)
trap 'rm -rf "$runtime"' EXIT INT TERM
output=$(LOCAL_RUNTIME_DIR="$runtime" "$PROJECT_ROOT/scripts/status-local.sh")
assert_contains "$output" "未运行"
echo "local service script tests passed"
