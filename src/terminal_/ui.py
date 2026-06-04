#!/usr/bin/env python3
"""
C4REQBER Terminal UI — UI Rendering Helpers
Text formatting, box drawing, and other UI utilities
"""
from __future__ import annotations


class S:
    """Styles for terminal UI"""

    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[38;5;206m"

    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    RESET = "\033[0m"
    CLEAR = "\033[2J\033[H"


def wrap_text_lines(text: str, width: int = 66) -> list[str]:
    """Wrap text into lines of maximum width."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line += word + " "
        else:
            lines.append(current_line.rstrip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.rstrip())
    return lines


def draw_box(title: str, lines: list[str], width: int = 68) -> str:
    """Draw a titled box around text lines."""
    top = f"{S.YELLOW}┌{'─' * width}┐{S.RESET}"
    title_line = f"{S.YELLOW}│{S.BOLD} {title}{S.RESET}{S.YELLOW}{' ' * (width - len(title) - 1)}│{S.RESET}"
    separator = f"{S.YELLOW}├{'─' * width}┤{S.RESET}"
    body = "\n".join(
        f"{S.YELLOW}│{S.RESET} {line:<{width - 1}} {S.YELLOW}│{S.RESET}"
        for line in lines
    )
    bottom = f"{S.YELLOW}└{'─' * width}┘{S.RESET}"
    return "\n".join([top, title_line, separator, body, bottom])


def draw_section_header(title: str) -> str:
    """Draw a section header line."""
    padding = (68 - len(title)) // 2
    return f"\n{S.CYAN}{S.BOLD}╔═══ {' ' * padding}{title}{' ' * padding}═══╗{S.RESET}"


def sparkline_bar(values: list[float], width: int = 8, color: str | None = None) -> str:
    """Render a compact sparkline bar using unicode blocks."""
    if not values:
        return ""
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        vmax = vmin + 1.0
    blocks = "▁▂▃▄▅▆▇█"
    step = (vmax - vmin) / (len(blocks) - 1)
    line = []
    slice_vals = values[-width:]
    for v in slice_vals:
        idx = int((v - vmin) / step) if step > 0 else 0
        idx = max(0, min(idx, len(blocks) - 1))
        line.append(blocks[idx])
    return "".join(line)


def hires_progress_bar(value: float, width: int = 12, fill: str = "#00FF41", empty: str = "#2A2A3E") -> str:
    """Render a high-resolution progress bar using unicode blocks."""
    value = max(0.0, min(1.0, value))
    filled = int(round(value * width))
    bar = "█" * filled + "░" * max(0, width - filled)
    return bar


def braille_chart(data: list[float], width: int = 40, height: int = 10) -> str:
    """Render a simple braille line chart from numeric data."""
    if not data:
        return ""
    min_v, max_v = min(data), max(data)
    rng = max_v - min_v if max_v != min_v else 1.0
    rows = []
    for y in range(height, 0, -1):
        threshold = min_v + (y - 1) / height * rng
        line = ""
        for x in range(min(width, len(data))):
            if data[x] >= threshold:
                line += "⠿"
            else:
                line += "⠀"
        rows.append(line)
    return "\n".join(rows)


def c4_state_sigil(state: str) -> str:
    """Return a sigil (symbol) for a given C4 state."""
    sigils = {
        "T": "⏳",
        "T_INV": "⌛",
        "S": "📐",
        "S_INV": "🔍",
        "A": "🎯",
        "A_INV": "🌀",
    }
    return sigils.get(state, "◆")


def draw_double_box(title: str, lines: list[str], width: int = 68) -> str:
    """Draw a double-line border box."""
    top = "╔" + "═" * (width - 2) + "╗"
    bottom = "╚" + "═" * (width - 2) + "╝"
    content = [f"║ {line:<{width-4}} ║" for line in lines]
    return "\n".join([top] + content + [bottom])


def draw_neural_box(title: str, lines: list[str], width: int = 68) -> str:
    """Draw a neural-themed box with rounded corners."""
    top = "╭" + "─" * (width - 2) + "╮"
    bottom = "╰" + "─" * (width - 2) + "╯"
    content = [f"│ {line:<{width-4}} │" for line in lines]
    return "\n".join([top] + content + [bottom])


def matrix_rain_frame(width: int = 80, height: int = 10) -> str:
    """Generate a single frame of matrix rain effect."""
    import random
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    lines = []
    for _ in range(height):
        line = "".join(random.choice(chars) for _ in range(width))
        lines.append(line)
    return "\n".join(lines)
