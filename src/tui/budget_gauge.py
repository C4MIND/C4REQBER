# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from rich.console import Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.text import Text
from textual.widgets import Static

from src.llm.depth_router import DepthBasedRouter


class BudgetGauge(Static):
    """Shows estimated cost for current pipeline run."""

    def __init__(self) -> None:
        super().__init__("")
        self._cost: float = 0.0
        self._budget: str = "balanced"
        self._max_cost: float = 1.0

    def set_budget(self, stage: int, budget: str = "balanced") -> None:
        """Update."""
        self._budget = budget
        depths = [DepthBasedRouter.STAGE_TO_DEPTH.get(s, 2) for s in range(1, stage + 1)]
        self._cost = DepthBasedRouter.estimate_cost(depths, budget)

    def render(self) -> Panel:
        """Render."""
        pct = min(1.0, self._cost / self._max_cost)
        bar = ProgressBar(total=100, completed=int(pct * 100), width=20)
        color = "green" if self._cost < 0.10 else "yellow" if self._cost < 0.50 else "red"
        label = Text()
        label.append("Budget: ", style="dim")
        label.append(f"${self._cost:.4f}", style=f"bold {color}")
        label.append(f"  [{self._budget}]", style="dim")
        return Panel(Group(label, bar), title="Cost", border_style="cyan")
