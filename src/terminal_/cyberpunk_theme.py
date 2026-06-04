#!/usr/bin/env python3
"""
Reqber Cyberpunk Theme — Neon Noir color system + Hi-Res ASCII techniques.
"""
from __future__ import annotations

import os


class CyberpunkTheme:
    """Neon Noir color palette + Hi-Res ASCII rendering utilities."""

    # ─── Base Colors ───
    BG = "\033[48;2;10;10;15m"           # #0A0A0F deep void black
    BG_CLEAR = "\033[40m"
    SURFACE = "\033[48;2;18;18;26m"      # #12121A panel black
    SURFACE_ELEVATED = "\033[48;2;26;26;46m"  # #1A1A2E active panel

    # ─── Foreground Colors ───
    FG_PRIMARY = "\033[38;2;0;255;65m"    # #00FF41 Matrix Green
    FG_SECONDARY = "\033[38;2;0;212;255m" # #00D4FF Cyber Cyan
    FG_ACCENT = "\033[38;2;255;0;110m"    # #FF006E Neon Pink
    FG_WARNING = "\033[38;2;255;184;0m"   # #FFB800 Amber 8-bit
    FG_DANGER = "\033[38;2;255;42;42m"   # #FF2A2A Blood Red
    FG_MUTED = "\033[38;2;107;114;128m"   # #6B7280 Steel Gray
    FG_GHOST = "\033[38;2;42;42;62m"      # #2A2A3E trace lines
    FG_WHITE = "\033[38;2;255;255;255m"   # #FFFFFF pure white

    # ─── Combined (fg + bg) ───
    PRIMARY = BG + FG_PRIMARY
    SECONDARY = BG + FG_SECONDARY
    ACCENT = BG + FG_ACCENT
    WARNING = BG + FG_WARNING
    DANGER = BG + FG_DANGER
    MUTED = BG + FG_MUTED
    GHOST = BG + FG_GHOST
    WHITE = BG + FG_WHITE

    # ─── Styles ───
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    STRIKETHROUGH = "\033[9m"

    RESET = "\033[0m"
    CLEAR = "\033[2J\033[H"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

    # ─── 8-bit Block Characters ───
    BLOCK_FULL = "█"
    BLOCK_DARK = "▓"
    BLOCK_MEDIUM = "▒"
    BLOCK_LIGHT = "░"
    BLOCK_UPPER = "▀"
    BLOCK_LOWER = "▄"

    # ─── Box Drawing ───
    HORIZ = "─"
    VERT = "│"
    TL = "┌"
    TR = "┐"
    BL = "└"
    BR = "┘"
    T_DOWN = "┬"
    T_UP = "┴"
    T_RIGHT = "├"
    T_LEFT = "┤"
    CROSS = "┼"
    HORIZ_DOUBLE = "═"
    VERT_DOUBLE = "║"
    TL_DOUBLE = "╔"
    TR_DOUBLE = "╗"
    BL_DOUBLE = "╚"
    BR_DOUBLE = "╝"

    # ─── Braille Patterns (2×2 dots per char) ───
    BRAILLE_FULL = "⣿"
    BRAILLE_3_4 = "⣷"
    BRAILLE_1_2 = "⣧"
    BRAILLE_1_4 = "⣀"
    BRAILLE_WAVE = "⠛"

    # ─── Arrow / Symbol ───
    ARROW_RIGHT = "▶"
    ARROW_LEFT = "◀"
    ARROW_UP = "▲"
    ARROW_DOWN = "▼"
    DIAMOND = "◈"
    DIAMOND_SMALL = "◆"
    DIAMOND_OUTLINE = "◇"
    SQUARE = "■"
    SQUARE_SMALL = "▪"
    SQUARE_OUTLINE = "□"
    CIRCLE = "●"
    CIRCLE_OUTLINE = "○"
    CIRCLE_SMALL = "•"
    CHECK = "✓"
    CROSS_MARK = "✗"
    BULLET = "◈"
    SPARKLE = "✦"

    @classmethod
    def color(cls, hex_color: str, bg: bool = False) -> str:
        """Generate ANSI escape from hex (#RRGGBB)."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        code = 48 if bg else 38
        return f"\033[{code};2;{r};{g};{b}m"

    @classmethod
    def gradient_text(cls, text: str, start_hex: str, end_hex: str) -> str:
        """Render text with horizontal color gradient."""
        if not text:
            return ""
        start = [int(start_hex[i : i + 2], 16) for i in (1, 3, 5)]
        end = [int(end_hex[i : i + 2], 16) for i in (1, 3, 5)]
        result = ""
        for i, ch in enumerate(text):
            ratio = i / max(1, len(text) - 1)
            r = int(start[0] + (end[0] - start[0]) * ratio)
            g = int(start[1] + (end[1] - start[1]) * ratio)
            b = int(start[2] + (end[2] - start[2]) * ratio)
            result += f"\033[38;2;{r};{g};{b}m{ch}"
        result += cls.RESET
        return result

    @classmethod
    def half_block(cls, upper_color: tuple[int, int, int] | None = None,
                   lower_color: tuple[int, int, int] | None = None) -> str:
        """Render half-block character with different upper/lower colors."""
        if upper_color and lower_color:
            return (f"\033[38;2;{upper_color[0]};{upper_color[1]};{upper_color[2]}m"
                    f"\033[48;2;{lower_color[0]};{lower_color[1]};{lower_color[2]}m"
                    f"{cls.BLOCK_UPPER}{cls.RESET}")
        return cls.BLOCK_UPPER

    @classmethod
    def sparkline(cls, values: list[float], width: int = 8,
                  color_hex: str = "#00FF41") -> str:
        """Render Braille sparkline from float values [0.0, 1.0]."""
        if not values or width <= 0:
            return ""
        max_val = max(values) or 1.0
        braille_chars = ["⠀", "⠁", "⠂", "⠃", "⠄", "⠅", "⠆", "⠇",
                         "⠈", "⠉", "⠊", "⠋", "⠌", "⠍", "⠎", "⠏",
                         "⠐", "⠑", "⠒", "⠓", "⠔", "⠕", "⠖", "⠗",
                         "⠘", "⠙", "⠚", "⠛", "⠜", "⠝", "⠞", "⠟",
                         "⠠", "⠡", "⠢", "⠣", "⠤", "⠥", "⠦", "⠧",
                         "⠨", "⠩", "⠪", "⠫", "⠬", "⠭", "⠮", "⠯",
                         "⠰", "⠱", "⠲", "⠳", "⠴", "⠵", "⠶", "⠷",
                         "⠸", "⠹", "⠺", "⠻", "⠼", "⠽", "⠾", "⠿"]
        # Braille pattern encoding: dots 1-8
        # dots 1,2,3,7 = left column top-to-bottom
        # dots 4,5,6,8 = right column top-to-bottom
        result = ""
        color = cls.color(color_hex)
        step = max(1, len(values) // width)
        for i in range(0, min(len(values), width * step), step):
            chunk = values[i:i + step]
            avg = sum(chunk) / len(chunk)
            # Map 0.0-1.0 to Braille density
            idx = int(avg * 63)  # 0-63
            idx = max(0, min(63, idx))
            result += color + braille_chars[idx]
        result += cls.RESET
        return result

    @classmethod
    def progress_bar(cls, value: float, width: int = 20,
                     filled_color: str = "#00FF41",
                     empty_color: str = "#2A2A3E") -> str:
        """Hi-Res progress bar using half-blocks for 1% precision."""
        value = max(0.0, min(1.0, value))
        filled_w = int(value * width)
        remainder = (value * width) - filled_w

        bar = ""
        bar += cls.color(filled_color) + cls.BLOCK_FULL * filled_w

        # Half-block for remainder precision
        if remainder > 0.5 and filled_w < width:
            bar += cls.half_block(
                (int(filled_color[1:3], 16), int(filled_color[3:5], 16), int(filled_color[5:7], 16)),
                (int(empty_color[1:3], 16), int(empty_color[3:5], 16), int(empty_color[5:7], 16))
            )
            filled_w += 1

        remaining = width - filled_w
        bar += cls.color(empty_color) + cls.BLOCK_LIGHT * remaining + cls.RESET
        return bar

    @classmethod
    def is_truecolor_supported(cls) -> bool:
        """Detect if terminal supports 24-bit truecolor."""
        term = os.environ.get("TERM", "")
        colorterm = os.environ.get("COLORTERM", "")
        return "truecolor" in colorterm or "24bit" in colorterm or "256color" in term

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


def draw_box(title: str, lines: list[str], width: int = 68,
             theme: type[CyberpunkTheme] = CyberpunkTheme) -> str:
    """Draw a titled box with cyberpunk styling."""
    top = f"{theme.FG_WARNING}{theme.TL}{theme.HORIZ * width}{theme.TR}{theme.RESET}"
    title_line = (f"{theme.FG_WARNING}{theme.VERT}{theme.RESET}{theme.BOLD} {title}{theme.RESET}"
                  f"{theme.FG_WARNING}{' ' * (width - len(title) - 1)}{theme.VERT}{theme.RESET}")
    separator = f"{theme.FG_WARNING}{theme.T_RIGHT}{theme.HORIZ * width}{theme.T_LEFT}{theme.RESET}"
    body = "\n".join(
        f"{theme.FG_WARNING}{theme.VERT}{theme.RESET} {line:<{width - 1}} {theme.FG_WARNING}{theme.VERT}{theme.RESET}"
        for line in lines
    )
    bottom = f"{theme.FG_WARNING}{theme.BL}{theme.HORIZ * width}{theme.BR}{theme.RESET}"
    return "\n".join([top, title_line, separator, body, bottom])


def draw_section_header(title: str, theme: type[CyberpunkTheme] = CyberpunkTheme) -> str:
    """Draw a section header line with cyberpunk styling."""
    padding = (68 - len(title)) // 2
    return (f"\n{theme.FG_SECONDARY}{theme.BOLD}{theme.TL_DOUBLE}{theme.HORIZ_DOUBLE * 3} "
            f"{' ' * padding}{title}{' ' * padding}"
            f"{theme.HORIZ_DOUBLE * 3}{theme.TR_DOUBLE}{theme.RESET}")
