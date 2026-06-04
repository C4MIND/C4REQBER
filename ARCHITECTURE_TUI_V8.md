# C4REQBER TUI v8 — Architecture

> Under-the-hood by default. Complexity is hidden from the user, visible on demand via Dashboard / Palette.

## 1. Overview

TUI v8 is a [Bubble Tea](https://github.com/charmbracelet/bubbletea)-based terminal interface for the C4REQBER discovery engine. It orchestrates a 7-phase cognitive pipeline (A–G), surfaces backend results through a reactive widget tree, and maintains a living "Cube Mascot" (3-frame ASCII companion) that reacts to user progress with theme-aware colors and S-rank jump animations.

**v8 improvements over v7:**
- Lock-free theme reads via `atomic.Value` (eliminates RWMutex contention on `ActiveTheme`)
- History navigation routed through Bubble Tea message loop (no direct textarea mutations)
- Poll tick de-duplication via cancellable timer (prevents tick pile-up during rapid state changes)
- SSE unknown events return `nil` instead of errors (graceful degradation)
- SSE JSON payload validation (`phase`/`status` required fields)
- Diagnostic test 3 now calls `Verify` instead of duplicating test 1 (`C4Navigate`)
- Chat viewport resizes even when collapsed
- `PhaseIndex("")` returns `-1` instead of `0`
- Mascot save serialized through single worker goroutine (was spawning unbounded goroutines)
- `containsWord` uses word-character boundaries (handles punctuation correctly)
- Deprecated `tea.MouseLeft` replaced with `tea.MouseActionPress + tea.MouseButtonLeft`
- Unused vars/funcs removed across widgets, update.go, splash_test.go
- `staticcheck ./...` passes clean; `go vet` clean; `gofmt` formatted

**Quality target:** 90–92 / 100 (audit-driven).

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────┐
│                 User Input                  │
│  (Keyboard bindings, mouse, mode buttons)   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│              C4TUIv7 (App)                  │
│  • Bindings (28 actions)                    │
│  • Phase orchestrator (_run)                │
│  • Background task tracker (_bg_tasks)      │
│  • State (DiscoveryRecord, session)         │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐    ┌─────────────────────┐
│   Widgets    │    │   Backend Bridge    │
│  (Reactive)  │◄──►│  (Graceful degrade) │
└──────────────┘    └─────────────────────┘
                            │
        ┌───────────────────┼───────────────┐
        ▼                   ▼               ▼
   ┌─────────┐      ┌────────────┐   ┌──────────┐
   │   LLM   │      │   Search   │   │  Verify  │
   │ Router  │      │  (Multi)   │   │ (Formal) │
   └─────────┘      └────────────┘   └──────────┘
```

## 3. Component Breakdown

### 3.1 `app.py` — The Orchestrator

| Element | Responsibility |
|---------|---------------|
| `C4TUIv7` | Main `textual.app.App` subclass. Owns the event loop, widget tree, and global state. |
| `_run(mode)` | 7-phase async pipeline entry. Validates → executes phases A–G → renders results. |
| `_phase_a_* … _phase_g_* | Isolated async methods. Each handles one cognitive phase and catches its own exceptions. |
| `_bg(coro)` | Background task factory. Tracks all tasks in `_bg_tasks: set[asyncio.Task]` and auto-removes them on completion. |
| `_sanitize(text)` | Input sanitization: NFKC Unicode normalization, HTML tag stripping, control-char removal. Applied to every user query before it reaches the pipeline. |
| `action_toggle_chat()` | Boolean-flag driven chat panel toggle (replaces fragile `styles.height.value` inspection). |
| `on_button_pressed()` | Type-safe dispatch via `isinstance(ev.button, ModeButton)`. |

**Key design decision:** `_run()` was refactored from a single 200-line monolith into 7 discrete `_phase_*` methods. This makes unit testing, profiling, and fault isolation trivial.

### 3.2 `backend_bridge.py` — Unified Backend Layer

All TUI → backend traffic goes through this module. Every function follows the same contract:

1. **Rate-limit** (sliding window).
2. **Try** the primary backend path.
3. **Catch** exceptions, log, and return a safe default.

| Function | Backend | Graceful Default | Rate Limit |
|----------|---------|------------------|------------|
| `run_llm_router` | `LLMProviderRouter.chat()` → OpenRouter fallback | `""` | 10 / 60 s |
| `run_search` | `MultiSourceSearcher.search_all()` | `{"papers":[]}` | 5 / 60 s |
| `run_plugins` | `execute_plugin()` via `asyncio.to_thread` | `{}` | — |
| `run_verification` | Lean4 → Dafny → Hoare (with LLM→formal spec step) | `{}` | — |
| `run_simulation` | `NewtonSimulator` (gated by math keywords, 30 s timeout) | `{"status":"skipped"}` | — |
| `run_social_post` | Telegram, Mastodon, Discord | `[]` | 3 / 60 s |
| `run_news_feed` | `NewsAggregator.get_ticker_feed()` | `[]` | — |

**Key design decision:** `run_verification` now translates the natural-language topic into a formal specification via the LLM router *before* passing it to theorem provers. This fixes the historical semantic mismatch where verifiers received prose instead of code.

### 3.3 `widgets/` — Reactive UI Surface

| Widget | Role | Key Feature |
|--------|------|-------------|
| `V7Header` | Status bar (API health, discovery count, clock, news ticker) | 5-min feed cache, 5-s tick, non-blocking LLM check via `asyncio.to_thread` |
| `V7Input` | Query + mode buttons | `ModeButton` subclass for type-safe mode dispatch |
| `V7Pipeline` | 7-phase progress + narrative log | Real progress based on `elapsed / expected_duration` per phase (not fake `time % 15`) |
| `V7Result` | Metrics table, top-5 hypotheses/sources | `ResultViewModel` dataclass replaces 9 positional args |
| `V7C4Frame` | Interactive 3×3×3 cognitive grid | Click-to-select hitmap + keyboard navigation (Tab/Arrows) |
| `LivingCubeMascot` | Emotional ASCII companion | Reactive emotion states (`idle/thinking/happy/surprised`) |

### 3.4 `state.py` — Data Models

- `C4State` — 3×3×3 Z₃³ cognitive coordinate.
- `DiscoveryRecord` — Single discovery result (sources, hypotheses, quality, simulation, verification).
- `ResultViewModel` — DTO for `V7Result.show()`.
- `DataStore` — Persistent JSON session store (`~/.c4reqber/sessions.json`).

### 3.5 `screens/` — Modal Overlays

Splash, onboarding, dashboard, diagnostics, dissertation viewer, settings, fireworks (quality > 80), matrix rain, package installer.

## 4. Data Flow

```
User types problem + presses Ctrl+F (flash)
        │
        ▼
  _sanitize(input)  →  strip HTML, normalize unicode
        │
        ▼
  _run("flash")
    ├── _phase_a_framing   → run_plugins("A")      → complexity score
    ├── _phase_b_search    → run_search()          → sources (mocked/empty in flash)
    ├── _phase_c_gaps      → run_plugins("C")      → gap analysis
    ├── _phase_d_hypotheses → run_llm_router()     → "Flash" hypothesis
    ├── _phase_e_simulation → run_simulation()     → skipped (no math keywords)
    ├── _phase_f_verification → run_verification() → LLM→formal spec → verifier
    └── _phase_g_quality   → quality scoring
        │
        ▼
  V7Result.show(ResultViewModel(...))
        │
        ▼
  Header.update() + Mascot.set_emotion("happy")  [if score > 80]
```

## 5. Testing Strategy

### 5.1 Layers

| Layer | Location | Count | Focus |
|-------|----------|-------|-------|
| Widget unit | `tests/tui/v7/test_widgets.py` | 7 | Compose, navigation, timer guards, emotions |
| App integration | `tests/tui/v7/test_app.py` | 6 | Actions, cancel, quit, validation |
| Mocked backend | `tests/tui/v7/test_app_mocked.py` | 2 | Full pipeline with 100 % mocked backends |
| Error injection | `tests/tui/v7/test_errors.py` | 3 | ConnectionError, TimeoutError, CancelledError |
| Input sanitization | `tests/tui/v7/test_sanitize.py` | 4 | HTML, control chars, Unicode, whitespace |
| Backend integration | `tests/integration/test_tui_backend.py` | 6 | Graceful degradation of each bridge function |
| Backend load | `tests/integration/test_load_backend.py` | 3 | 100 LLM calls, 100 simulations, memory < 100 MB |
| Rate limits | `tests/integration/test_rate_limit.py` | 3 | Sliding-window enforcement |

### 5.2 Key Testing Patterns

- **Mock at the bridge boundary**, not inside `app.py`. Because `app.py` does `from .backend_bridge import fn` locally inside async methods, `patch("src.tui.v7.backend_bridge.run_*")` works reliably.
- **Reset global state** (`RateLimiter.reset()`, `_bg_tasks`) via `autouse` fixtures to keep tests hermetic.
- **Assert on `_bg_tasks` state**, not just return values, to catch background leaks.

## 6. Security & Resilience

| Concern | Mitigation |
|---------|------------|
| Input injection | `_sanitize()` strips HTML, decodes HTML entities, normalizes Unicode, removes control characters, blocks role tags, neutralizes bidirectional overrides |
| Prompt injection | Nonce delimiters (`<user_query nonce=…>`), LaTeX escaping, `html.unescape` for encoded entities |
| Length overflow | Hard block at > 500 chars in `_run()` |
| Rate abuse | Per-operation sliding-window limiters (LLM 10/60s, search 5/60s, social 3/60s) |
| SSRF | Paper IDs validated against `^[A-Za-z0-9_-]+$`; URL-encode + disable redirects |
| Path traversal | `validate_path()` ensures paths stay within `~/.c4reqber`; temp files validated via `validate_temp_path()` |
| Subprocess injection | `safe_subprocess` denylist expanded: `; & | $> < \` $() \n $ \ * ? ~ {} ! # % ^` |
| Symlink attacks | `path.is_symlink()` checked after `resolve()` in `safe_subprocess` |
| Backend outage | Every bridge function has `try/except` + safe default |
| JWT secret | `secrets.token_hex(32)` instead of hardcoded string |
| Signal safety | `SIGINT` / `SIGTERM` handlers cancel background tasks and flush store |

## 7. Performance Notes

- **Header** — news feed cached for 5 min; LLM status cached for 60 s; both queried via `asyncio.to_thread` to avoid blocking the event loop.
- **Pipeline** — progress bars use per-phase `expected_duration` (A=2s, B=5s, C=3s, D=10s, E=5s, F=3s, G=2s) rather than an arbitrary modulo animation.
- **Plugins** — executed in parallel via `asyncio.gather(*[asyncio.to_thread(...)])`.
- **Simulation** — 30-second hard timeout via `asyncio.wait_for`.

## 8. Extension Points

- **New backend** — Add a function to `backend_bridge.py` following the `try/except/return-default` contract.
- **New pipeline phase** — Insert a `_phase_*` method in `app.py` and add a `ProgressBar` + `Label` in `V7Pipeline.P`.
- **New widget** — Subclass `textual.widgets.Static` or `textual.containers.Vertical`, add it to `compose()`, and reference it via `#id` in CSS.
- **New mode** — Add to `MODE_LIST` in `constants.py`, create an `action_run_*`, and wire it in `ModeButton` + `on_button_pressed`.
