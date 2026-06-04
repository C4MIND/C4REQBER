# C4REQBER TUI v8

A fast, beautiful, keyboard-driven Terminal User Interface for C4REQBER — built in Go with [Bubble Tea](https://github.com/charmbracelet/bubbletea) and [Lipgloss](https://github.com/charmbracelet/lipgloss).

## Features

- **7-phase discovery pipeline** — real-time progress with narrative logs
- **3×3×3 C4 Cognitive Cube** — interactive ASCII visualization with theme-aware colors
- **55+ i18n keys** — 7 languages (EN, RU, ZH, JA, DE, AR, HI)
- **3 themes** — Dark, Matrix, Paper (cycle with `T`)
- **Responsive layout** — adapts to terminal width/height (wide/narrow/very-narrow breakpoints)
- **Companion cube** — 3-frame ASCII mascot with emotions & persistent memory
- **Export** — Markdown, JSON, HTML, BibTeX
- **~150 allocs/frame eliminated** — cached styles, memoized separators, pre-allocated slices

## Requirements

- Go 1.22+
- Backend API running (see project root `.env`)

## Build

```bash
cd src/tui/v8
go build -o c4tui-v8 .
```

Or from project root:

```bash
./launch_tui_v8.sh
```

## Usage

```bash
# Basic launch
./c4tui-v8

# Override API URL
./c4tui-v8 --api http://localhost:8000

# Start in Russian with Matrix theme
./c4tui-v8 --lang ru --theme matrix
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit query / activate button |
| `Tab` | Cycle C4 axis (Time → Scale → Agency) |
| `←` / `→` | Move along active C4 axis |
| `↑` / `↓` | Move along active C4 axis (inverted) |
| `Shift+↑` / `Shift+↓` | Move Agency axis |
| `Ctrl+Enter` | Start discovery pipeline |
| `F1` | Toggle help overlay |
| `F2` | Toggle chat panel |
| `F3` | Toggle C4 grid expanded view |
| `F4` | Pipeline overlay |
| `F5` | Dashboard overlay |
| `F6` | GPU monitor |
| `F7` | Social sharing |
| `F8` | Package installer |
| `F9` | Result / Dissertation overlay |
| `F10` | Export results |
| `F11` | Bibliography |
| `F12` | Settings / Palette |
| `T` | Cycle theme (Dark → Matrix → Paper) |
| `L` | Cycle language |
| `Ctrl+S` | Toggle sounds |
| `Ctrl+E` | Export chat history |
| `Esc` | Close overlay / quit if no overlay |

## Architecture

```
c4tui/
├── main.go           # App orchestrator (splash → TUI transition)
├── model.go          # Core model + overlay routing
├── update.go         # Message dispatch (window, backend, keys, input)
├── view.go           # Layout composition + status bar
├── layout.go         # Responsive layout engine
├── signals.go        # SIGINT graceful shutdown
├── backend/          # HTTP client, SSE, rate limiter, bridge
├── config/           # Theme & layout config
├── internal/         # i18n, session store, mascot memory, sanitization
├── screens/          # Overlay screens (export, dashboard, palette, etc.)
├── splash/           # Boot splash with morph animation
├── styles/           # Theme system (Dark/Matrix/Paper) + cached styles
└── widgets/          # Reusable widgets (header, chat, C4 grid, mascot, pipeline, result, input bar, toast)
```

## Development

```bash
# Run tests
go test ./...

# Run with race detector
go test -race ./...

# Format
gofmt -w .

# Vet
go vet ./...
```

## License

Dual-licensed under AGPL-3.0 (non-commercial) and Commercial License.
See `LICENSE` and `LICENSE-COMMERCIAL.md` in the project root.
