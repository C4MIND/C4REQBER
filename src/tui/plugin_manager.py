from __future__ import annotations


"""
TUI: Plugin Manager
Plugin management UI for enabling/disabling 20 cognitive plugins.
"""


from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# 20 Cognitive Plugins (from AGENTS.md)
PLUGIN_LIST = [
    ("SWOT", "Strengths/Weaknesses/O/T", "strategic"),
    ("Red Team", "Adversarial analysis", "security"),
    ("Six Hats", "6 thinking modes", "creativity"),
    ("SCAMPER", "7 creativity techniques", "creativity"),
    ("5 Whys", "Root cause analysis", "analysis"),
    ("Ishikawa", "Fishbone diagram", "analysis"),
    ("Morphological", "Matrix analysis", "design"),
    ("Delphi", "Expert consensus", "collaboration"),
    ("OODA Loop", "Observe-Orient-Decide-Act", "military"),
    ("Pareto", "80/20 analysis", "efficiency"),
    ("Mind Map", "Visual brainstorming", "creativity"),
    ("Brainstorming", "Idea generation", "creativity"),
    ("Reverse Brainstorming", "Find flaws", "creativity"),
    ("Six Thinking Hats", "De Bono's method", "creativity"),
    ("TRIZ", "40 principles", "invention"),
    ("C4-META", "27 states navigation", "cognitive"),
    ("Bayesian", "Probabilistic reasoning", "statistics"),
    ("Causal", "Do-calculus", "causality"),
    ("Monte Carlo", "Statistical validation", "statistics"),
    ("Falsifier", "Adversarial check", "validation"),
]


class PluginManager:
    """Manage 20 cognitive plugins."""

    def __init__(self) -> None:
        # All plugins enabled by default
        self.enabled: dict[str, bool] = {name: True for name, _, _ in PLUGIN_LIST}
        self.category_filter: str = "all"  # all, creativity, analysis, etc.

    def toggle(self, plugin_name: str) -> bool:
        """Toggle a plugin on/off. Returns new state."""
        if plugin_name in self.enabled:
            self.enabled[plugin_name] = not self.enabled[plugin_name]
            return self.enabled[plugin_name]
        return False

    def is_enabled(self, plugin_name: str) -> bool:
        return self.enabled.get(plugin_name, False)

    def get_enabled_list(self) -> list[str]:
        return [name for name, enabled in self.enabled.items() if enabled]

    def set_filter(self, category: str) -> None:
        self.category_filter = category

    def get_filtered_plugins(self) -> list[tuple]:
        """Get filtered plugins."""
        if self.category_filter == "all":
            return PLUGIN_LIST
        return [(n, d, c) for n, d, c in PLUGIN_LIST if c == self.category_filter]


def make_plugin_panel(manager: PluginManager) -> Panel:
    """Create plugin management panel."""
    plugins = manager.get_filtered_plugins()
    enabled_count = sum(1 for n, _ in plugins if manager.is_enabled(n))

    table = Table(
        title=f"[bold #4ECDC4]🧠 PLUGIN MANAGER ({enabled_count}/{len(plugins)} enabled)[/]",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Status", style="bold", width=6)
    table.add_column("Plugin", style="cyan", no_wrap=True)
    table.add_column("Description", style="dim")
    table.add_column("Category", style="yellow")

    for name, desc, cat in plugins:
        status = "✅" if manager.is_enabled(name) else "❌"
        style = "bold #4ADE80" if manager.is_enabled(name) else "dim"
        table.add_row(
            f"[{style}]{status}[/]",
            f"[bold]{name}[/]",
            desc,
            cat,
        )

    return Panel(
        table,
        title="[bold #4ECDC4]🧠 COGNITIVE PLUGINS[/]",
        border_style="bold #4ECDC4",
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
    )


def make_plugin_toggle_help() -> Panel:
    """Help panel for plugin toggle keys."""
    text = Text()
    text.append("[bold #4ECDC4]PLUGIN MANAGER CONTROLS[/]\n\n")
    text.append("[bold]1-9[/] Toggle plugin (number)\n")
    text.append("[bold]f[/] Filter: creativity\n")
    text.append("[bold]a[/] Filter: analysis\n")
    text.append("[bold]s[/] Filter: statistics\n")
    text.append("[bold]c[/] Clear filter (show all)\n")
    text.append("[bold]q[/] Quit plugin manager\n")

    return Panel(
        text,
        title="[bold]🧠 HELP[/]",
        border_style="bold #FFD93D",
        box=box.ROUNDED,
        padding=(1, 2),
    )
