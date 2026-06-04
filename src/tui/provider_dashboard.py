# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""TUI Provider Dashboard — auto-detect and display all LLM providers.

Shows: local providers (MLX, LM Studio, Ollama) and cloud providers (OpenRouter, etc.)
with real-time status, load, and cost info.
"""
from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from src.pipeline.provider_coordinator import ProviderAwareCoordinator


class ProviderDashboard(Static):
    """Real-time provider status panel — auto-detects on show."""

    def __init__(self) -> None:
        super().__init__("")
        self._coordinator: ProviderAwareCoordinator | None = None

    def on_mount(self) -> None:
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        self._coordinator = ProviderAwareCoordinator(budget_limit=0)

    def render(self) -> Panel:
        """Render."""
        if self._coordinator is None:
            self.refresh_dashboard()

        coordinator = self._coordinator
        if not coordinator or not coordinator._slots:
            return Panel(
                Text("No LLM providers detected\n\nAdd API keys to .env or start local LLM:\n  LM Studio: http://localhost:1234\n  Ollama: http://localhost:11434\n  MLX: python -m mlx_lm.server",
                     style="dim"),
                title="[bold]Providers[/]", border_style="yellow",
            )

        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
        table.add_column("Provider", style="cyan")
        table.add_column("Tier")
        table.add_column("Load")
        table.add_column("Rate")
        table.add_column("Cost")

        for _name, slot in sorted(coordinator._slots.items()):
            tier_color = {"local": "green", "cheap": "dim", "balanced": "cyan", "premium": "magenta"}.get(slot.tier, "white")
            load_color = "green" if slot.load_pct < 0.5 else "yellow" if slot.load_pct < 0.8 else "red"
            load_bar = "█" * int(slot.load_pct * 5) + "░" * (5 - int(slot.load_pct * 5))

            table.add_row(
                Text(slot.name, style="bold"),
                Text(slot.tier, style=tier_color),
                Text(f"{load_bar} {slot.active_pipelines}/{slot.concurrent_limit}", style=load_color),
                Text(f"{len(slot._call_times)}/{slot.rate_limit_per_min}/min", style="dim"),
                Text("FREE" if slot.cost_per_1k == 0 else f"${slot.cost_per_1k}/MTok", style="dim"),
            )

        total_cap = coordinator.total_concurrent_capacity()
        available = sum(1 for s in coordinator._slots.values() if s.available)

        footer = Text()
        footer.append(f"{available} available", style="green")
        footer.append(f" · {total_cap} total concurrent", style="dim")

        return Panel(table, title="[bold]Provider Dashboard[/]", subtitle=footer, border_style="cyan")
