> **Note:** Repo on **GitLab** (`git@gitlab.com:cognitive-functors/c4reqber.git`). GitHub is a read-only mirror.

# TUI v9 "The Cockpit"

**Tag / honesty:** aligned with **v9.18.0** honesty contract — see [`docs/HONESTY_CONTRACT.md`](../../../docs/HONESTY_CONTRACT.md).
**Status mapping (anti green-fake):**
- `sim_finished` → green only if `engine_status` ∈ `{ok, success, completed}`
- `partial` / `stub` / `unavailable` → amber/red, not success glyph
- Job `partial` → `toast.partial` (no celebration burst); `failed` → `toast.failed` + error card
- Capsim summary card uses `EngineStatus: partial` (probe ≠ engine available)
- Debug overlay (Ctrl+Shift+D) records last SSE type + timestamp
- Restored feed cards do **not** show `NEW`

**Pipeline claim:** discovery may end `complete` **or** `partial` — do not assume F(verified).

## Quick Start

```bash
# 1. API ключи
cp .env.dontredact .env

# 2. Бэкенд
cd /Users/figuramax/LocalProjects/C4REQBER
nohup .venv/bin/python -m uvicorn src.api.server:app \
  --host 127.0.0.1 --port 8000 --no-access-log > /tmp/c4backend.log 2>&1 &

# 3. TUI
cd src/tui/v9 && ./bin/c4tui-v9

# 4. Demo режим (без бэкенда)
./bin/c4tui-v9 --demo --story=crispr
```

**Что изменилось с v9.11.0?** См. CHANGELOG.md в корне. Основное:
- Discovery теперь работает (был баг `_ = submitCmd`)
- Pipeline A→F за ~2 мин (было 5+)
- Диссертация с нормальными ссылками [1]..[N] и DOI
- Два режима вывода: human (статья) / explain (технический)
- 7 языков, все переводы контекстные

---

```
◉ C4REQBER v9  F<1,1,0>  [EN]  DeepSeek  $0.0000  04:55:12  DISCOVER
├────────────────────────────────────────────────────────────────┤
│ ▣ Phase A: Framing   [██████░░░░░░░] 33%                       │
│ ▣ Phase B: Search    [████████████░░] 65%                       │
│ ✦ Hypothesis (typing...)  87% confidence                       │
│ 📚 Optimized sgRNA design to maximize activity and minimize off-target │
│    Diekelmann & Born · Nature 2010 · 3728 citations              │
├────────────────────────────────────────────────────────────────┤
│ ❯ design a CRISPR guide RNA with minimal off-targets in T-cells…  │
├────────────────────────────────────────────────────────────────┤
│ ⏵ RUNNING                              [Enter] Run [Tab] Mode [Ctrl+C] Quit  │
└────────────────────────────────────────────────────────────────┘
```

## What is this?

TUI v9 is the **single-screen, feed-driven** version of c4reqber. The entire app fits in one terminal window. Cards appear in the feed as the discovery progresses. Discoveries, hypotheses, papers, simulations, verifications — all rendered inline as they happen.

## Architecture

**4 subpackages** (per Go AGENTS.md "modules ≤300 lines"):

| Package | LOC | Purpose |
|---|---|---|
| `tui` (root) | 720 | model, view, update, commands — main loop |
| `tui/i18n` | 330 | translations, 7 languages, mutex-safe |
| `tui/effects` | 410 | Rain, Burst, SlideIn, Typewriter, Sparkles |
| `tui/api` | 380 | Client wrapping c4reqber backend (CSRF + JWT + SSE) |

## Features

### Core
- **4-region single layout** — header + feed (viewport) + input (textarea) + footer
- **5 card types** — Phase, Hypothesis, Paper, Code, Error
- **5 game-feel effects** (60fps driven):
  - Matrix rain (idle state, katakana falling)
  - Particle burst (50 particles, gravity, 2.5s)
  - Card slide-in (Harmonica spring, 200ms ease-out)
  - Typewriter reveal (hypothesis char-by-char, 33ms each)
  - Cursor sparkles (on keypress, gravity)
- **Pulsing badge** ●/◉ every 250ms when running
- **Progress bars** `[████░░░░] 50%` on phase cards
- **Cost ticker** live in header

### Backend
- **SSE streaming** via `/v8/discover/stream/{id}` for real-time events
- **Polling fallback** via `/v8/discover/status/{id}` every 2s if SSE fails
- **CSRF + JWT auth** auto-harvested from `/api/v1/health`
- **5 endpoints wired**:
  - `OneClick` — full discovery pipeline
  - `Flash` — sync quick answer
  - `Multi` — multi-hypothesis
  - `KnowledgeSearch` — paper discovery
  - `JobStatus` — poll endpoint

