#!/usr/bin/env bash
# CI Python deps — works on Docker (Debian/Alpine) and macOS shell runners.
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH:-}"

install_requirements() {
  local req_file="$1"
  pip install -r "$req_file" --prefer-binary
}

if command -v apt-get >/dev/null 2>&1; then
  apt-get update && apt-get install -y curl git
  pip install --upgrade pip
  install_requirements requirements.txt
elif command -v apk >/dev/null 2>&1; then
  apk add --no-cache curl git
  pip install --upgrade pip
  install_requirements requirements.txt
else
  # macOS Homebrew Python (PEP 668) — venv with system packages for prebuilt wheels.
  VENV_DIR="${CI_PROJECT_DIR:-.}/.ci-venv"
  python3 -m venv --system-site-packages "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip
  # Optional sim/ML packages often fail to compile on shell runners (kiwisolver, etc.).
  grep -Ev '^(matplotlib|newton-physics|pymc|arviz|numba|sentence-transformers|gensim|dowhy)' requirements.txt \
    | grep -Ev '^\s*#' | grep -v '^[[:space:]]*$' > /tmp/requirements-ci.filtered.txt
  install_requirements /tmp/requirements-ci.filtered.txt
fi

pip install pytest pytest-asyncio pytest-timeout ruff mypy
