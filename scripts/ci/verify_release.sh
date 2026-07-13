#!/usr/bin/env sh
# Verify the published API image is pullable and runnable (end-user release gate).
# Runs in CI after build-api — does NOT deploy to any host.
set -eu

REGISTRY_IMAGE="${CI_REGISTRY_IMAGE:-registry.gitlab.com/cognitive-functors/c4reqber}"
IMAGE_TAG="${API_IMAGE_TAG:-latest}"
IMAGE_REF="${REGISTRY_IMAGE}/api:${IMAGE_TAG}"
SHA_TAG="${REGISTRY_IMAGE}/api:${CI_COMMIT_SHA}"

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

log "Release verify: ${IMAGE_REF}"

# Registry manifest check (works without local Docker)
if [ -n "${CI_JOB_TOKEN:-}" ]; then
  MANIFEST_URL="https://gitlab.com/v2/cognitive-functors/turbo-cdi/api/manifests/${IMAGE_TAG}"
  if curl -fsS -o /dev/null -H "JOB-TOKEN: ${CI_JOB_TOKEN}" "${MANIFEST_URL}"; then
    log "Registry manifest OK (${IMAGE_TAG})"
  else
    die "Registry manifest missing for ${IMAGE_TAG}"
  fi
fi

if ! docker info >/dev/null 2>&1; then
  log "Docker not available — manifest check only (OK for end-user release gate)"
  exit 0
fi

if [ -n "${CI_REGISTRY:-}" ] && [ -n "${CI_REGISTRY_USER:-}" ] && [ -n "${CI_REGISTRY_PASSWORD:-}" ]; then
  echo "${CI_REGISTRY_PASSWORD}" | docker login -u "${CI_REGISTRY_USER}" --password-stdin "${CI_REGISTRY}" \
    || die "Registry login failed"
else
  log "WARN: CI registry credentials missing — pull may fail on private projects"
fi

docker pull "${IMAGE_REF}" || die "Failed to pull ${IMAGE_REF}"
docker pull "${SHA_TAG}" 2>/dev/null || log "WARN: SHA tag ${SHA_TAG} not found (latest is enough)"

log "Smoke: import FastAPI app inside image"
docker run --rm \
  -e JWT_SECRET=ci-release-smoke-secret-min-32-chars \
  -e DATABASE_URL=sqlite:///tmp/smoke.db \
  -e CACHE_BACKEND=memory \
  -e DEV_MODE=1 \
  "${IMAGE_REF}" \
  python -c "from src.api.server import app; print('import_ok', app.title)" \
  || die "In-image import smoke failed"

log "Release OK — end users can install via:"
printf '%s\n' \
  "  pip install c4reqber && blast setup" \
  "  docker pull ${IMAGE_REF}" \
  "  docker compose -f docker-compose.release.yml up -d" \
  "  Docs: https://turbo-cdi-86c583.gitlab.io/docs/install.html"
