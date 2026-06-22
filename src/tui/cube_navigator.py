# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from typing import Callable

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class InteractiveCube:
    """Clickable ASCII cube for C4 state navigation."""

    LAYER_COLORS = {1: "cyan", 2: "yellow", 3: "magenta"}
    LAYER_LABELS = {1: "T (Time)", 2: "S (Scale)", 3: "A (Agency)"}
    DIM_LABELS = {
        (0, 0): ("Past", "Concrete", "Self"),
        (1, 0): ("Past", "Concrete", "Other"),
        (2, 0): ("Past", "Concrete", "System"),
        (0, 1): ("Past", "Abstract", "Self"),
        (1, 1): ("Past", "Abstract", "Other"),
        (2, 1): ("Past", "Abstract", "System"),
        (0, 2): ("Past", "Meta", "Self"),
        (1, 2): ("Past", "Meta", "Other"),
        (2, 2): ("Past", "Meta", "System"),
        (0, 3): ("Present", "Concrete", "Self"),
        (1, 3): ("Present", "Concrete", "Other"),
        (2, 3): ("Present", "Concrete", "System"),
    }

    def __init__(self, on_click: Callable | None = None) -> None:
        self._state = (1, 1, 1)  # default: Present:Abstract:Other
        self._active_layer = 1
        self._on_click = on_click
        self._selected_cell: tuple[int, int, int] | None = None

    @property
    def state(self) -> tuple[int, int, int]:
        return self._state

    def navigate(self, axis: str, delta: int) -> None:
        """Navigate."""
        t, s, a = self._state
        if axis == "T":
            t = (t + delta) % 3
        elif axis == "S":
            s = (s + delta) % 3
        elif axis == "A":
            a = (a + delta) % 3
        self._state = (t, s, a)
        if self._on_click:
            self._on_click(self._state)

    def click_cell(self, t: int, s: int, a: int) -> None:
        """Click cell."""
        self._state = (t, s, a)
        self._selected_cell = (t, s, a)
        if self._on_click:
            self._on_click(self._state)

    def render(self) -> Panel:
        """Render."""
        t, s, a = self._state
        grid = Table.grid(padding=(0, 1))
        for t_val in range(3):
            row: list[Text] = []
            for a_val in range(3):
                cell_active = (t_val == t) and (s == 1)  # simplified: T-axis face
                sym = "■" if cell_active else "·"
                if cell_active and self._selected_cell == (t_val, 1, a_val):
                    sym = "◆"
                color = {0: "cyan", 1: "yellow", 2: "magenta"}.get(a_val, "white")
                row.append(Text(sym, style=f"bold {color}" if cell_active else f"dim {color}"))
            grid.add_row(*row)
        name = self.state_name
        nav = "[T/S/A] +/- navigate | [R]eset | [Q]uit cube"
        return Panel(grid, title=f"C4: {name}", subtitle=nav, border_style="cyan")

    @property
    def state_name(self) -> str:
        """State name."""
        t, s, a = self._state
        t_names = {0: "Past", 1: "Present", 2: "Future"}
        s_names = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        a_names = {0: "Self", 1: "Other", 2: "System"}
        return f"{t_names[t]}:{s_names[s]}:{a_names[a]}"
