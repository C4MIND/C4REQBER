#!/usr/bin/env python3
"""Render stripped ANSI terminal text to PNG (dark theme).

Uses ASCII fallbacks for box-drawing / progress glyphs that Menlo cannot render,
and a CJK-capable font on macOS so EN+ZH TUI text does not show tofu boxes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Bubble Tea / lipgloss progress + card glyphs → ASCII (readable in any font)
_GLYPH_MAP = str.maketrans(
    {
        "░": "-",
        "▒": "=",
        "▓": "#",
        "█": "#",
        "▣": "[*]",
        "▶": ">",
        "●": "*",
        "✦": "*",
        "✗": "x",
        "❯": ">",
        "┃": "|",
        "│": "|",
        "─": "-",
        "━": "-",
        "┏": "+",
        "┓": "+",
        "┗": "+",
        "┛": "+",
        "┣": "+",
        "┫": "+",
        "┳": "+",
        "┻": "+",
        "╋": "+",
        "╱": "/",
        "╲": "\\",
        "╳": "x",
        "→": "->",
        "…": "...",
    }
)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def normalize_terminal_text(text: str) -> str:
    return strip_ansi(text).translate(_GLYPH_MAP)


def _pick_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render(txt_path: Path, png_path: Path, *, font_size: int = 13) -> None:
    raw = txt_path.read_text(encoding="utf-8", errors="replace")
    lines = normalize_terminal_text(raw).splitlines()
    font = _pick_font(font_size)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 2
    char_w = max(font.getlength("M"), font.getlength("中")) or 8
    cols = max((len(line) for line in lines), default=80)
    rows = max(len(lines), 1)
    pad = 12
    w = int(cols * char_w + pad * 2)
    h = int(rows * line_h + pad * 2)
    img = Image.new("RGB", (w, h), color=(13, 17, 23))
    draw = ImageDraw.Draw(img)
    fg = (200, 230, 255)
    accent = (0, 200, 200)
    for i, line in enumerate(lines):
        y = pad + i * line_h
        stripped = line.strip()
        if stripped.startswith(("[*]", ">", "*", "x")):
            color = accent
        else:
            color = fg
        draw.text((pad, y), line, fill=color, font=font)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(png_path, format="PNG")
    print(f"Wrote {png_path} ({w}x{h})")


def main() -> None:
    if len(sys.argv) not in (3, 4):
        print(
            f"usage: {sys.argv[0]} input.txt output.png [font_size]",
            file=sys.stderr,
        )
        sys.exit(1)
    font_size = int(sys.argv[3]) if len(sys.argv) == 4 else 13
    render(Path(sys.argv[1]), Path(sys.argv[2]), font_size=font_size)


if __name__ == "__main__":
    main()
