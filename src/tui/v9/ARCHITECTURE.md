# Architecture — c4reqber TUI v9 + Backend

## High Level

```
┌─────────────┐     SSE/HTTP      ┌──────────────┐
│  TUI v9.13.0 │ ←─────────────→ │   Backend    │
│  (Go+Bubble) │    :8000        │  (FastAPI)   │
│              │                  │  :8000       │
│  bin/c4tui-v9│                  │  uvicorn     │
└─────────────┘                  └──────┬───────┘
                                        │
                              ┌─────────┴─────────┐
                              │   Discovery        │
                              │   Pipeline (A→G)   │
                              │                    │
                              │  7 phases, ~2-5min │
                              └────────────────────┘
```

## TUI v9 (Go)

- **Framework:** Bubble Tea v2 (charm.sh)
- **Key files:** `src/tui/v9/`
  - `view.go` — renderHeader/renderFooter/progressBar
  - `update.go` — Update loop, key handlers, SSE/poll
  - `commands.go` — tea.Cmd functions (submitCmd, flashCmd, pollCmd, sseCmd)
  - `empty_widgets.go` — 7 dashboard widgets for empty state
  - `keymap.go` — platform-aware key bindings (Cmd on Mac, Ctrl on Linux)
  - `settings_menu.go` — Ctrl+, settings
- **i18n:** 7 languages × 158 keys in `i18n/*.toml`
- **Build:** `make build` → `bin/c4tui-v9`

## Backend (Python/FastAPI)

- **Entry:** `uvicorn src.api.server:app --port 8000`
- **Auth:** CSRF + JWT (kilo-v9@test.com / test12345)
- **Pipeline:** `src/api/v8_routers/discovery/pipeline.py`
  - Phase A: Cognitive framing
  - Phase B: Multi-source search (OpenAlex, Crossref, etc.)
  - Phase C: Gap analysis + contradiction mining (chunked 7× parallel)
  - Phase D: Hypothesis generation (LLM)
  - Phase E: Simulation
  - Phase F: Quality + formal verification
  - Phase G: Dissertation generation

## How to Test Without Backend

```bash
cd src/tui/v9 && ./bin/c4tui-v9 --demo --story=crispr
```

## Key API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/login` | Login |
| POST | `/v8/discover/one-click` | Start discovery |
| GET | `/v8/discover/status/{job_id}` | Poll job status |
| GET | `/v8/discover/stream/{job_id}` | SSE stream |

## Recent fixes (v9.12.x)

See `CHANGELOG.md` for full history. Key fixes:
1. Discovery submit was broken (`_ = submitCmd` discarded request)
2. SSE streaming was broken (`m.sseEvents` never assigned)
3. Phase C pipeline hung at search (S2 rate limit + citation chaser crash)
4. Register endpoint returned 500 on duplicate user
5. Header/footer corrupted by Unicode width miscalculation
6. Phase F LLM response parse crash (try/except → fallback)
7. `_pick_centroids` order mismatch (as_completed → dict fix)
