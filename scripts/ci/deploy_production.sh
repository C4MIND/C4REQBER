#!/usr/bin/env bash
# Production deploy for c4reqber API (Mac Colima / self-hosted host).
# Idempotent: skips pull/recreate when the running API already matches target image.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

REGISTRY_IMAGE="${CI_REGISTRY_IMAGE:-registry.gitlab.com/cognitive-functors/turbo-cdi}"
IMAGE_TAG="${API_IMAGE_TAG:-latest}"
IMAGE_REF="${REGISTRY_IMAGE}/api:${IMAGE_TAG}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/v1/health}"
MAX_HEALTH_ATTEMPTS="${MAX_HEALTH_ATTEMPTS:-30}"
HEALTH_SLEEP="${HEALTH_SLEEP:-5}"
DEPLOY_SERVICES="${DEPLOY_SERVICES:-postgres api}"

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose -f "${COMPOSE_FILE}")
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose -f "${COMPOSE_FILE}")
else
  die "Neither 'docker compose' nor 'docker-compose' is available"
fi

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

ensure_colima() {
  if ! docker info >/dev/null 2>&1; then
    if command -v colima >/dev/null 2>&1; then
      log "Starting Colima..."
      colima start >/dev/null 2>&1 || die "Colima failed to start"
    fi
  fi
  docker info >/dev/null 2>&1 || die "Docker daemon not reachable"
}

load_env() {
  if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
}

ensure_env_keys() {
  local changed=0
  if [[ -z "${JWT_SECRET:-}" ]]; then
    if grep -q '^JWT_SECRET=.\+' .env 2>/dev/null; then
      export JWT_SECRET="$(grep '^JWT_SECRET=' .env | head -1 | cut -d= -f2-)"
    else
      JWT_SECRET="$(openssl rand -hex 32)"
      echo "JWT_SECRET=${JWT_SECRET}" >> .env
      export JWT_SECRET
      changed=1
      log "Generated JWT_SECRET in .env"
    fi
  fi
  if [[ -z "${DB_PASSWORD:-}" ]]; then
    if grep -q '^DB_PASSWORD=.\+' .env 2>/dev/null; then
      export DB_PASSWORD="$(grep '^DB_PASSWORD=' .env | head -1 | cut -d= -f2-)"
    else
      DB_PASSWORD="$(openssl rand -hex 16)"
      echo "DB_PASSWORD=${DB_PASSWORD}" >> .env
      export DB_PASSWORD
      changed=1
      log "Generated DB_PASSWORD in .env"
    fi
  fi
  [[ -n "${OPENROUTER_API_KEY:-}" ]] || log "WARN: OPENROUTER_API_KEY unset — LLM routes may fail"
  [[ $changed -eq 0 ]] || log "Reloading .env after key generation"
  load_env
}

registry_login() {
  local registry="${REGISTRY:-registry.gitlab.com}"
  if docker pull "${IMAGE_REF}" >/dev/null 2>&1; then
    return 0
  fi
  if [[ -n "${CI_REGISTRY_USER:-}" && -n "${CI_REGISTRY_PASSWORD:-}" ]]; then
    echo "${CI_REGISTRY_PASSWORD}" | docker login -u "${CI_REGISTRY_USER}" --password-stdin "${registry}"
    return 0
  fi
  if [[ -n "${GITLAB_DEPLOY_TOKEN_USER:-}" && -n "${GITLAB_DEPLOY_TOKEN:-}" ]]; then
    echo "${GITLAB_DEPLOY_TOKEN}" | docker login -u "${GITLAB_DEPLOY_TOKEN_USER}" --password-stdin "${registry}"
    return 0
  fi
  if command -v glab >/dev/null 2>&1; then
    local token user
    token="$(glab auth token 2>/dev/null || true)"
    user="${GITLAB_REGISTRY_USER:-oauth2}"
    if [[ -n "$token" ]]; then
      echo "$token" | docker login -u "$user" --password-stdin "${registry}" >/dev/null 2>&1 || true
    fi
  fi
}

resolve_image() {
  if docker image inspect "${IMAGE_REF}" >/dev/null 2>&1; then
    log "Using local image ${IMAGE_REF}"
    return 0
  fi
  if docker pull "${IMAGE_REF}" 2>/dev/null; then
    log "Pulled ${IMAGE_REF}"
    return 0
  fi
  log "Registry pull failed — building locally from Dockerfile.backend"
  docker build -f Dockerfile.backend -t "${IMAGE_REF}" .
}

image_id_for_ref() {
  docker image inspect --format '{{.Id}}' "${IMAGE_REF}" 2>/dev/null || true
}

running_api_image_id() {
  local cid
  cid="$("${COMPOSE[@]}" ps -q api 2>/dev/null || true)"
  [[ -n "$cid" ]] || return 0
  docker inspect --format '{{.Image}}' "$cid" 2>/dev/null || true
}

free_port_if_dev_server() {
  local pid
  pid="$(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 0
  if ps -p "$pid" -o args= 2>/dev/null | grep -q 'src.api.server:app'; then
    log "Stopping dev uvicorn on :8000 (pid ${pid})"
    kill "$pid" 2>/dev/null || true
    sleep 2
  else
    die "Port 8000 in use by another process (pid ${pid}) — free it or set API_PORT"
  fi
}

wait_postgres() {
  local i=0
  while [[ $i -lt 30 ]]; do
    if "${COMPOSE[@]}" ps postgres 2>/dev/null | grep -q '(healthy)'; then
      log "PostgreSQL healthy"
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  die "PostgreSQL did not become healthy in time"
}

wait_api_health() {
  local i=0
  while [[ $i -lt $MAX_HEALTH_ATTEMPTS ]]; do
    if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
      log "API healthy at ${HEALTH_URL}"
      return 0
    fi
    sleep "$HEALTH_SLEEP"
    i=$((i + 1))
  done
  "${COMPOSE[@]}" logs --tail=80 api >&2 || true
  die "API health check failed after ${MAX_HEALTH_ATTEMPTS} attempts"
}

main() {
  log "c4reqber production deploy"
  ensure_colima
  load_env
  ensure_env_keys
  free_port_if_dev_server

  export CI_REGISTRY_IMAGE="${REGISTRY_IMAGE}"
  export API_IMAGE_TAG="${IMAGE_TAG}"

  registry_login
  resolve_image

  local target_id current_id
  target_id="$(image_id_for_ref)"
  current_id="$(running_api_image_id)"

  if [[ -n "$target_id" && "$target_id" == "$current_id" ]]; then
    log "API already running image ${IMAGE_TAG} — skipping recreate"
  else
    log "Starting dependencies: postgres"
    "${COMPOSE[@]}" up -d postgres
    wait_postgres
    log "Deploying services: ${DEPLOY_SERVICES}"
    "${COMPOSE[@]}" up -d --no-build --pull missing ${DEPLOY_SERVICES}
    "${COMPOSE[@]}" ps
  fi

  wait_api_health
  log "Deploy complete — ${IMAGE_REF}"
  curl -fsS "${HEALTH_URL}" | head -c 400 || true
  echo
}

main "$@"
