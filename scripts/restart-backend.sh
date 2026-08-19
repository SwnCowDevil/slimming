#!/bin/sh
set -eu
SLIM_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
"$SLIM_SCRIPT_DIR/stop-local.sh"
"$SLIM_SCRIPT_DIR/start-local.sh"
