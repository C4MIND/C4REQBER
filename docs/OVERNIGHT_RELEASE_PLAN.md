# Overnight Release Plan — Full Production Scope

**Date:** 2026-06-21  
**Branch:** `feat/production-upgrade`  
**Contract:** no халтура — real Postgres, Redis jobs, landing, web-v2, Flash-fix, packaging, audit fixes.

---

## Goals (all in scope tonight)

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | **Postgres prod** — `PostgresDatabase` in `db_manager.py` + Alembic `001_initial` | Done |
| 2 | **Redis job store** — `REDIS_URL` → `RedisJobStore` for multi-replica k8s | Done |
| 3 | **Flash TUI fix** — `FlashAndWait()` polls `job_id` after async flash | Done |
| 4 | **TUI auth** — `C4_API_EMAIL`/`C4_API_PASSWORD`; demo via `C4_DEMO_AUTH=1` | Done |
| 5 | **Landing** — nested `<main>` fix, `og-image.png`, version sync | Done |
| 6 | **web-v2** — Vite+React SPA (health, readiness, flash form) | Done |
| 7 | **PyPI packaging** — `[build-system]`, hatch wheel, `blast init` wizard | Done |
| 8 | **Desktop** — `packaging/desktop/` Mac `.app` + Win Inno Setup scaffold | Done |
| 9 | **Apple notarization** — `notarize-mac.sh` (human: Apple ID + app password) | Script ready |
| 10 | **k8s** — `redis.yaml`, `migrate-job.yaml`, readiness `/health/ready` | Done |
| 11 | **Audit fixes** — auth on discovery list, error sanitization, JWT prod fail-fast | Done |
| 12 | **CI** — pytest `--junitxml=report.xml` | Done |
| 13 | **PyPI upload** — `twine upload` | **Human:** TWINE token |

---

## K8s deploy order

```bash
cd k8s
cp secrets.example.yaml secrets.yaml   # fill DB, JWT, CSRF, OPENROUTER
./deploy.sh
```

Applies: namespace → configmap → secrets → postgres → **redis** → **alembic migrate job** → API deployment.

**Readiness probe:** `/api/v1/health/ready` (DB + cache must pass).

---

## PyPI (agent path)

```bash
python -m build
pip install dist/c4reqber-5.6.0-*.whl
blast init
blast serve --mcp
```

MCP templates: `packaging/mcp/cursor-mcp.json`, `packaging/mcp/claude-desktop-mcp.json`.

**Human-only:** `TWINE_PASSWORD` → `twine upload dist/*` (user provides token later).

---

## Desktop (human path)

```bash
packaging/desktop/mac/build.sh
# Optional after codesign cert:
APPLE_ID=... APPLE_APP_PASSWORD=... TEAM_ID=... SIGNING_IDENTITY=... \
  packaging/desktop/mac/notarize-mac.sh dist/C4REQBER.app
```

Windows: cross-compile TUI, PyInstaller on Win runner, `packaging/desktop/win/build.iss`.

---

## web-v2

```bash
cd web-v2 && npm install && npm run dev
# API proxy → http://127.0.0.1:8000
```

---

## Human-only checkpoints

1. **PyPI token** — `twine upload` (never commit)
2. **Apple notarization** — `APPLE_ID`, app-specific password, `TEAM_ID`, `SIGNING_IDENTITY`
3. **Windows Authenticode** — optional cert for SmartScreen
4. **GitLab push** — when user asks

---

## Success criteria

- [x] Postgres + Redis code paths implemented
- [x] Flash TUI polls async jobs
- [x] Landing valid HTML + og-image
- [x] web-v2 builds
- [x] `blast init` writes `~/.c4reqber/config.toml`
- [x] k8s manifests include Redis + migrate job
- [x] Notarization script ready
- [ ] `twine upload` (blocked on human token)
- [ ] Physical notarization run (blocked on Apple creds)

---

*Expanded scope — execution contract for production upgrade branch.*