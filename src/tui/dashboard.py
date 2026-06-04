# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from typing import cast

from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Static


class PathNavigator(Static):
    """Left panel: 24 scientist paths with C4 state badges."""

    PATHS = [
        ("Curie", 1, "☢"), ("Einstein", 1, "⚛"), ("Newton", 1, "🍎"), ("Darwin", 1, "🧬"),
        ("Turing", 2, "💻"), ("von Neumann", 2, "🎲"), ("Gödel", 2, "🔣"), ("Shannon", 2, "📡"),
        ("Feynman", 1, "🎨"), ("Hawking", 1, "🕳"), ("Poincaré", 2, "🔮"), ("Lovelace", 2, "👩‍💻"),
        ("Karikó", 1, "💉"), ("Doudna", 1, "🧪"), ("Baker", 2, "🫧"), ("Hassabis", 2, "🧩"),
        ("Hinton", 2, "🤖"), ("Moser", 1, "🧠"), ("Curie:Marie", 3, "⚡"), ("Bohr", 3, "🌀"),
        ("Maxwell", 3, "🌐"), ("Planck", 3, "💡"), ("Dirac", 3, "🌀"), ("Wheeler", 3, "🔭"),
    ]

    def __init__(self, active_layer: int = 1) -> None:
        super().__init__("")
        self.active_layer = active_layer

    def render(self) -> Panel:
        """Render."""
        lines = []
        for name, layer, icon in self.PATHS:
            style = "bold" if layer == self.active_layer else "dim"
            color = {1: "cyan", 2: "yellow", 3: "magenta"}.get(layer, "white")
            line = Text()
            line.append(f"  {icon} ", style=style)
            line.append(f"{name:<14}", style=f"{style} {color}")
            lines.append(line)
        return Panel(Text("\n").join(lines), title="Scientist Paths", border_style="cyan")


class MainWorkspace(Static):
    """Center panel: analysis output with C4-stratified blocks."""

    def __init__(self) -> None:
        super().__init__("")
        self.content = "(no analysis running)"

    def update_content(self, text: str) -> None:
        self.content = text

    def render(self) -> Panel:
        return Panel(cast(str, self.content), title="Workspace", border_style="yellow")


class C4DashboardScreen(Screen):
    """Tri-panel dashboard: 20/55/25 split layout."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield PathNavigator()
            yield MainWorkspace()
