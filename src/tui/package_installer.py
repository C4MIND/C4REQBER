"""TUI Package Manager — Rich-based interactive package installer.

Arrow keys: navigate. Enter: install/remove. Q: quit.
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table


_console = Console(log_path=False)


def tui_package_manager() -> None:
    """Interactive TUI for scientific package management."""
    from src.cli.package_manager import (
        PACKAGES,
        PackageStatus,
        detect_all,
        install_package,
        uninstall_package,
    )

    statuses = detect_all()
    selected = 0
    installed = sum(1 for s in statuses.values() if s == PackageStatus.INSTALLED)

    while True:
        _console.clear()
        _console.print("[bold cyan]C4REQBER Scientific Package Manager[/]")
        _console.print(
            f"[dim]{installed}/{len(PACKAGES)} installed | ↑↓ navigate | Enter install/remove | Q quit[/]"
        )
        _console.print()

        table = Table(show_header=True, header_style="bold")
        table.add_column("", width=3)
        table.add_column("Package", width=18)
        table.add_column("Status", width=14)
        table.add_column("Description", width=40)

        for i, pkg in enumerate(PACKAGES):
            st = statuses.get(pkg.id, PackageStatus.UNKNOWN)
            icon_map = {
                PackageStatus.INSTALLED: "●",
                PackageStatus.AVAILABLE: "○",
                PackageStatus.INCOMPATIBLE: "✗",
                PackageStatus.UNKNOWN: "?",
            }
            icon_map.get(st, "?")
            status_str = {
                PackageStatus.INSTALLED: "[green]installed[/]",
                PackageStatus.AVAILABLE: "[dim]available[/]",
                PackageStatus.INCOMPATIBLE: "[red]incompatible[/]",
                PackageStatus.UNKNOWN: "[dim]unknown[/]",
            }.get(st, "unknown")
            cursor = "→" if i == selected else " "
            color = ""
            if i == selected:
                color = "[bold cyan]"
            table.add_row(
                cursor,
                f"{color}{pkg.id}[/]",
                status_str,
                f"{color}{pkg.description[:60]}[/]" if i == selected else pkg.description[:60],
            )

        _console.print(table)
        _console.print()
        _console.print("[dim]Arrow keys (↑↓) — navigate | Enter — toggle install | Q — quit[/]")

        key = _keyboard_input()
        if key == "up" and selected > 0:
            selected -= 1
        elif key == "down" and selected < len(PACKAGES) - 1:
            selected += 1
        elif key == "enter":
            pkg = PACKAGES[selected]
            st = statuses.get(pkg.id, PackageStatus.UNKNOWN)
            if st == PackageStatus.INSTALLED:
                _console.clear()
                _console.print(f"[yellow]Removing {pkg.name}...[/]")
                ok, msg = uninstall_package(pkg.id)
                _console.print(f"[green]{msg}[/]" if ok else f"[red]{msg}[/]")
                _console.input("[dim]Press Enter[/]")
            elif st == PackageStatus.AVAILABLE:
                _console.clear()
                _console.print(f"[bold]Installing {pkg.name}...[/]")
                ok, msg = install_package(pkg.id)
                _console.print(f"[green]{msg}[/]" if ok else f"[red]{msg}[/]")
                _console.input("[dim]Press Enter[/]")
            statuses = detect_all()
            installed = sum(1 for s in statuses.values() if s == PackageStatus.INSTALLED)
        elif key in ("q", "esc"):
            break


def _keyboard_input() -> str:
    """Cross-platform single-key input — uses Rich Live context when in Textual App."""
    import sys

    try:
        from textual.app import App

        active_app = App.get_running_app()  # type: ignore[attr-defined]
        if active_app:
            return ""  # Textual handles keys via on_key, not raw stdin
    except Exception:
        pass
    if sys.platform == "win32":
        import msvcrt

        key = msvcrt.getch()
        if key == b"\xe0":
            key = msvcrt.getch()
            if key == b"H":
                return "up"
            if key == b"P":
                return "down"
        if key == b"\r":
            return "enter"
        if key == b"q" or key == b"Q":
            return "q"
        if key == b"\x1b":
            return "esc"
        return ""
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(2)
                if ch2 == "[A":
                    return "up"
                if ch2 == "[B":
                    return "down"
                return "esc"
            if ch in ("\r", "\n"):
                return "enter"
            if ch.lower() == "q":
                return "q"
            return ""
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
