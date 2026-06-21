#!/usr/bin/env bash
# Generate k8s/secrets.yaml from secrets.example.yaml with safe random values.
# Usage: ./scripts/k8s-init-secrets.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="$ROOT/k8s/secrets.example.yaml"
TARGET="$ROOT/k8s/secrets.yaml"
ENV_FILE="$ROOT/.env"

if [[ -f "$TARGET" ]]; then
  echo "k8s/secrets.yaml already exists — remove it first to regenerate." >&2
  exit 1
fi

DB_PASSWORD="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
JWT_SECRET="$(openssl rand -base64 48 | tr -d '/+=' | head -c 48)"
CSRF_SECRET="$(openssl rand -base64 48 | tr -d '/+=' | head -c 48)"
OPENROUTER_KEY=""

if [[ -f "$ENV_FILE" ]]; then
  OPENROUTER_KEY="$(grep -E '^OPENROUTER_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"' || true)"
fi

cp "$EXAMPLE" "$TARGET"

# macOS + GNU sed compatibility
sed_inplace() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

sed_inplace "s/CHANGE_ME_STRONG_PASSWORD/$DB_PASSWORD/g" "$TARGET"
sed_inplace "s/CHANGE_ME_MIN_32_CHARS_JWT_SECRET_VALUE/$JWT_SECRET/g" "$TARGET"
sed_inplace "s/CHANGE_ME_MIN_32_CHARS_CSRF_SECRET_VALUE/$CSRF_SECRET/g" "$TARGET"

if [[ -n "$OPENROUTER_KEY" ]]; then
  sed_inplace "s|\"sk-or-v1-\\.\\.\\.\"|\"$OPENROUTER_KEY\"|g" "$TARGET"
fi

echo "Created $TARGET"
echo "  DB_PASSWORD, JWT_SECRET, CSRF_SECRET — generated"
if [[ -n "$OPENROUTER_KEY" ]]; then
  echo "  OPENROUTER_API_KEY — copied from .env"
else
  echo "  OPENROUTER_API_KEY — still placeholder (set in .env and re-run, or edit manually)"
fi
echo "Apply with: ./k8s/deploy.sh"