# CI/CD & GitLab Runner — c4reqber

**Updated:** 2026-07-11

This document explains how GitLab CI builds the API image, deploys Pages, and how to configure the self-hosted Mac runner (Colima).

## Pipeline overview (`main`)

| Job | Stage | Purpose |
|-----|-------|---------|
| `test-backend` | test | Ruff, truths, MCP registry, pytest |
| `tui-v9-test` | test | Go vet/build/test for TUI v9 |
| `build-api` | build | Build + **push** API image to GitLab Container Registry |
| `pages` | deploy | Publish `landing/` to GitLab Pages |
| `deploy-production` | deploy | Manual production deploy (depends on `build-api`) |

`pages` does **not** depend on `build-api` — a landing deploy succeeds even if the API image build is skipped on a feature branch.

## `build-api` — why Kaniko (not Docker-in-Docker)

The previous job used `docker:24-dind`. That fails on macOS self-hosted runners because:

- `privileged = false` (required on Mac)
- DinD needs Linux cgroups/namespaces Colima does not expose to service containers
- Error: `Cannot connect to the Docker daemon at tcp://docker:2375`

**Fix:** `build-api` now uses [Kaniko](https://github.com/GoogleContainerTools/kaniko) — builds and pushes images **without** a Docker daemon. Works on shared GitLab runners and self-hosted Docker executors alike.

Fallback: if Kaniko is unavailable but host Docker works (Colima socket configured on the runner), `scripts/ci/build_api_image.sh` uses `docker build` + `docker push`.

## Self-hosted runner — Mac + Colima

Runner tag: `docker`, `c4reqber` (see `.gitlab-ci.yml` `default.tags`).

### Recommended `config.toml` snippet

Copy from `scripts/ci/gitlab-runner.colima.example.toml`. Key settings:

```toml
[[runners]]
  executor = "docker"
  tag_list = ["docker", "c4reqber"]
  [runners.docker]
    host = "unix:///Users/<you>/.colima/default/docker.sock"
    privileged = false
    pull_policy = ["if-not-present"]
    volumes = ["/cache"]
```

**Do not** add `docker:24-dind` as a CI service when `host` points to Colima — they conflict.

### Verify locally

```bash
colima status          # should be Running
docker info            # should succeed
bash scripts/ci/build_api_image.sh   # only works inside CI with env vars set
```

## GitLab Pages — public access

If `https://cognitive-functors.gitlab.io/turbo-cdi/` redirects to GitLab login, Pages are set to **private**.

**Fix (project maintainer):**

1. GitLab → **Settings → General → Visibility, project features, permissions**
2. **Pages** → **Everyone** (public)
3. Or API: `pages_access_level=public` (project can stay private)

After change, allow ~2 minutes for CDN propagation.

## Container Registry image

After a green `build-api` on `main`:

```
registry.gitlab.com/cognitive-functors/turbo-cdi/api:latest
registry.gitlab.com/cognitive-functors/turbo-cdi/api:<commit-sha>
```

Use in `docker-compose.prod.yml` or Kubernetes instead of local `build:` when deploying production.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `tcp://docker:2375` connection refused | DinD service enabled | Remove dind; use Kaniko job (current `.gitlab-ci.yml`) |
| Kaniko push 401 | Registry auth | GitLab provides `CI_REGISTRY_*` on project runners automatically |
| `pages` OK but site asks login | `pages_access_level: private` | Set Pages to Everyone (above) |
| Pipeline red, landing live | `build-api` failed | Check job log; Pages is independent |
