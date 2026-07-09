#!/usr/bin/env bash
# CI Go deps — works on Docker Alpine and macOS shell runners.
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH:-}"

if command -v apk >/dev/null 2>&1; then
  apk add --no-cache git
fi

cd src/tui/v9
go mod download
