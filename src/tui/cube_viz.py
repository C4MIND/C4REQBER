"""
TUI: Cube Visualization
ASCII 3×3×3 cube with Z₃³ coordinates, Matrix rain, TRON glow.
"""
from __future__ import annotations

import math
import random
from typing import Any

from rich.box import ROUNDED
from rich.panel import Panel
from rich.style import Style
from rich.text import Text


CUBE_STATES = {
    (0,0,0): ("origin", "Начало познания", Style(color="#4ECDC4")),
    (0,0,1): ("observe", "Наблюдение", Style(color="#4ECDC4")),
    (0,0,2): ("abstract", "Абстракция", Style(color="#4ECDC4")),
    (0,1,0): ("analyze", "Анализ", Style(color="#06b6d4")),
    (0,1,1): ("decompose", "Декомпозиция", Style(color="#06b6d4")),
    (0,1,2): ("formalize", "Формализация", Style(color="#06b6d4")),
    (0,2,0): ("structure", "Структурирование", Style(color="#0ea5e9")),
    (0,2,1): ("model", "Моделирование", Style(color="#0ea5e9")),
    (0,2,2): ("generalize", "Обобщение", Style(color="#0ea5e9")),
    (1,0,0): ("understand", "Понимание", Style(color="#4ADE80")),
    (1,0,1): ("contextualize", "Контекстуализация", Style(color="#4ADE80")),
    (1,0,2): ("theorize", "Теоретизирование", Style(color="#4ADE80")),
    (1,1,0): ("synthesize", "Синтез", Style(color="#FFD93D")),
    (1,1,1): ("integrate", "Интеграция", Style(color="#FFD93D")),
    (1,1,2): ("meta_analyze", "Мета-анализ", Style(color="#FFD93D")),
    (1,2,0): ("design", "Проектирование", Style(color="#f97316")),
    (1,2,1): ("optimize", "Оптимизация", Style(color="#f97316")),
    (1,2,2): ("architect", "Архитектура", Style(color="#f97316")),
    (2,0,0): ("question", "Сомнение", Style(color="#8b5cf6")),
    (2,0,1): ("hypothesize", "Гипотеза", Style(color="#8b5cf6")),
    (2,0,2): ("abstract_deep", "Глубокая абстракция", Style(color="#8b5cf6")),
    (2,1,0): ("discover", "Открытие", Style(color="#ec4899")),
    (2,1,1): ("innovate", "Инновация", Style(color="#ec4899")),
    (2,1,2): ("insight", "Инсайт", Style(color="#ec4899")),
    (2,2,0): ("create", "Создание", Style(color="#FF6B6B")),
    (2,2,1): ("master", "Мастерство", Style(color="#FF6B6B")),
    (2,2,2): ("emerge", "Эмерджентность", Style(color="#FF6B6B")),
}

ALL_CUBE_COORDS = [(t, s, a) for t in range(3) for s in range(3) for a in range(3)]

STEP_COLORS = [
    "#4ECDC4", "#06b6d4", "#0ea5e9",
    "#a78bfa", "#c084fc", "#e879f9",
    "#fb923c", "#FFD93D", "#4ADE80",
]

MATRIX_CHARS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TRON_GLOW_CHARS = "▐░▒▓█"

# Mutable container to avoid global keyword
_matrix: dict[str, Any] = {"state": {}, "initialized": False}


def _init_matrix_state(cols: int) -> None:
    if _matrix["initialized"]:
        return
    _matrix["state"] = {
        "drops": [random.randint(-30, -1) for _ in range(cols)],
        "lengths": [random.randint(5, 18) for _ in range(cols)],
        "phases": [random.random() * 2 * math.pi for _ in range(cols)],
    }
    _matrix["initialized"] = True


