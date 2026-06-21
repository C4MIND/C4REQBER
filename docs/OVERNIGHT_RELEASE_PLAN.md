# Overnight Release Plan — PyPI MCP + Mac/Win Desktop

**Date:** 2026-06-21  
**Branch:** `feat/production-upgrade` → `release/0.1.0-desktop`  
**Primary goals (in order):**

1. **PyPI:** `pip install c4reqber` → MCP в Cursor/Claude через `blast serve --mcp`
2. **Desktop:** рабочие **macOS .app** и **Windows installer** с настройками и TUI v9

**Not tonight:** k8s, Postgres prod, landing, web-v2, полный audit-fix.

---

## K8s reminder (do not forget)

`c4reqber-secrets` **бесполезен без кластера**. Сейчас манифесты **опережают код** (Postgres stub, in-memory jobs).  
Деплой k8s — **только после** Redis job store + реальный Postgres в `db_manager`.  
См. `PRODUCTION_UPGRADE_PLAN.md` Phase 7.

---

## Product shape (what user gets)

```
┌─────────────────────────────────────────────────────────────┐
│  PATH A — PyPI (агенты)                                     │
│  pip install c4reqber                                       │
│  → mcp.json: command "blast" args ["serve","--mcp"]         │
│  → 20–21 tools в Claude Desktop / Cursor                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PATH B — Desktop app (люди)                                │
│  Double-click C4REQBER                                        │
│  → First-run: API key (OPENROUTER) + optional local API     │
│  → Launches TUI v9 cockpit (terminal UI, как iTerm app)     │
│  → Demo mode works без ключа (--demo)                       │
└─────────────────────────────────────────────────────────────┘
```

**One-shot в desktop = bundled `blast` CLI + `c4tui-v9` binary**, не отдельный GUI-фреймворк.  
Настройки = `~/.c4reqber/config.toml` + TUI `:settings` / `blast models --save`.

---

## Architecture decision (fastest path to “real app”)

| Layer | Choice | Why |
|-------|--------|-----|
| Python core | **PyInstaller one-folder** | Already have `blast` typer CLI + MCP |
| TUI | **Pre-built Go binary** inside app bundle | `make release-all` in `src/tui/v9` |
| Local API | **Optional** subprocess `uvicorn` | Only if user enables “Run local backend” |
| Settings UI | **TUI palette + `blast init`** | No Electron/Tauri overnight |
| Mac wrap | **.app bundle** + `Info.plist` | Standard macOS app |
| Win wrap | **Inno Setup** or **NSIS** | Standard Windows installer |

**Avoid:** Electron, Tauri, Briefcase (too much scaffolding for one night).

---

## Blockers to fix first (≤2h)

| # | Task | File(s) |
|---|------|---------|
| B1 | Add `[build-system]` + hatch wheel config | `pyproject.toml` |
| B2 | Move `pytest`, `build`, `hatchling` → `[project.optional-dependencies] dev` | `pyproject.toml` |
| B3 | Package layout: `packages = ["src"]` or `src` layout mapping | `pyproject.toml` |
| B4 | `pip install .` smoke: `blast --help`, `blast serve --mcp` imports | manual |
| B5 | TUI auth: `C4_API_EMAIL`, `C4_API_PASSWORD` env (убрать hardcode) | `commands.go`, `config.go` |
| B6 | `blast init` — write `~/.c4reqber/config.toml` from wizard | `src/cli/blast_app.py` (new) |
| B7 | `.env.example` CSRF ≥32 chars | `.env.example` |

---

## Hour-by-hour schedule (8h autonomous block)

### Hour 0–1 — PyPI packaging

- [ ] Fix `pyproject.toml` (build-system, dependencies split, version `5.6.0`)
- [ ] Add `packaging/mcp/cursor-mcp.json` and `packaging/mcp/claude-desktop-mcp.json` templates
- [ ] Add `packaging/README-PYPI.md` → fold into main README section “MCP Setup”
- [ ] `python -m build` → wheel + sdist
- [ ] TestPyPI upload (if token available) else local `pip install dist/*.whl`

**Acceptance:** fresh venv → `pip install c4reqber` → `blast serve --mcp` starts without ImportError.

### Hour 1–2 — MCP polish (minimum)

