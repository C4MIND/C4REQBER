# C4REQBER Terminal User Interface

The official TUI for C4REQBER — a keyboard-driven, themeable, i18n-aware terminal interface for cognitive discovery.

## Current Version: v9 (Go)

TUI v9 is built in **Go** using Bubble Tea v2 and Lipgloss. It is the supported, feed-driven terminal cockpit.

- **Location**: `src/tui/v9/`
- **Binary**: `c4tui-v9`
- **Build**: `make -C src/tui/v9 build`
- **Launch**: `blast tui`

## Quick Start

```bash
# Build
make -C src/tui/v9 build

# Run
blast tui

# Demo mode (no backend required)
blast tui --demo --story=crispr
```

## Features

- **Feed-driven discovery pipeline** with real-time SSE updates
- **Inline cards** for hypotheses, papers, simulations, and verification
- **7 languages** with complete translation parity
- **7 color profiles**, including solarized dark
- **Adaptive layouts** for narrow through wide terminals
- **Command palette, debug overlay, and capability browser**
- **Persistent feed** with resume on launch

## Architecture

See [`v9/README.md`](v9/README.md) and [`v9/ARCHITECTURE.md`](v9/ARCHITECTURE.md).

## Legacy

The retired v6/v7 Python interfaces and v8 parallel Go app have been removed. Python launchers delegate to TUI v9.

## License

Dual-licensed under AGPL-3.0 and Commercial License. See project root.
