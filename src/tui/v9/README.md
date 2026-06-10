# TUI v9 "The Cockpit"

Single-screen terminal UI for c4reqber — feed-driven, real-time discovery.

## Build & Run

```bash
make build       # builds bin/c4tui-v9
make test        # go test ./...
make snapshot    # update golden snapshots
./bin/c4tui-v9  # run (requires backend on http://127.0.0.1:8000)
```

## Architecture

4-region single layout (no overlays):
- **Header** (1 line) — `● C4REQBER v9  F⟨1,1,0⟩  🇬🇧  DeepSeek  $0.00`
- **Feed** (flex) — scrollable card list (phase / hypothesis / paper / code / error)
- **Input** (3 lines) — bubbles textarea, Enter submit
- **Footer** (1 line) — `▶ READY · $0.00 · [Enter] Run  [?] Help  [Ctrl+C] Quit`

## Files

| Path | Purpose |
|---|---|
| `cmd/c4tui-v9/main.go` | Entry point |
| `update.go` | Single Update method |
| `view.go` | 4-region composition |
| `model.go` | App state struct |
| `layout.go` | Region geometry |
| `internal/api.go` | Backend HTTP client |
| `widgets/feed.go` | Card list + viewport |
| `widgets/header.go` | 1-line header |
| `widgets/footer.go` | Narrative status footer |
| `widgets/inputbar.go` | Wrapped textarea |
| `widgets/card_*.go` | 5 card types |
| `i18n/{en,ru}.toml` | Translations |
| `tests/snapshots/*` | Golden output tests |

## Status

Phase 0+ scaffold. See `/Users/figuramax/LocalProjects/C4REQBER/MiniM-M3-Artefacts/tui-v9-cockpit-plan-v3.md`.
