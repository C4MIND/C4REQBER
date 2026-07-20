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
| 9 | pytest **Killed** at ~80% | Two pipelines on one Mac runner (`concurrent=4`) | `resource_group: mac-colima` + runner `limit=1` + auto-cancel |
| 10 | `bash: not found` in TUI job | `golang:*-alpine` has no bash | Use `golang:1.26` (debian) or POSIX `sh` scripts |

**Critical:** GitLab project **maximum job timeout** overrides per-job `timeout:` when project limit is lower. Verify: Settings → CI/CD → General pipelines → **Timeout** = **3 hours**.

## Concurrency model (single Mac runner)

Professional pattern for one self-hosted runner with limited RAM:

1. **`resource_group: mac-colima-v2`** on all Mac runner jobs — GitLab semaphore, one job at a time across all pipelines.
2. **`workflow.auto_cancel.on_new_commit: interruptible`** — new push cancels stale pipelines.
3. **Project `auto_cancel_pending_pipelines=enabled`** — redundant pipelines cancelled.
4. **Runner `limit = 1`** on `c4reqber MacBook docker` — runner never picks up a second job.
5. **Resource group `process_mode=oldest_first`** — FIFO queue (API one-time setup).

```bash
# One-time project settings (already applied on turbo-cdi):
glab api --method PUT projects/cognitive-functors%2Fturbo-cdi \
  -f auto_cancel_pending_pipelines=enabled
glab api --method PUT projects/cognitive-functors%2Fturbo-cdi/resource_groups/mac-colima-v2 \
  -f process_mode=oldest_first
```

## Pipeline overview (`main`)

| Job | Stage | Blocks pipeline? | Purpose |
|-----|-------|------------------|---------|
| `test-backend-checks` | test | **yes** | Ruff, scripts, fast pytest |
| `test-backend-suite` | test | **yes** | Heavy pytest (verification/discovery/api/knowledge) |
| `tui-v9-test` | test | no (`allow_failure`) | Go TUI advisory |
| `build-api` | build | **yes** | Kaniko → registry (`timeout: 3h`, retry ×2) |
| `deploy-production` | deploy | **yes** | Verify registry image pull + import smoke (end-user release) |
| `pages` | deploy | no (`needs: []`) | Landing / GitLab Pages |

## `build-api` stack

1. **Kaniko** — no Docker daemon (Mac runner safe)
2. **`requirements-docker.txt`** — committed, checked in `test-backend-checks` via `check_docker_requirements.sh`
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

Public URL: https://cognitive-functors.gitlab.io/c4reqber/

If login redirect: Settings → General → Pages → **Everyone**.

## PyPI tag release order (badge pitfall)

`pypi-publish-prod` runs only on tags matching `^v\d+\.\d+\.\d+$` and needs green
`test-backend-checks` + `test-backend-suite` on that **tag** pipeline.

**Order (avoid dual queue on one Mac runner):**

1. Locally run the same suite as CI (`tests/verification/` … `not slow`) until 0 failed.
2. Push the release commit to `main` only; wait until `main` suite is green.
3. Then `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. Confirm publish via Pipelines `ref=vX.Y.Z` + `https://pypi.org/pypi/c4reqber/json`, **not** the
   CI icon next to the commit in Commits.

**Why:** Pushing `main` and the tag together starts two pipelines that share
`resource_group: mac-colima-v2`. Canceling `main` to unblock the tag frees the runner but leaves a
**canceled** badge on that SHA in the Commits UI even when the tag pipeline and PyPI succeed.
Retry the `main` pipeline afterward if you need a green commit badge (no new version bump).

## Registry

```
registry.gitlab.com/cognitive-functors/c4reqber/api:latest
```
