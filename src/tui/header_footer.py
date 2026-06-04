"""
TUI: Header and Footer
Header with mode/tokens/LLM/GPU info. Footer with keyboard shortcuts.
"""
from __future__ import annotations

from datetime import datetime

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def make_header(mode: str, token_text: str, llm_text: str, gpu_text: str) -> Panel:
    """Header: name + mode + time + tokens + LLM status + GPU."""
    mode_name = {
        "discover": "🔬 Discover",
        "invent": "🔧 Invent",
        "transform": "🌌 Transform",
    }
    now = datetime.now().strftime("%H:%M:%S")

    header = Table.grid(padding=(0, 2))
    header.add_column(justify="left")
    header.add_column(justify="right")
    header.add_row(
        Text.assemble(
            (" C4REQBER ", "bold white on #0a0a0f"),
            (" v5.4.0 ", "dim"),
        ),
        Text(f"{mode_name.get(mode, mode)} │ {token_text} │ {llm_text} │ {gpu_text} │ {now}", style="dim"),
    )
    return Panel(header, box=box.SIMPLE, border_style="#4ECDC4", padding=(0, 1))


def make_footer() -> Panel:
    """Footer: always-visible keyboard shortcuts bar — 20 keys."""
    shortcuts = Text("", style="bold")
    shortcuts.append("[Tab]", style="bold #4ECDC4")
    shortcuts.append(" Mode  ", style="dim")
    shortcuts.append("[Enter]", style="bold #4ECDC4")
    shortcuts.append(" Run  ", style="dim")
    shortcuts.append("[L]", style="bold #4ECDC4")
    shortcuts.append(" Lang  ", style="dim")
    shortcuts.append("[A]", style="bold #4ECDC4")
    shortcuts.append(" Alert  ", style="dim")
    shortcuts.append("[B]", style="bold #4ECDC4")
    shortcuts.append(" Budget  ", style="dim")
    shortcuts.append("[D]", style="bold #4ECDC4")
    shortcuts.append(" Depth  ", style="dim")
    shortcuts.append("[T]", style="bold #4ECDC4")
    shortcuts.append(" Article  ", style="dim")
    shortcuts.append("[R]", style="bold #4ECDC4")
    shortcuts.append(" Proof  ", style="dim")
    shortcuts.append("[G]", style="bold #4ECDC4")
    shortcuts.append(" GPU  ", style="dim")
    shortcuts.append("[M]", style="bold #4ECDC4")
    shortcuts.append(" Mod  ", style="dim")
    shortcuts.append("[P]", style="bold #4ECDC4")
    shortcuts.append(" Plugins  ", style="dim")
    shortcuts.append("[1-5]", style="bold #4ECDC4")
    shortcuts.append(" Export  ", style="dim")
    shortcuts.append("[Q]", style="bold #4ECDC4")
    shortcuts.append(" Quit", style="dim")

    return Panel(
        Align.center(shortcuts),
        box=box.SIMPLE,
        border_style="#4ECDC4",
        padding=(0, 1),
    )
