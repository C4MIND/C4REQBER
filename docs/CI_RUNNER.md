# CI/CD & GitLab Runner — c4reqber

**Updated:** 2026-07-11

## Failure modes we hit (and fixes)

| # | Symptom | Root cause | Fix in repo / GitLab |
|---|---------|------------|---------------------|
| 1 | `tcp://docker:2375` | DinD on Mac Colima runner | Kaniko executor (no DinD) |
| 2 | Pipeline 0 jobs | YAML colon in `deploy-production` echo | Quote script lines |
| 3 | `bash: not found` | Kaniko image is busybox | `sh scripts/ci/...` |
| 4 | Job killed at **1h** (`exit 143`) | **Project** `build_timeout=3600` caps job timeout | GitLab Settings → CI/CD → **3h** (`10800`); job `timeout: 3h` |
| 5 | pip >1h on huggingface | Full `requirements.txt` in Docker | `requirements-docker.txt` (filtered) |
| 6 | `resolution-too-deep` | pip on `pydantic-ai` graph | `uv pip install` in Dockerfile |
| 7 | MR won't merge | Flaky `tui-v9-test` fails pipeline | `allow_failure: true` + test sleep fix |
| 8 | Red pipeline, green Pages | Unrelated job failure | `pages` has `needs: []`; TUI advisory only |

**Critical:** GitLab project **maximum job timeout** overrides per-job `timeout:` when project limit is lower. Verify: Settings → CI/CD → General pipelines → **Timeout** = **3 hours**.

## Pipeline overview (`main`)

| Job | Stage | Blocks pipeline? | Purpose |
|-----|-------|------------------|---------|
| `test-backend` | test | **yes** | Ruff, checks, pytest |
| `tui-v9-test` | test | no (`allow_failure`) | Go TUI advisory |
| `build-api` | build | **yes** | Kaniko → registry (`timeout: 3h`, retry ×2) |
| `pages` | deploy | no (`needs: []`) | Landing / GitLab Pages |
| `deploy-production` | deploy | no (`manual`, `allow_failure`) | Prod deploy hint |

## `build-api` stack

1. **Kaniko** — no Docker daemon (Mac runner safe)
2. **`requirements-docker.txt`** — committed, checked in `test-backend` via `check_docker_requirements.sh`
3. **`uv pip install`** — same resolver strategy as `scripts/ci/setup_python.sh`
4. **`timeout: 3h`** + project `build_timeout=10800` + runner `maximum_timeout=10800`

Regenerate docker requirements:

```bash
sh scripts/ci/filter_requirements.sh requirements.txt requirements-docker.txt
sh scripts/ci/check_docker_requirements.sh
```

## Self-hosted runner — Mac + Colima

See `scripts/ci/gitlab-runner.colima.example.toml`:

- `host = unix:///Users/<you>/.colima/default/docker.sock`
- `maximum_timeout = 10800`
- **No** `docker:dind` CI service

## Pages

Public URL: https://turbo-cdi-86c583.gitlab.io/

If login redirect: Settings → General → Pages → **Everyone**.

## Registry

```
registry.gitlab.com/cognitive-functors/turbo-cdi/api:latest
```
