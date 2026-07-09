#!/usr/bin/env python3
"""Render stripped ANSI terminal text to PNG (dark theme)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def render(txt_path: Path, png_path: Path, *, font_size: int = 14) -> None:
    raw = txt_path.read_text(encoding="utf-8", errors="replace")
    lines = strip_ansi(raw).splitlines()
    # Monospace metrics
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 2
    char_w = font.getlength("M") or 8
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
        color = accent if line.strip().startswith(("▣", "✦", "●")) else fg
        draw.text((pad, y), line, fill=color, font=font)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(png_path, format="PNG")
    print(f"Wrote {png_path} ({w}x{h})")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} input.txt output.png", file=sys.stderr)
        sys.exit(1)
    render(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