- [ ] Verify all 20 registered tools + optional `c4_codegen` import
- [ ] `docs/mcp_registry.md` — copy-paste mcp.json with `env.OPENROUTER_API_KEY`
- [ ] Smoke: `blast flash "test"` with key in env (optional manual)
- [ ] **Skip:** Postgres, k8s, discovery list auth (MCP doesn't hit that route)

### Hour 2–3 — Go binaries

- [ ] `cd src/tui/v9 && make release-all`
- [ ] Artifacts: `c4tui-v9-darwin-arm64`, `darwin-amd64`, `windows-amd64.exe`, `linux-amd64`
- [ ] Embed version in `c4tui-v9 -version` (already in main.go?)
- [ ] Update `tui_launcher.py` to prefer bundled binary next to app

### Hour 3–5 — Mac desktop app

- [ ] Create `packaging/desktop/mac/`:
  - `build.sh` — PyInstaller + copy Go binary + plist
  - `Info.plist` — `CFBundleName`, `CFBundleExecutable`, terminal app (`LSUIElement` false)
  - `launcher.sh` — reads `~/.c4reqber/config.toml`, sets env, runs TUI or demo
- [ ] PyInstaller spec `c4reqber-desktop.spec`:
  - Entry: `src/cli/blast_app.py` (or thin `packaging/desktop/launcher.py`)
  - Hidden imports: `src.mcp_server.server`, heavy deps minimal subset
  - **Slim mode:** exclude simulations optional (lazy import already?)
- [ ] Output: `dist/C4REQBER.app`
- [ ] Optional: `create-dmg` for distribution

**Acceptance:** double-click → Terminal opens → TUI splash → demo works without API key.

### Hour 5–7 — Windows desktop app

- [ ] Cross-compile Go on Mac (already `GOOS=windows`)
- [ ] PyInstaller on Windows **or** GitLab `windows` runner **or** ship “portable zip” first
- [ ] `packaging/desktop/win/build.iss` (Inno Setup)
- [ ] Installer: Program Files, Start Menu, `%APPDATA%\c4reqber\config.toml`
- [ ] Fallback if no Win runner: **portable ZIP** `C4REQBER-win64.zip` (still a valid v0.1)

**Acceptance:** `C4REQBER.exe` → cmd window → TUI; config in AppData.

### Hour 7–8 — Settings + docs + tag

- [ ] `blast init` interactive (Rich prompts): OPENROUTER_API_KEY, C4_API_URL, C4_LANG
- [ ] Desktop launcher calls `blast init` on first run if no config
- [ ] `RELEASE.md` — install paths Mac/Win/PyPI
- [ ] Git tag `v5.6.0+desktop.1` (local or GitLab)
- [ ] PyPI publish (manual token step by human)

---

## PyPI package structure (target)

```toml
[project]
name = "c4reqber"
version = "5.6.0"
requires-python = ">=3.11"
dependencies = [
  # core only: typer, rich, pydantic, httpx, mcp, openai, ...
]

[project.optional-dependencies]
api = ["fastapi", "uvicorn", ...]
full = ["numpy", "pandas", ...]  # heavy science
dev = ["pytest", "ruff", "mypy", ...]

[project.scripts]
blast = "src.cli.blast_app:app"
c4reqber = "src.cli.blast_app:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Size strategy:** default wheel should install in <2 min on MacBook; sim engines stay optional / lazy.

---

## MCP config templates (ship in repo)

**Cursor / Claude Desktop (`mcp.json`):**

```json
{
  "mcpServers": {
    "c4reqber": {
      "command": "blast",
      "args": ["serve", "--mcp"],
      "env": {
        "OPENROUTER_API_KEY": "<your-key>",
        "PYTHONPATH": ""
      }
    }
  }
}
```

Note: after PyPI install, `blast` is on PATH — no `PYTHONPATH=src` needed.

---

## Desktop app user flow

```
First launch
  ├─ No ~/.c4reqber/config.toml?
  │    └─ blast init (API key, language, demo vs live)
  ├─ "Live discovery" enabled?
  │    ├─ Yes → start uvicorn background (optional v0.1)
  │    └─ No  → blast tui --demo
  └─ Launch c4tui-v9 (bundled binary)

Settings later
  ├─ TUI command palette :settings
  ├─ blast models --save
  └─ Edit ~/.c4reqber/config.toml
```

---

## What we deliberately skip tonight

| Item | Reason |
|------|--------|
| k8s + secrets deploy | Code not ready (Phase 7) |
| Postgres + Alembic runtime | SQLite enough for desktop single-user |
| Flash TUI fix | Use one-click / demo for desktop v0.1 |
| Apple code signing / notarization | Needs Apple Dev account (human) |
| Windows Authenticode signing | Needs cert (human) |
| web-v2 | Directory absent |
| Landing / og-image | Not blocking install |
| Full pytest in CI | Ship first, harden later |

---

## Human-only checkpoints (cannot AI-automate)

1. **PyPI token** — `twine upload` (use env `TWINE_PASSWORD`, never commit)
2. **Apple notarization** — optional for v0.1 (users: right-click Open)
3. **Windows SmartScreen** — unsigned exe warning expected
4. **GitLab push** — when ready

---

## Success criteria (tomorrow morning)

- [ ] `pip install c4reqber` from TestPyPI or local wheel
- [ ] Cursor MCP connects, `c4_solve` or `blast_turbo` returns JSON
- [ ] `C4REQBER.app` opens TUI on macOS
- [ ] `C4REQBER-win64.zip` or `.exe` opens TUI on Windows
- [ ] `blast init` creates config; no hardcoded test password in TUI
- [ ] k8s **not** deployed; reminder in plan ✅

---

## After overnight (Phase 9 backlog)

1. Flash TUI ↔ async job polling
2. Code signing + auto-update (Sparkle / WinSparkle)
3. Menu bar app wrapper (macOS) — optional
4. PyPI size optimization (split `c4reqber-core` / `c4reqber-full`)
5. k8s only after Redis jobs + Postgres `db_manager`

---

## File tree to create

```
packaging/
├── mcp/
│   ├── cursor-mcp.json
│   └── claude-desktop-mcp.json
├── desktop/
│   ├── mac/
│   │   ├── build.sh
│   │   ├── Info.plist
│   │   └── launcher.sh
│   ├── win/
│   │   ├── build.iss
│   │   └── launcher.bat
│   └── c4reqber-desktop.spec
└── README-PYPI.md
```

---

*This plan is the execution contract for the next implementation session.*