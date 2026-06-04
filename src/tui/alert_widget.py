# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from collections import deque

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from src.c4.alert_taxonomy import AlertClassifier, C4Alert


class AlertPanel(Static):
    """Shows recent C4 alerts with severity color coding."""

    def __init__(self, max_alerts: int = 5) -> None:
        super().__init__("")
        self._alerts: deque[C4Alert] = deque(maxlen=max_alerts)
        self._max = max_alerts

    def add(self, message: str, source: str = "pipeline") -> None:
        """Add."""
        alert = AlertClassifier.classify(message, source)
        self._alerts.appendleft(alert)

    def render(self) -> Panel:
        """Render."""
        self._prune_expired()
        if not self._alerts:
            return Panel(Text("No alerts", style="dim"), title="Alerts", border_style="cyan")
        lines = []
        for alert in list(self._alerts)[: self._max]:
            age = time.time() - alert.timestamp
            age_str = f"{age:.0f}s ago" if age < 60 else f"{age/60:.0f}m ago"
            line = Text()
            line.append(f"[{alert.severity}] ", style=alert.color)
            line.append(alert.title, style="bold")
            line.append(f"  {age_str}", style="dim")
            lines.append(line)
        return Panel(Text("\n").join(lines), title="Alerts", border_style="cyan")

    def _prune_expired(self) -> None:
        now = time.time()
        self._alerts = deque(
            (a for a in self._alerts if now - a.timestamp < a.ttl),
            maxlen=self._max,
        )
