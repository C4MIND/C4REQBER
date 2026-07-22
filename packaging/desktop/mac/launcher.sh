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

# Export config.toml → env for polished desktop (full settings via central ~/.c4reqber + keys)
if [[ -f "${CONFIG}" ]]; then
  export C4_API_URL="${C4_API_URL:-$(grep -E '^api_url' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export C4_LANG="${C4_LANG:-$(grep -E '^language' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export C4_API_EMAIL="${C4_API_EMAIL:-$(grep -E '^email' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export C4_API_PASSWORD="${C4_API_PASSWORD:-$(grep -E '^password' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-$(grep -E '^openrouter_api_key' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-$(grep -E '^deepseek_api_key' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export BRAVE_API_KEY="${BRAVE_API_KEY:-$(grep -E '^brave_api_key' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export TAVILY_API_KEY="${TAVILY_API_KEY:-$(grep -E '^tavily_api_key' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export EXA_API_KEY="${EXA_API_KEY:-$(grep -E '^exa_api_key' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export XAI_API_KEY="${XAI_API_KEY:-$(grep -E '^xai_api_key' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
  export LEAN4_PATH="${LEAN4_PATH:-$(grep -E '^lean4_path' "${CONFIG}" 2>/dev/null | head -1 | sed 's/.*= *"\(.*\)".*/\1/')}"
fi

# secrets.env (Setup Hub) — Tavily and other keys may live here only
SECRETS="${HOME}/.c4reqber/secrets.env"
if [[ -f "${SECRETS}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${SECRETS}" 2>/dev/null || true
  set +a
fi

if [[ ! -x "${TUI_BIN}" ]]; then
  echo "TUI binary missing at ${TUI_BIN}"
  exit 1
fi

# Desktop splash header (port of terminal splash text) — Go TUI will show full animated splash
echo "C4REQBER DESKTOP  ·  Creative & Destructive Insights · At Your Fingertips"
echo "Discover. Invent. Shift paradigms."
echo "GitLab · c4reqber · Z₃³"
echo

exec "${TUI_BIN}" "$@"
