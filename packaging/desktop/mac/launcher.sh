#!/usr/bin/env bash
# C4REQBER macOS desktop launcher — reads ~/.c4reqber/config.toml and starts TUI v9.
set -euo pipefail

CONFIG="${HOME}/.c4reqber/config.toml"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_ROOT="$(cd "${APP_DIR}/../.." && pwd)"
TUI_BIN="${BUNDLE_ROOT}/Contents/Resources/c4tui-v9"

if [[ ! -f "${CONFIG}" ]]; then
  echo "First run — creating config..."
  "${BUNDLE_ROOT}/Contents/MacOS/blast" init
fi

# Export config.toml → env (blast tui does this too; belt-and-suspenders for raw binary launch)
if [[ -f "${CONFIG}" ]]; then
  export C4_API_URL="${C4_API_URL:-$(grep -E '^api_url' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export C4_API_EMAIL="${C4_API_EMAIL:-$(grep -E '^email' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export C4_API_PASSWORD="${C4_API_PASSWORD:-$(grep -E '^password' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
fi

if [[ ! -x "${TUI_BIN}" ]]; then
  echo "TUI binary missing at ${TUI_BIN}"
  exit 1
fi

exec "${TUI_BIN}" "$@"