#!/bin/sh
# Build and push the c4reqber API image to GitLab Container Registry.
# Used by .gitlab-ci.yml job build-api (Kaniko executor).
set -eu

: "${CI_PROJECT_DIR:?CI_PROJECT_DIR is required}"
: "${CI_REGISTRY_IMAGE:?CI_REGISTRY_IMAGE is required}"
: "${CI_COMMIT_SHA:?CI_COMMIT_SHA is required}"

DOCKERFILE="${DOCKERFILE:-Dockerfile.backend}"
CONTEXT="${CI_PROJECT_DIR}"
DEST_SHA="${CI_REGISTRY_IMAGE}/api:${CI_COMMIT_SHA}"
DEST_LATEST="${CI_REGISTRY_IMAGE}/api:latest"

echo "==> Building API image"
echo "    dockerfile: ${DOCKERFILE}"
echo "    context:    ${CONTEXT}"
echo "    dest:       ${DEST_SHA}"
echo "    dest:       ${DEST_LATEST}"

if command -v /kaniko/executor >/dev/null 2>&1; then
  DOCKER_CONFIG="${DOCKER_CONFIG:-/kaniko/.docker}"
  export DOCKER_CONFIG
  mkdir -p "${DOCKER_CONFIG}"

  if [ -n "${CI_REGISTRY:-}" ] && [ -n "${CI_REGISTRY_USER:-}" ] && [ -n "${CI_REGISTRY_PASSWORD:-}" ]; then
    cat > "${DOCKER_CONFIG}/config.json" <<EOF
{
  "auths": {
    "${CI_REGISTRY}": {
      "username": "${CI_REGISTRY_USER}",
      "password": "${CI_REGISTRY_PASSWORD}"
    }
  }
}
EOF
  fi

  /kaniko/executor \
    --context "${CONTEXT}" \
    --dockerfile "${CONTEXT}/${DOCKERFILE}" \
    --destination "${DEST_SHA}" \
    --destination "${DEST_LATEST}" \
    --snapshot-mode=redo \
    --use-new-run \
    --verbosity=info
  exit 0
fi

# Fallback: host Docker (self-hosted runners with Colima/socket — no DinD).
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: neither Kaniko nor a reachable Docker daemon is available." >&2
  echo "Self-hosted runner: set runners.docker.host to your Colima socket in config.toml." >&2
  echo "See docs/CI_RUNNER.md" >&2
  exit 1
fi

if [ -n "${CI_REGISTRY:-}" ] && [ -n "${CI_REGISTRY_USER:-}" ] && [ -n "${CI_REGISTRY_PASSWORD:-}" ]; then
  echo "${CI_REGISTRY_PASSWORD}" | docker login -u "${CI_REGISTRY_USER}" --password-stdin "${CI_REGISTRY}"
fi

docker build \
  -f "${CONTEXT}/${DOCKERFILE}" \
  -t "${DEST_SHA}" \
  -t "${DEST_LATEST}" \
  "${CONTEXT}"

docker push "${DEST_SHA}"
docker push "${DEST_LATEST}"
