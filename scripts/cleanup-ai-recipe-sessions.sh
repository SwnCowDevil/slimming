#!/bin/sh
set -eu
SLIM_CLEANUP_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$SLIM_CLEANUP_DIR/backend"
exec .venv/bin/python -m app.ai_recipes.cleanup
