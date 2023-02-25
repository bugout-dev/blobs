#!/usr/bin/env sh

# Sets up blobs3 API server
# Expects access to Python environment with the requirements
# for this project installed.
set -e

BLOBS3_HOST="${BLOBS3_HOST:-127.0.0.1}"
BLOBS3_PORT="${BLOBS3_PORT:-8108}"
BLOBS3_APP_DIR="${BLOBS3_APP_DIR:-$PWD}"
BLOBS3_ASGI_APP="${BLOBS3_ASGI_APP:-blobs3.api:app}"
BLOBS3_UVICORN_WORKERS="${BLOBS3_UVICORN_WORKERS:-1}"

uvicorn --reload \
  --port "$BLOBS3_PORT" \
  --host "$BLOBS3_HOST" \
  --app-dir "$BLOBS3_APP_DIR" \
  --workers "$BLOBS3_UVICORN_WORKERS" \
  "$BLOBS3_ASGI_APP"
