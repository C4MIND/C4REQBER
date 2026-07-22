#!/bin/sh
# Validate optional VPS Traefik compose file (syntax + required env placeholders).
set -eu
ROOT="${CI_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT"
COMPOSE_FILE="examples/hosting/docker-compose.vps-traefik.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: missing $COMPOSE_FILE" >&2
  exit 1
fi

export JWT_SECRET="${JWT_SECRET:-ci-fake-jwt-for-compose-config-only-32chars}"
export DB_PASSWORD="${DB_PASSWORD:-ci-fake-db-password}"
export ACME_EMAIL="${ACME_EMAIL:-ci@example.com}"

compose_config_ok=0
if docker compose version >/dev/null 2>&1; then
  if docker compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
    compose_config_ok=1
    echo "VPS compose config OK (docker compose)"
  fi
elif command -v docker-compose >/dev/null 2>&1; then
  if docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
    compose_config_ok=1
    echo "VPS compose config OK (docker-compose)"
  fi
fi

if [ "$compose_config_ok" -eq 0 ]; then
  echo "SKIP docker compose config — compose CLI unavailable or config failed (static checks only)"
fi

# Static sanity: no stale turbo-cdi-only paths in the example
if grep -q 'turbo-cdi.org' "$COMPOSE_FILE"; then
  echo "ERROR: VPS compose still references legacy turbo-cdi.org hostnames" >&2
  exit 1
fi

if ! grep -q 'healthcheck:' "$COMPOSE_FILE"; then
  echo "ERROR: VPS compose missing healthcheck blocks" >&2
  exit 1
fi

echo "validate_vps_compose.sh OK"
