#!/bin/sh
# CI Go deps — POSIX sh (Alpine golang images have no bash).
set -eu

export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH:-}"

if command -v apk >/dev/null 2>&1; then
  apk add --no-cache git
fi

cd src/tui/v9
go mod download
