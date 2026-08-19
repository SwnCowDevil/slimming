#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_ROOT"

test -f .gitignore
grep -q '^\.DS_Store$' .gitignore
grep -q '^superdesign/config.json$' .gitignore
grep -q '^backend/\.env$' .gitignore
grep -q '^miniprogram/private\.' .gitignore
grep -q '^\.local/$' .gitignore
! git ls-files --error-unmatch superdesign/config.json >/dev/null 2>&1

echo "security baseline: ok"
