# TURBO-CDI Ghost in the Shell TUI

Futuristic Terminal User Interface inspired by Ghost in the Shell universe.

![Ghost in the Shell aesthetic](https://img.shields.io/badge/aesthetic-cyberpunk-4ECDC4)
![Terminal UI](https://img.shields.io/badge/interface-TUI-FF6B6B)

## Design Philosophy

Following the **Council of Geniuses** synthesis:

- **Dieter Rams**: "Less but better" — minimal, functional aesthetic
- **Edward Tufte**: Maximum data-ink ratio — dense information display
- **M.C. Escher**: Spatial visualizations in constrained 2D terminal space
- **Ken Thompson**: Unix philosophy — composable, focused components
- **Daniel Kahneman**: System 1 intuition — spatial stability, consistent patterns

## Features

### Visualizations
- **C4 State Grid** — ASCII representation of 27 cognitive states (Z₃³)
- **Discovery Workflow** — Real-time progress with 7 stages
- **Confidence Sparklines** — Braille-based density visualization
- **Hypothesis Cards** — Compact, information-dense displays

### Interaction
- **Vim-like navigation** — `hjkl` for power users
- **Mouse support** — Clickable elements for discoverability
- **Keyboard shortcuts** — `/` for command palette
- **Real-time updates** — WebSocket integration for live data

## Quick Start

```bash
# Install dependencies
pip install textual

# Run the TUI
python src/tui/ghost_tui.py
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `d` | Focus Discovery |
| `c` | Focus C4 |
| `?` | Show help |
| `Tab` | Next element |
| `Enter` | Activate button |

## Architecture

```
GhostTUI (App)
├── GhostHeader (status bar)
├── Main Container
│   ├── DiscoveryWorkflow (7-stage progress)
│   ├── C4Visualizer (27-state grid)
│   └── HypothesisList (results)
└── Footer (shortcuts)
```

## Color Scheme

```python
# Dark theme (Ghost in the Shell)
background = "#0f0f1a"      # Deep void
primary    = "#4ECDC4"      # Cyan accent
secondary  = "#FF6B6B"      # Coral alert
accent     = "#FFE66D"      # Yellow highlight
success    = "#2ecc71"      # Green status
surface    = "#1a1a2e"      # Card background
```

## Visual Language

### Symbols
- `◈` — Primary action / C4
- `◉` — Status indicator / TRIZ
- `●` — Complete / Active
- `○` — Pending
- `◔` — Clock / Time

### Braille Patterns
For high-density sparklines:
```
⣀ ⡠ ⡄ ⡆ ⡇ ⣇ ⣏ ⣟ ⣿
```
4x density vs standard block characters.

## Future Enhancements

- [ ] Force-directed graph visualization
- [ ] Real-time WebSocket data
- [ ] Customizable color schemes
- [ ] Vim-mode command palette
- [ ] Multi-panel layouts

## References

- **Textual**: https://textual.textualize.io/
- **Ghost in the Shell**: 1995 anime cyberpunk aesthetic
- **TUIs of the future**: https://github.com/rothgar/awesome-tuis

## License

MIT
