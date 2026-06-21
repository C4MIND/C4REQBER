"""C4REQBER TUI Package — delegates to v9 Go binary."""
from __future__ import annotations

from src.cli.tui_launcher import launch_tui_v9


def main() -> None:
    """Entry point for C4REQBER TUI v9."""
    raise SystemExit(launch_tui_v9())