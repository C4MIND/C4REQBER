# C4REQBER TUI v8 — Implementation Summary

## Overview

TUI v8 is a complete rewrite from Python/Textual to **Go + Bubble Tea + Lipgloss**. It replaces the previous v6/v7 Python stack with a statically compiled, race-free, allocation-optimized terminal interface.

## Technology Stack

```
Language:     Go 1.26
Framework:    Bubble Tea v1.13.0 (Elm architecture for TUI)
Styling:      Lipgloss v1.1.0 + Bubbles v1.0.0
Module:       c4tui
Binaries:     c4tui, c4tui-v8
```

## Architecture

### Core Loop (Bubble Tea)

```
Model → Update(msg) → (Model, Cmd)
   ↓
View(model) → string (frame)
```

All state lives in a single `model` struct. Messages flow through `update.go` and are routed to overlays first, then to the main model.

### Packages

| Package | Purpose | Key Files |
|---------|---------|-----------|
| `backend` | HTTP client, SSE streaming, rate limiting, bridge | `client.go`, `sse.go`, `bridge.go`, `rate_limiter.go` |
| `config` | Theme & layout constants | `config.go` |
| `internal` | i18n, session store, mascot memory, text utils | `i18n.go`, `store.go`, `mascot_memory.go`, `sanitize.go` |
| `screens` | Overlay screens (export, dashboard, palette, etc.) | `export.go`, `dashboard.go`, `palette.go`, `dissertation.go` … |
| `splash` | Boot splash with ASCII morph animation | `splash.go`, `art.go`, `ascii_art.go` |
| `styles` | Theme system + cached style helpers | `theme.go` |
| `widgets` | Reusable UI components | `header.go`, `chat.go`, `c4grid.go`, `mascot.go`, `pipeline.go`, `result.go`, `inputbar.go`, `toast.go`, `help.go` |

### Responsive Layout Engine

Breakpoints:
- `veryNarrow` (< 70 cols) → single-column stack
- `narrow` (< 90 cols) → two-column layout
- `wide` (≥ 90 cols) → three-column layout (28/32/40 split)
- `short` (< 24 rows) → collapses help/chat, hides mascot

`layout.go` computes all dimensions in a single pass. `splitHeight()` avoids sequential clamp bugs.

## Performance Optimizations

| Optimization | Location | Impact |
|--------------|----------|--------|
| Cached `lipgloss.Style` vars | `styles/theme.go` | ~17 `NewStyle()` calls eliminated per frame |
| Memoized header separator | `view.go` | Zero rebuild when width unchanged |
| C4 grid view cache | `widgets/c4grid.go` | Skips rebuild when state/dims unchanged |
| Stack-allocated grids | `widgets/mascot.go` | `[7][7]rune` instead of `[][]rune` |
| Pre-allocated slices | `widgets/pipeline.go` | `make([]string, 0, 20)` |
| Cached `elapsedStr` | `widgets/pipeline.go` | No `time.Since` formatting in `View()` |
| Cached `TimeEmoji` | `widgets/header.go` | No `time.Now()` syscall every frame |
| `expiresAt` instead of `time.Since` | `widgets/toast.go` | Single comparison |
| Manual float→string | `widgets/pipeline.go` | `strconv.FormatFloat` instead of `fmt.Sprintf` |

**Total: ~150+ heap allocations per frame eliminated.**

## Internationalization

- 55 keys across 7 languages
- `internal.T(key)` with fallback chain: active → EN → key
- Languages: EN, RU, ZH, JA, DE, AR, HI
- Cycle with `L` key

## Theme System

Three built-in themes protected by `sync.RWMutex`:
- **Dark** — deep void `#0f0f1e`, cyan accent
- **Matrix** — black/green terminal aesthetic
- **Paper** — light theme for daytime use

`syncColorsUnlocked()` rebuilds ~17 cached styles atomically on theme change.

## Safety & Reliability

- `recover()` in async goroutines (store save, mascot save, SSE scanner)
- Graceful SIGINT shutdown (`signals.go`) — flushes store before exit
- Rate limiter with `Acquire()` / `AcquireN()`
- HTTP retry limited to **idempotent methods only**
- Chat clamp: max 2000 runes/line, max 500 lines
- UTF-8 safe truncation in `widgets/chat.go`

## Testing

```
Total coverage: 38.6%
splash:   76.3%
styles:   65.7%
widgets:  51.2%
backend:  46.6%
internal: ~40%
screens:  ~4.5% (overlays)
```

All tests pass with `-race`. Build gate: `go test ./...` must pass before binary rebuild.

## Build & Run

```bash
cd src/tui/v8
go build -o c4tui-v8 .
./c4tui-v8 --api http://localhost:8000 --lang ru --theme matrix
```

## Migration from v7

v6/v7 (Python/Textual) have been **removed**. The remaining Python shims in `src/tui/` (`__init__.py`, `app.py`, `entry.py`) now locate and execute the Go binary.

```
Removed:
  src/tui/v7/               (entire Python TUI v7)
  src/tui/app_v6*.py
  src/tui/app_v7.py
  tests/tui/v7/
  tests/integration/test_tui_backend.py
  tests/integration/test_rate_limit.py
  tests/integration/test_load_backend.py
```

## Status

✅ Production-ready — 21 audit-polish rounds completed  
✅ Race-clean  
✅ `go vet` clean  
✅ `gofmt` clean  
✅ Both binaries build successfully
