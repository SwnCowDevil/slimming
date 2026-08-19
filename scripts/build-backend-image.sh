#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
docker build --file "$PROJECT_ROOT/deploy/Dockerfile.backend" --tag slimming-api:local "$PROJECT_ROOT"
