"""Desktop app entry — first-run wizard + always-seed models.json + TUI v9.
Full settings out-of-the-box (config + models + keys for all providers).
Robust: never crashes desktop on missing keys or partial config.

Splash: Python rich banner (desktop port of terminal splash vibe) + full Go TUI v9 animated splash.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.cli.config_init import config_exists, run_init_wizard
from src.cli.tui_launcher import launch_tui_v9
from src.config.paths import apply_config_to_env as central_apply
from src.llm.model_assignment import ModelAssignment

console = Console()


def _get_desktop_version() -> str:
    try:
        # Try to get from the bundled TUI or package
        from src.tui.v9.cmd.c4tui_v9 import main as _  # type: ignore  # noqa
        return "v9"
    except Exception:
        return "v9"

def render_desktop_splash(first_run: bool) -> None:
    """Static rich splash banner — port of terminal splash (subtitle/motto/footer + branding).
    Desktop version of the splash. Go TUI animated splash follows for the full experience.
    """
    ver = _get_desktop_version()

    # Mini art port (simplified cube / crystal vibe)
    art = Text("    ▗▖  ▗▖  \n", style="magenta")
    art.append("   ▐▌  ▐▌   \n", style="magenta")
    art.append("  ▗▞▚▞▚▞▚▖  \n", style="magenta")
    art.append("  ▐      ▌  ", style="magenta")
    art.append("C4\n", style="bold green")
    art.append("   ▝▚▞▚▞▘   \n", style="magenta")
    art.append("    ▝▘  ▝▘  ", style="magenta")

    # Title block
    title = Text("C4REQBER", style="bold yellow")
    title.append("  DESKTOP  ", style="bold cyan")
    title.append(ver, style="dim")

    # Subtitle (from terminal splash, EN base for desktop branding)
    sub = Text("Creative & Destructive Insights", style="dim")
    sub.append("  ·  ", style="dim")
    sub.append("At Your Fingertips", style="dim")

    # Motto with colored "Shift paradigms" (same as Go splash)
    motto = Text("Discover.  ", style="dim")
    motto.append("Invent.  ", style="cyan")
    motto.append("Shift", style="bold green")
    motto.append(" ", style="dim")
    motto.append("paradigms.", style="bold red")

    # Footer (GitLab primary, per global rule)
    footer = Text("GitLab · c4reqber · Z₃³", style="dim")

    # Compose content
    content = Text.assemble(
        art, "\n",
        title, "\n",
        sub, "\n",
        motto, "\n\n",
        footer,
    )

    if first_run:
        content.append("\n\n", style="")
        content.append("first run — full settings + keys via ~/.c4reqber (central)", style="green")

    panel = Panel.fit(
        content,
        title="[bold]COGNITIVE EXOSKELETON[/bold]",
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(panel)
    # Tiny pause so banner is readable before TUI takes alt-screen (Go splash follows)
    time.sleep(0.65)


def main() -> int:
    try:
        central_apply()
    except Exception:
        pass  # never block desktop start

    first_run = not config_exists()

    # Ensure core config + wizard
    if first_run:
        try:
            run_init_wizard(force=False)
            central_apply()
        except Exception:
            pass

    # Always ensure models.json (full settings even if user skipped wizard or deleted it)
    from src.config.paths import MODELS_JSON
    if not MODELS_JSON.exists():
        try:
            assignment = ModelAssignment.create_default("balanced")
            assignment.save()
        except Exception:
            pass

    central_apply()

    # Desktop splash banner (ported + polished version of terminal splash text/art vibe)
    no_splash = (
        "--no-splash" in sys.argv
        or os.environ.get("C4_NO_SPLASH", "") != ""
        or os.environ.get("C4_SPLASH", "1") == "0"
    )
    if not no_splash:
        render_desktop_splash(first_run)

    # Forward args; launch Go TUI v9 (the animated splash + full cockpit)
    extra = [a for a in sys.argv[1:] if a not in ("--no-splash",)]
    if "--no-splash" in sys.argv:
        extra.append("--no-splash")

    # In bundled desktop, the TUI binary is next to us in Resources (mac) or alongside (win)
    # launch_tui_v9 will find it or auto-build in dev.
    return launch_tui_v9(extra, build_if_missing=True)


if __name__ == "__main__":
    raise SystemExit(main())