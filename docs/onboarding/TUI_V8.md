# TUI v8 Setup Guide — C4REQBER v5.6.0

> **Last updated:** 2026-06-03 | **Target:** Developers building the Go TUI

TUI v8 is a [Bubble Tea](https://github.com/charmbracelet/bubbletea) terminal interface written in Go. It connects to the Python backend API and provides an interactive discovery experience with a 7-phase pipeline, C4 cognitive grid, and the cube mascot.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Go | 1.22+ | [go.dev/dl](https://go.dev/dl/) |
| Python backend | Running | See [INSTALL.md](../../INSTALL.md) |

---

## Build

```bash
cd src/tui/v8

# Download dependencies
go mod download

# Build binary
go build -o c4tui-v8 .

# Or with race detector (development)
go build -race -o c4tui-v8 .
```

---

## Run

```bash
# Default: connects to http://localhost:8000
./c4tui-v8

# Custom API endpoint
./c4tui-v8 --api http://localhost:8000

# Russian language + Matrix theme
./c4tui-v8 --lang ru --theme matrix
```

**Before running TUI v8, ensure the Python backend is running:**

```bash
# Terminal 1: start backend
cd /path/to/c4reqber
source .venv314/bin/activate
python -m src.api.server

# Terminal 2: start TUI
cd src/tui/v8
./c4tui-v8
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Enter` | Start pipeline |
| `Ctrl+C` / `q` | Quit |
| `Esc` | Cancel running pipeline |
| `Tab` | Cycle C4 axis (Time → Scale → Agency) |
| `←` / `→` | Move along active C4 axis |
| `↑` / `↓` | Move along active C4 axis (inverted) |
| `Shift+↑` / `Shift+↓` | Move Agency axis |
| `Shift+D` | Dashboard overlay |
| `Shift+P` | Palette overlay |
| `Shift+H` | Cycle theme (Dark → Matrix → Paper) |
| `Shift+L` | Cycle language (EN → RU → ZH → JA → DE → AR → HI) |
| `Shift+E` | Export results |
| `Shift+O` | Dissertation overlay |
| `Shift+Y` | History overlay |
| `Shift+K` | Knowledge graph overlay |
| `Shift+X` | Diagnostic overlay |
| `Shift+B` | Bibliography overlay |
| `Shift+A` | Agenda overlay |
| `Shift+V` | Provider overlay |
| `Shift+N` | Social sharing overlay |
| `Shift+G` | GPU monitor overlay |
| `Shift+I` | Package installer overlay |
| `Ctrl+F` | Flash mode |
| `Ctrl+D` | Discover mode |
| `Ctrl+T` | Turbo mode |
| `Ctrl+Shift+T` | TurboFactory mode |
| `Ctrl+S` | Search mode |
| `Ctrl+V` | Verify mode |
| `F2` | Toggle chat panel |
| `?` | Help overlay |

---

## Themes

| Theme | Style | Best for |
|-------|-------|----------|
| **Dark** | Purple/cyan on dark | Default, low light |
| **Matrix** | Green on black | Retro terminal feel |
| **Paper** | Blue/black on light | Bright environments |

Switch with `Shift+H`.

---

## Languages

7 languages supported with full i18n:
- English (en)
- Russian (ru)
- Chinese (zh)
- Japanese (ja)
- German (de)
- Arabic (ar)
- Hindi (hi)

Switch with `Shift+L`.

---

## Architecture

```
c4tui/
├── main.go              # App orchestrator (splash → TUI transition)
├── model.go             # Core Bubble Tea model
├── update.go            # Message dispatch (keys, backend, pipeline)
├── view.go              # Layout composition + status bar
├── layout.go            # Responsive layout engine (3 breakpoints)
├── backend/             # HTTP client, SSE, rate limiter, bridge
├── config/              # Theme & layout config
├── internal/            # i18n (52 keys × 7 languages), mascot memory, store
├── screens/             # Overlay screens (export, dashboard, palette, etc.)
├── splash/              # Boot splash with morph animation
├── styles/              # Theme system (Dark/Matrix/Paper) + cached styles
└── widgets/             # Header, chat, C4 grid, mascot, pipeline, result, input, toast
```

---

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

# Static analysis (requires staticcheck)
staticcheck ./...
```

**Quality gates:**
- `go vet` — must be clean
- `staticcheck ./...` — must be clean
- `gofmt -l .` — must return empty

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `connection refused` | Backend not running | Start `python -m src.api.server` first |
| `404 Not Found` | Wrong API URL | Use `--api http://localhost:8000` |
| Black screen | Terminal too small | Resize to at least 80×24 |
| Mascot not animating | `IdleTickMsg` blocked | Check that backend SSE is connected |
| Build fails | Go version < 1.22 | Upgrade Go |
| `module not found` | Outside GOPATH | Run `go mod download` inside `src/tui/v8` |

---

## Differences from Python TUI (`blast tui`)

| | Python TUI (`blast tui`) | Go TUI v8 (`c4tui-v8`) |
|---|---|---|
| **Framework** | Textual (Python) | Bubble Tea (Go) |
| **Command** | `blast tui` | `./c4tui-v8` |
| **Slash commands** | `/models`, `/council`, etc. | None (keyboard shortcuts only) |
| **Mascot** | 8-bit cube | 3-frame ASCII cube |
| **Themes** | Custom | Dark / Matrix / Paper |
| **Pipeline** | Integrated | Via backend API |
| **Target** | Quick local use | Rich interactive experience |

Both connect to the same Python backend. Use whichever you prefer.