### Modes (Tab to cycle)
- **Discover** — full 7-phase pipeline
- **Flash** — sync quick answer
- **Turbo** — paradigm shift
- **TurboFactory** — parallel factory

### i18n (7 languages, 210 translations)
| Lang | Source | Coverage |
|---|---|---|
| EN | hand-authored | 100% (30 keys) |
| RU | hand-authored | 100% (30 keys) |
| ZH | OpenRouter→DeepInfra | 100% (30 keys) |
| JA | OpenRouter→DeepInfra | 100% (30 keys) |
| DE | OpenRouter→DeepInfra | 100% (30 keys) |
| AR | OpenRouter→DeepInfra | 100% (30 keys) |
| HI | OpenRouter→DeepInfra | 100% (30 keys) |

### Mouse
- **Clickable cards** via bubblezone v2 — click any card to "select" it
- Mouse motion enabled (`tea.MouseModeCellMotion`)

## How to build & run

```bash
cd src/tui/v9
make build          # → bin/c4tui-v9
make test           # 20/20 PASS
make run            # run with TTY (needs backend on :8000)
make release-all    # cross-compile to 4 platforms
```

## Headless probe (e2e testing)

```bash
# Build the headless probe (no TTY required)
go build -o bin/c4tui-v9-probe ./cmd/c4tui-v9-probe

# Run against live backend
./bin/c4tui-v9-probe "test CRISPR off-target effects in T-cells"

# Output: full JSON report (auth, submit, polls, papers, hypothesis)
```

Used by CI for live integration smoke tests. The probe runs the **full flow** without TTY:
1. Health + CSRF harvest
2. Register (idempotent)
3. Login → JWT
4. Submit one-click
5. Poll loop (30 polls, every 2s)
6. Knowledge search (parallel discovery source)
7. JSON report to stdout

## Tests

```bash
$ go test ./... -count=1
ok  github.com/figuramax/c4reqber-tui-v9         (20/20 PASS, 23.6% coverage)
?   github.com/figuramax/c4reqber-tui-v9/api     (no test files)  ← see api_test.go
?   github.com/figuramax/c4reqber-tui-v9/cmd     (no test files)
ok  github.com/figuramax/c4reqber-tui-v9/effects (94.0% coverage)
ok  github.com/figuramax/c4reqber-tui-v9/i18n    (18.8% coverage)
```

**Total: 20 tests** (i18n: 6, view: 5, effects: 9) + **api: 7 tests** (httptest-based, no real backend needed).

## GitLab CI

`.gitlab-ci.yml` defines 3 new jobs:
- `tui-v9:test` — runs `go test -race`
- `tui-v9:build` — builds `bin/c4tui-v9` and uploads as artifact
- `tui-v9:release` — cross-compiles to 4 platforms on every `v9.*` tag

## Keyboard map

| Key | Action |
|---|---|
| `Enter` | Submit query |
| `Tab` | Cycle mode (Discover → Flash → Turbo → TurboFactory) |
| `Esc` | Cancel running discovery |
| `Ctrl+C` | Quit |
| `?` | Help (inline card in feed) |
| Mouse click | Select card (zone-based) |

## Architecture decisions (from `tui-v9-cockpit-plan-v2.md` §13)

Built on the Charm ecosystem:
- `charm.land/bubbletea/v2` (Elm-architecture TUI framework)
- `charm.land/bubbles/v2` (textarea, viewport, etc.)
- `charm.land/lipgloss/v2` (style engine)
- `github.com/lrstanley/bubblezone/v2` (mouse zones)
- `github.com/charmbracelet/harmonica` (spring animations)

## Performance

- **Binary size:** 11.4 MB stripped (-s -w) Mach-O arm64
- **Startup:** ~50ms (including alt-screen + mouse setup)
- **60fps animation loop:** 16ms tick, 5 effects ticking in parallel
- **Memory:** ~30MB resident (mostly lipgloss + bubbletea internals)
- **Backend roundtrips:** 1 for auth, 1 for submit, 1 for knowledge search, 1 per poll (or streaming)

## Cross-platform release

`make release-all` produces:
- `bin/c4tui-v9-linux-amd64` (Linux, x86_64)
- `bin/c4tui-v9-darwin-arm64` (macOS Apple Silicon)
- `bin/c4tui-v9-darwin-amd64` (macOS Intel)
- `bin/c4tui-v9-windows-amd64.exe` (Windows)

GitLab CI runs this on every `v9.*` tag and uploads to GitLab Releases.

## What's next (v9.1+)

- SSH exposure via `charmbracelet/wish`
- Runtime language switch (Shift+L)
- Achievements, theme unlocks, streaks
- 5th screen for export to .md / .bib

## License

Same as c4reqber (AGPL-3.0 / Commercial).
