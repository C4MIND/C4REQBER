#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# Load credentials from .env if present
if [ -f "$DIR/.env" ]; then
  export C4_API_KEY="$(grep '^API_KEYS=' "$DIR/.env" | cut -d= -f2- | head -1)"
  export C4_DEV_BYPASS="$(grep '^DEV_MODE_BYPASS_TOKEN=' "$DIR/.env" | cut -d= -f2- | head -1)"
fi

mkdir -p "$DIR/bin"
cd "$DIR/src/tui/v8"
go build -o "$DIR/bin/c4tui-v8" .
"$DIR/bin/c4tui-v8" "$@"
