#!/usr/bin/env bash
# Load AI keys from ~/.kilo (canonical vault). Never commit secrets to repo.
set -euo pipefail
KILO_HOME="${KILO_HOME:-$HOME/.kilo}"
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
if [[ -f "$KILO_HOME/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$KILO_HOME/.env"
  set +a
fi
if [[ -f "$KILO_HOME/secrets/api_keys_working.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$KILO_HOME/secrets/api_keys_working.env"
  set +a
fi
if [[ -f "$KILO_HOME/secrets/env_exports.sh" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$KILO_HOME/secrets/env_exports.sh"
  set +a
fi
# Repo-local overrides (optional, last wins)
if [[ -f "$REPO_ROOT/.env.dontredact" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env.dontredact"
  set +a
fi