def render_ascii_cube(active_state: tuple[int, int, int] = (2,1,2), glow: bool = False, all_glow: set[tuple[int, int, int]] | None = None, completion_flash: bool = False) -> Panel:
    """ASCII-рендер куба 3×3×3 с half-block графикой."""
    t, s, a = active_state

    if all_glow is None:
        all_glow = set()

    def cell_char(tv, sv, av) -> str:
        """Cell char."""
        coord = (tv, sv, av)
        if completion_flash:
            return "[bold #4ADE80]█[/]"
        if coord in all_glow:
            return f"[bold {CUBE_STATES.get(coord, CUBE_STATES[(0,0,0)])[2].color}]█[/]"
        if coord == (t, s, a):
            inner = "█" if glow else "▓"
            cs = CUBE_STATES.get(coord, CUBE_STATES[(0,0,0)])
            return f"[bold {cs[2].color}]{inner}[/]"
        return "░"

    lines = []
    lines.append(f"         (a=2)  {cell_char(0,0,2)} {cell_char(0,1,2)} {cell_char(0,2,2)}")
    lines.append(f"                  {cell_char(1,0,2)} {cell_char(1,1,2)} {cell_char(1,2,2)}")
    lines.append(f"                  {cell_char(2,0,2)} {cell_char(2,1,2)} {cell_char(2,2,2)}")
    lines.append("")
    lines.append(f"    (a=1)   {cell_char(0,0,1)} {cell_char(0,1,1)} {cell_char(0,2,1)}")
    lines.append(f"              {cell_char(1,0,1)} {cell_char(1,1,1)} {cell_char(1,2,1)}")
    lines.append(f"              {cell_char(2,0,1)} {cell_char(2,1,1)} {cell_char(2,2,1)}")
    lines.append("")
    lines.append(f"    (a=0)   {cell_char(0,0,0)} {cell_char(0,1,0)} {cell_char(0,2,0)}")
    lines.append(f"              {cell_char(1,0,0)} {cell_char(1,1,0)} {cell_char(1,2,0)}")
    lines.append(f"              {cell_char(2,0,0)} {cell_char(2,1,0)} {cell_char(2,2,0)}")

    name, desc, style = CUBE_STATES.get(active_state, CUBE_STATES[(0,0,0)])

    panel = Panel(
        Text.from_markup("\n".join(lines)),
        title=f"[bold]{name}[/bold] ({t},{s},{a})",
        subtitle=desc,
        border_style="bold #4ECDC4",
        box=ROUNDED,
        padding=(1, 4),
    )
    return panel


def matrix_rain_text(rows: int = 20, cols: int = 60, tick: int = 0) -> Text:
    """Generate Matrix rain as Rich Text for overlay on panels."""
    _init_matrix_state(cols)
    drops = _matrix["state"]["drops"]
    lengths = _matrix["state"]["lengths"]
    texts = []

    for col in range(min(cols, len(drops))):
        drops[col] += 1
        if drops[col] > rows + lengths[col]:
            drops[col] = random.randint(-18, -5)
            lengths[col] = random.randint(5, 18)

        for row_offset in range(lengths[col]):
            y = drops[col] - row_offset
            if 0 <= y < rows:
                ch = random.choice(MATRIX_CHARS)
                if row_offset == 0:
                    brightness = random.randint(200, 255)
                    color = f"#{0:02x}{brightness:02x}{0:02x}"
                    style_str = f"bold {color}"
                elif row_offset < 3:
                    brightness = random.randint(80, 180)
                    color = f"#{0:02x}{brightness:02x}{0:02x}"
                    style_str = color
                elif row_offset < 5:
                    brightness = random.randint(30, 80)
                    color = f"#00{brightness:02x}00"
                    style_str = color
                else:
                    brightness = random.randint(5, 20)
                    color = f"#00{brightness:02x}00"
                    style_str = color

                texts.append((ch, style_str, col, y))

    result = Text()
    for ch, style_str, col, _y in texts:
        result.append(ch, style=style_str)
        if col < cols - 1:
            result.append(" ")
    return result


def tron_glow_panel(content: Any, title: str = "", subtitle: str = "", border_color: str = "#4ECDC4", padding: tuple = (1,2)) -> Panel:
    """Panel with TRON-style glow borders and half-block accents."""
    bright = f"bold {border_color}"
    return Panel(
        content,
        title=f"[{bright}]{title}[/]" if title else "",
        subtitle=subtitle,
        border_style=bright,
        box=ROUNDED,
        padding=padding,
    )
