# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Thinking Indicator — animated cyberpunk gradient bar for TUI.

Inspired by Kilo's animated bar. Shows system thinking state with:
- Gradient colors cycling through the c4reqber palette
- Unicode block characters for smooth animation
- Speed varies based on activity intensity
- Mode-dependent colors (discovery=cyan, verification=magenta, etc.)
"""
from __future__ import annotations


def render_thinking_bar(frame: int, width: int = 30, phase: str = "idle", intensity: float = 0.5) -> str:
    """Render an animated thinking indicator bar.

    Args:
        frame: Animation frame counter (increment each render)
        width: Bar width in characters
        phase: Current pipeline phase (idle/searching/verifying/etc.)
        intensity: 0.0-1.0 animation speed/intensity
    """
    phase_colors = {
        "idle":    ["#06d6a0", "#06d6a0"],           # cyan
        "searching": ["#06d6a0", "#4ECDC4"],         # cyan → teal
        "analyzing": ["#4ECDC4", "#FFD93D"],         # teal → gold
        "generating": ["#FFD93D", "#e040fb"],        # gold → magenta
        "verifying": ["#e040fb", "#06d6a0"],         # magenta → cyan
        "complete":  ["#FFD93D", "#FFD93D"],         # gold
    }
    phase_colors.get(phase, phase_colors["idle"])

    chars = " ▏▎▍▌▋▊▉█"
    bar = []
    speed = 1.0 + intensity * 3.0

    for i in range(width):
        pos = (frame * speed + i * 2) % (width * 2)
        if pos > width:
            pos = width * 2 - pos
        idx = int(pos / width * 7) % 8
        bar.append(chars[idx])

    prefix = {
        "idle":       "[dim]◈[/dim]",
        "searching":  "[cyan]◈[/cyan]",
        "analyzing":  "[yellow]◈[/yellow]",
        "generating": "[bold yellow]◈[/bold yellow]",
        "verifying":  "[magenta]◈[/magenta]",
        "complete":   "[bold #FFD93D]◈[/bold #FFD93D]",
    }.get(phase, "[dim]◈[/dim]")

    return f" {prefix} [dim]{''.join(bar)}[/dim]"


def render_phase_label(phase: str) -> str:
    """Render current phase label with appropriate styling."""
    labels = {
        "idle":       "[dim]cognitive field stable[/dim]",
        "searching":  "[cyan]⟳ scanning knowledge graph[/cyan]",
        "analyzing":  "[yellow]⚡ gap analysis active[/yellow]",
        "generating": "[bold yellow]✦ hypothesis crystallization[/bold yellow]",
        "verifying":  "[magenta]⊢ formal verification[/magenta]",
        "complete":   "[bold #FFD93D]★ paradigm formed[/bold #FFD93D]",
    }
    return labels.get(phase, labels["idle"])


def thinking_spinner(frame: int) -> str:
    """A cyberpunk spinner that cycles through geometric shapes."""
    spinners = ["◈", "◇", "◆", "◈", "◇", "◆", "◉", "◎", "●", "◉", "◎", "●"]
    colors = ["#06d6a0", "#06d6a0", "#4ECDC4", "#FFD93D", "#FFD93D", "#e040fb",
              "#e040fb", "#e040fb", "#FFD93D", "#FFD93D", "#4ECDC4", "#06d6a0"]
    idx = frame % len(spinners)
    return f"[{colors[idx]}]{spinners[idx]}[/{colors[idx]}]"
