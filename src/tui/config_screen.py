"""TUI Config Editor — Rich table with editable settings.

Arrow keys: navigate providers. Q: quit. Displays all providers, API keys (masked), status, and model.
Note: API key editing is done via environment variables or .env file, not this screen.
"""
from __future__ import annotations

import os
import sys

from rich.console import Console
from rich.table import Table


_console = Console(log_path=False)


def tui_config_screen() -> None:
    """Interactive TUI for viewing and validating configuration."""
    from src.llm.config import LLMProvider, get_default_model

    providers = [
        ("OpenRouter", "OPENROUTER_API_KEY", LLMProvider.OPENROUTER),
        ("DeepSeek", "DEEPSEEK_API_KEY", LLMProvider.DEEPSEEK),
        ("XAI / Grok", "XAI_API_KEY", LLMProvider.XAI),
        ("Mistral", "MISTRAL_API_KEY", LLMProvider.MISTRAL),
        ("Moonshot", "MOONSHOT_API_KEY", LLMProvider.MOONSHOT),
        ("Liquid AI", "LIQUID_API_KEY", LLMProvider.LIQUID),
        ("NVIDIA NIM", "NVIDIA_API_KEY", LLMProvider.NVIDIA),
        ("YandexGPT", "YANDEX_API_KEY", LLMProvider.YANDEX),
        ("Ollama (local)", "OLLAMA_URL", LLMProvider.OLLAMA),
        ("LM Studio (local)", "LM_STUDIO_URL", LLMProvider.LM_STUDIO),
        ("MLX (Apple Silicon)", None, LLMProvider.MLX),
    ]

    selected = 0

    def _render():
        _console.clear()
        _console.print("[bold cyan]C4REQBER Configuration[/]")
        _console.print(f"[dim]Python {sys.version_info.major}.{sys.version_info.minor} | ↑↓ navigate | Q quit[/]")
        _console.print()

        table = Table(show_header=True, header_style="bold")
        table.add_column("", width=2)
        table.add_column("Provider", width=20)
        table.add_column("Key", width=18)
        table.add_column("Model", width=30)
        table.add_column("Status", width=12)

        for i, (name, env_var, provider) in enumerate(providers):
            cursor = "→" if i == selected else " "
            if env_var:
                key = os.getenv(env_var, "")
                if key:
                    masked = key[:12] + "..." + key[-4:] if len(key) > 20 else "***"
                    status = "[green]● configured[/]"
                else:
                    masked = "—"
                    status = "[dim]○ not set[/]"
            else:
                masked = "(local)"
                status = "[green]● available[/]" if _check_mlx() else "[dim]○ not Apple Silicon[/]"

            model = get_default_model(provider)
            row_style = "bold cyan" if i == selected else ""
            table.add_row(cursor, f"[{row_style}]{name}[/]", masked, model, status)

        _console.print(table)
        _console.print()

        os.getenv("JWT_SECRET", "")
        if selected < len(providers):
            sel_name, sel_env, _ = providers[selected]
            _console.print(f"[bold]Selected:[/] {sel_name}")
            if sel_env:
                val = os.getenv(sel_env, "")
                if val:
                    _console.print(f"  Key: [green]{val[:16]}...{val[-4:]}[/] (set)")
                else:
                    _console.print(f"  [dim]Key not set. Set via: export {sel_env}=<key>[/]")

    _render()

    while True:
        ch = _read_key()
        if ch == "up" and selected > 0:
            selected -= 1
            _render()
        elif ch == "down" and selected < len(providers) - 1:
            selected += 1
            _render()
        elif ch in ("q", "esc"):
            break


def _read_key() -> str:
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
        if ch.lower() == "q":
            return "q"
        return ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _check_mlx() -> bool:
    try:
        import platform
        proc = platform.processor().lower()
        return "arm" in proc or "apple" in proc
    except Exception:
        return False
