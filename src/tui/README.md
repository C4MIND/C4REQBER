# C4REQBER Terminal User Interface

The official TUI for C4REQBER — a keyboard-driven, themeable, i18n-aware terminal interface for cognitive discovery.

## Current Version: v8 (Go)

TUI v8 is built in **Go** using [Bubble Tea](https://github.com/charmbracelet/bubbletea) and [Lipgloss](https://github.com/charmbracelet/lipgloss). It replaces the previous Python/Textual stack (v6/v7) with a statically compiled, allocation-optimized implementation.

- **Location**: `src/tui/v8/`
- **Binary**: `c4tui-v8`
- **Build**: `cd src/tui/v8 && go build -o c4tui-v8 .`
- **Launch**: `./launch_tui_v8.sh` or `cd src/tui/v8 && ./c4tui-v8`

## Quick Start

```bash
# Build
cd src/tui/v8
go build -o c4tui-v8 .

# Run
./c4tui-v8

# With options
./c4tui-v8 --api http://localhost:8000 --lang ru --theme matrix
```

## Features

- **7-phase discovery pipeline** with real-time SSE updates
- **3×3×3 C4 Cognitive Cube** — interactive navigation with theme-aware colors
- **7 languages** — cycle with `L`
- **3 themes** — Dark, Matrix, Paper — cycle with `T`
- **Responsive layout** — adapts to any terminal size
- **Quantum mascot** — animated companion cube
- **Export** — Markdown, JSON, HTML, BibTeX

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit query |
| `Tab` / `←→↑↓` | Navigate C4 cube |
| `Shift+↑↓` | Agency axis |
| `Ctrl+Enter` | Start pipeline |
| `F1`–`F12` | Overlays (help, chat, dashboard, export, etc.) |
| `T` | Cycle theme |
| `L` | Cycle language |
| `Esc` | Close overlay / quit |

## Architecture

See [`IMPLEMENTATION.md`](IMPLEMENTATION.md) for the full architecture deep-dive.

## Legacy

v6 and v7 (Python/Textual) have been removed. Python shims in `src/tui/__init__.py`, `app.py`, and `entry.py` now delegate to the Go binary.

## License

Dual-licensed under AGPL-3.0 and Commercial License. See project root.
