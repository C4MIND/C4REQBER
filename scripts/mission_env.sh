#!/usr/bin/env bash
# Mission recording / smoke-test env — free APIs + knowledge from .env.dontredact
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load_kilo_env.sh"

# Knowledge SSOT (already in dontredact, loaded last by load_kilo_env)
export C4REQBER_CONFIG="${C4REQBER_CONFIG:-$HOME/.c4reqber}"
mkdir -p "$C4REQBER_CONFIG"
cp -f "$ROOT/config/mission_free_models.json" "$C4REQBER_CONFIG/models.json"

# LM Studio: never use docker host URL on bare Mac
export LM_STUDIO_URL="${LM_STUDIO_URL_LOCAL:-http://127.0.0.1:1234}"
export LM_STUDIO_MODEL="${LM_STUDIO_MODEL:-qwen2.5-14b-instruct}"

# NVIDIA: dontredact key is 403; KILO keys work
export NVIDIA_API_KEY="${NVIDIA_API_KEY_KILO:-${NVIDIA_API_KEY_1:-${NVIDIA_API_KEY:-}}}"

# Groq: prefer KILO pool key if set
export GROQ_API_KEY="${GROQ_API_KEY_KILO:-${GROQ_API_KEY:-}}"

# Phase / mode models (OpenCode Zen free tier)
export C4_LLM_MODEL="${C4_LLM_MODEL:-deepseek-v4-flash-free}"
export DISSERTATION_MODEL="${DISSERTATION_MODEL:-nemotron-3-ultra-free}"
export C4_PHASE_A_MODEL="${C4_PHASE_A_MODEL:-deepseek-v4-flash-free}"
export C4_PHASE_B_MODEL="${C4_PHASE_B_MODEL:-north-mini-code-free}"
export C4_PHASE_C_MODEL="${C4_PHASE_C_MODEL:-nemotron-3-ultra-free}"
export C4_PHASE_D_MODEL="${C4_PHASE_D_MODEL:-big-pickle}"
export C4_PHASE_F_MODEL="${C4_PHASE_F_MODEL:-nemotron-3-ultra-free}"
export C4_PHASE_G_MODEL="${C4_PHASE_G_MODEL:-mimo-v2.5-free}"

export C4_LANG=en
export C4_DREAM_IDLE=0
export C4_LOCAL_LLM_FIRST=0
export MLX_SERVER_ENABLED=0
export C4_API_URL="${C4_API_URL:-http://127.0.0.1:8000}"
export PYTHONPATH="${PYTHONPATH:-$ROOT/src}"
