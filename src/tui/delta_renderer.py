# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Delta renderer — flicker-free terminal updates by tracking cell diffs.

Instead of clear+redraw (which flickers), we track the previous frame as a
grid of cells and only write ANSI escape sequences for cells that changed.

Usage:
    dr = DeltaRenderer(width=80, height=24)
    for frame in frames:
        dr.render(frame)  # only changed cells are sent to stdout
"""
from __future__ import annotations

import sys
from typing import Iterator, TextIO


ANSI_RESET = "\033[0m"


class Cell:
    """Cell."""
    __slots__ = ("char", "fg", "bg", "bold", "dim")

    def __init__(
        self,
        char: str = " ",
        fg: str = "",
        bg: str = "",
        bold: bool = False,
        dim: bool = False,
    ) -> None:
        self.char = char
        self.fg = fg
        self.bg = bg
        self.bold = bold
        self.dim = dim

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return False
        return (
            self.char == other.char
            and self.fg == other.fg
            and self.bg == other.bg
            and self.bold == other.bold
            and self.dim == other.dim
        )

    def to_ansi(self) -> str:
        """To ansi."""
        parts = []
        if self.bold:
            parts.append("\033[1m")
        if self.dim:
            parts.append("\033[2m")
        if self.fg:
            parts.append(self.fg)
        if self.bg:
            parts.append(self.bg)
        parts.append(self.char)
        return "".join(parts)


class DeltaRenderer:
    """Flicker-free terminal frame rendering.

    Maintains a grid of the previous frame. On each render(),
    compares new frame against cached grid and writes only
    changed cells using absolute cursor positioning (ANSI CSI n;mH).
    """

    def __init__(self, width: int = 80, height: int = 24) -> None:
        self.width = width
        self.height = height
        self._grid: list[list[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]
        self._frame_count = 0
        self._total_diffs = 0
        self._initialized = False

    def _ansi_move(self, row: int, col: int) -> str:
        """Move cursor to 1-based (row, col)."""
        return f"\033[{row};{col}H"

    def _ansi_color(self, hex_color: str, is_fg: bool = True) -> str:
        """Convert #rrggbb to ANSI 256-color or truecolor."""
        if not hex_color or not hex_color.startswith("#"):
            return ""
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return ""
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        layer = 16 if is_fg else 48
        return f"\033[{layer};2;{r};{g};{b}m"

    def _parse_rich_line(self, line: str, row: int) -> list[Cell]:
        """Parse a Rich-markup string line into Cell grid row.

        Handles basic Rich tags: [color], [/color], [bold], [dim].
        Does NOT handle nested tags or all edge cases — but enough
        for the C4REQBER TUI which uses simple markup.
        """
        cells = [Cell() for _ in range(self.width)]
        col = 0
        i = 0

        current_fg = ""
        current_bg = ""
        current_bold = False
        current_dim = False

        style_stack: list[dict[str, bool | str]] = []

        while i < len(line) and col < self.width:
            ch = line[i]

            if ch == "[":
                end = line.find("]", i)
                if end == -1:
                    break
                tag = line[i + 1 : end]

                if tag.startswith("/"):
                    clean = tag[1:]
                    if clean.startswith("#"):
                        if style_stack:
                            prev = style_stack.pop()
                            current_fg = str(prev.get("fg", ""))
                            current_bold = bool(prev.get("bold", False))
                            current_dim = bool(prev.get("dim", False))
                    elif clean == "bold":
                        if style_stack:
                            prev = style_stack.pop()
                            current_bold = bool(prev.get("bold", False))
                    elif clean == "dim":
                        if style_stack.pop():
                            current_dim = bool(style_stack[-1].get("dim", False)) if style_stack else False
                else:
                    style_stack.append({
                        "fg": current_fg,
                        "bg": current_bg,
                        "bold": current_bold,
                        "dim": current_dim,
                    })
                    if tag.startswith("#") or tag.startswith("rgb"):
                        current_fg = self._ansi_color(tag)
                    elif tag == "bold":
                        current_bold = True
                    elif tag == "dim":
                        current_dim = True

                i = end + 1
                continue

            cells[col] = Cell(
                char=ch,
                fg=current_fg,
                bg=current_bg,
                bold=current_bold,
                dim=current_dim,
            )
            col += 1
            i += 1

        return cells

    def render(self, frame: str, out: TextIO | None = None) -> None:
        """Render a frame to stdout, only updating changed cells.

        Args:
            frame: Multi-line string (plain ANSI or Rich-markup).
                   Each line becomes one row.
            out: File-like object (default: sys.stdout).
        """
        if out is None:
            out = sys.stdout

        lines = frame.split("\n")
        row_count = min(len(lines), self.height)

        if not self._initialized:
            out.write("\033[2J\033[H")
            out.write(ANSI_RESET)
            self._initialized = True

        out.write("\033[?25l")  # hide cursor

        diffs = 0

        for row in range(row_count):
            line = lines[row]
            new_cells = self._parse_rich_line(line, row)
            modified = False
            run_start = -1
            run_text: list[str] = []

            for col in range(self.width):
                old = self._grid[row][col]
                new = new_cells[col]
                if old != new:
                    diffs += 1
                    if not modified:
                        modified = True
                        run_start = col
                        run_text = []
                    run_text.append(new.to_ansi())
                    self._grid[row][col] = new
                elif modified:
                    self._flush_run(out, row + 1, run_start + 1, run_text)
                    modified = False

            if modified:
                self._flush_run(out, row + 1, run_start + 1, run_text)

        out.write("\033[?25h")  # show cursor
        out.flush()

        self._frame_count += 1
        self._total_diffs += diffs

    def _flush_run(
        self, out: TextIO, row: int, col: int, text: list[str]
    ) -> None:
        """Write a contiguous run of changed cells at (row, col)."""
        out.write(self._ansi_move(row, col))
        out.write("".join(text))
        out.write(ANSI_RESET)

    def stats(self) -> dict[str, object]:
        return {
            "frames": self._frame_count,
            "total_diffs": self._total_diffs,
            "avg_diffs_per_frame": (
                self._total_diffs / max(1, self._frame_count)
            ),
        }


def split_into_cells(text: str, width: int = 80) -> list[list[str]]:
    """Split multi-line text into per-line character lists, padded to width."""
    lines = text.split("\n")
    result: list[list[str]] = []
    for line in lines:
        chars = list(line)
        chars.extend([" "] * max(0, width - len(chars)))
        result.append(chars[:width])
    while len(result) < 24:
        result.append([" "] * width)
    return result


def diff_and_patch(
    old_lines: list[str],
    new_lines: list[str],
) -> Iterator[tuple[int, int, str]]:
    """Yield (row, col, ansi_text) for changed cells between two frames."""
    for row, (old, new) in enumerate(zip(old_lines, new_lines, strict=False)):
        for col in range(max(len(old), len(new))):
            oc = old[col] if col < len(old) else " "
            nc = new[col] if col < len(new) else " "
            if oc != nc:
                yield (row + 1, col + 1, nc)
