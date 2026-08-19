#!/bin/sh
set -eu

fail() { echo "FAIL: $*" >&2; exit 1; }
assert_contains() { case "$1" in *"$2"*) : ;; *) fail "expected output to contain: $2" ;; esac; }
assert_fails() { if "$@" >/dev/null 2>&1; then fail "expected command to fail: $*"; fi; }
