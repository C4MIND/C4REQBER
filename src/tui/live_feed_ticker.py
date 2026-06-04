# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""TUI Live Feed Ticker — scrolling problems + hypotheses in terminal."""
from __future__ import annotations

import time

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from src.intel.live_feed import Hypothesis, get_live_feed
from src.pipeline.hil_pipeline import HILDiscoveryPipeline, run_hil_pipeline


class LiveFeedTicker(Static):
    """Dual-line scrolling ticker: UNSOLVED PROBLEMS (top) + RESEARCH HYPOTHESES (bottom)."""

    def __init__(self) -> None:
        super().__init__("")
        self._feed = get_live_feed()
        self._offset = 0
        self._last_update = time.time()

    def on_mount(self) -> None:
        self.set_interval(3.0, self._tick)

    def _tick(self) -> None:
        self._offset = (self._offset + 1) % max(len(self._feed.problems), 1)
        self.refresh()

    def render(self) -> Panel:
        """Render."""
        problems = self._feed.problems
        hypotheses = self._feed.hypotheses

        lines: list[Text] = []

        # Line 1: Problems ticker
        if problems:
            line1 = Text()
            line1.append("🔴 UNSOLVED ", style="bold red")
            p = problems[self._offset % len(problems)]
            line1.append(p.title[:80], style="cyan")
            line1.append(f"  [{p.source}] {p.age_minutes:.0f}m", style="dim")
            lines.append(line1)
        else:
            lines.append(Text("🔴 UNSOLVED [italic dim]collecting data...[/]", style="bold red"))

        # Line 2: Hypotheses ticker
        if hypotheses:
            line2 = Text()
            line2.append("💡 HYPOTHESIS ", style="bold yellow")
            h = hypotheses[self._offset % len(hypotheses)]
            line2.append(h.title[:80], style="green")
            line2.append(f"  conf:{h.confidence:.0%}", style="dim")
            lines.append(line2)
        else:
            lines.append(Text("💡 HYPOTHESIS [italic dim]generating from anomalies...[/]", style="bold yellow"))

        return Panel(
            Text("\n").join(lines),
            title="[bold]Live Intelligence Feed[/]",
            subtitle=f"{len(problems)} problems · {len(hypotheses)} hypotheses",
            border_style="#e040fb",
            padding=(0, 1),
        )


class HypothesisRunner:
    """Quick-launch: take a feed hypothesis → spawn blast turbo pipeline."""

    @staticmethod
    def run(hypothesis: Hypothesis) -> str:
        """Run."""
        from src.pipeline.config import PipelineConfig
        cfg = PipelineConfig()

        topic = hypothesis.title
        run_hil_pipeline(topic, config=cfg)
        return f"Pipeline started for: {topic}"
