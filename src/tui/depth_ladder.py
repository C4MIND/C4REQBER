# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.text import Text
from textual.widgets import Static


class DepthLadder(Static):
    """Three-rung ladder: C1 Discovery → C2 Formalization → C3 Verification."""

    LAYERS = [
        (1, "Discovery", "cyan"),
        (2, "Formalization", "yellow"),
        (3, "Verification", "magenta"),
    ]

    def __init__(self) -> None:
        super().__init__("")
        self._progress: dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0}

    def update_layer(self, layer: int, percent: float) -> None:
        self._progress[layer] = min(1.0, max(0.0, percent))

    def set_from_pipeline_step(self, step: int, total: int = 12) -> None:
        """Set from pipeline step."""
        ratio = step / total
        self._progress[1] = min(1.0, ratio / 0.33)  # Steps 1-4
        self._progress[2] = min(1.0, max(0.0, (ratio - 0.33) / 0.33))  # Steps 5-8
        self._progress[3] = min(1.0, max(0.0, (ratio - 0.66) / 0.34))  # Steps 9-12

    def render(self) -> Panel:
        """Render."""
        lines: list[Any] = []
        for layer, name, color in self.LAYERS:
            pct = self._progress[layer]
            bar = ProgressBar(total=100, completed=int(pct * 100), width=20)
            label = Text()
            label.append(f"C{layer} {name:<16}", style=color)
            label.append(f" {int(pct * 100):>3}%", style="bold")
            if pct >= 1.0:
                label.append(" ✓", style="bold green")
            lines.append(label)
            lines.append(bar)
        return Panel(Group(*lines), title="Depth Ladder", border_style="cyan")
