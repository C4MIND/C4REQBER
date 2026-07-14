#!/usr/bin/env bash
# Humanity-saving discovery mission — free-tier models only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Keys live in ~/.kilo — repo .env.dontredact is optional override only
# shellcheck disable=SC1091
source "$(dirname "$0")/load_kilo_env.sh"

export PYTHONPATH=src
export PREFERRED_MODELS="${PREFERRED_MODELS:-ollama,opencode,groq,openrouter,nvidia,xai}"
export DISSERTATION_MODEL="${DISSERTATION_MODEL:-deepseek-v4-flash-free}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct}"
export MLX_SERVER_ENABLED="${MLX_SERVER_ENABLED:-0}"
export MLX_SERVER_URL="${MLX_SERVER_URL:-http://localhost:8001}"
export LM_STUDIO_URL="${LM_STUDIO_URL:-http://localhost:1234}"

# Bootstrap LM Studio headless server (no desktop GUI)
LMS="$HOME/.lmstudio/bin/lms"
if [[ -x "$LMS" ]]; then
  if ! curl -sf "${LM_STUDIO_URL}/v1/models" >/dev/null 2>&1; then
    "$LMS" server start >/dev/null 2>&1 || true
    sleep 2
  fi
  # Auto-load first available model if none loaded
  if ! "$LMS" ps 2>/dev/null | grep -q "Loaded"; then
    FIRST_MODEL=$("$LMS" ls 2>/dev/null | awk 'NF && $1 !~ /^(You|LLM|─)/ {print $1; exit}')
    if [[ -n "${FIRST_MODEL:-}" ]]; then
      "$LMS" load "$FIRST_MODEL" -y >/dev/null 2>&1 || true
    fi
  fi
fi

# Install free-tier model routing (no Claude/Kimi/Minimax)
mkdir -p "$HOME/.c4reqber"
cp -f config/mission_free_models.json "$HOME/.c4reqber/models.json" 2>/dev/null || true

MODE="${1:-flash}"
shift || true

case "$MODE" in
  flash) python3 -m src.cli.blast_app flash "$@" ;;
  solve) python3 -m src.cli.blast_app solve "$@" ;;
  turbo) python3 -m src.cli.blast_app turbo "$@" ;;
  *) echo "Usage: $0 {flash|solve|turbo} <query> [--output path.md]" >&2; exit 1 ;;
esac
