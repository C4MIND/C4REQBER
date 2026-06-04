# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""REPL input handler with per-keystroke spark particles and ghost-text completion.

Replaces cmd.Cmd's default readline input with raw-terminal character-by-character
reading, enabling:
  - Spark particles on each keypress
  - Ghost text inline completion preview
  - Tab-based word completion
  - Cursor state indicator (block/underline/beam by C4 depth)
"""
from __future__ import annotations

import select
import sys
import termios
import time
import tty

from src.tui.particles import CursorSparkEffect
from src.tui.smart_prompt import find_ghost_completion, render_ghost_text


_GHOST = "\033[2m\033[90m"
_RESET = "\033[0m"
_CURSOR_SAVE = "\033[s"
_CURSOR_RESTORE = "\033[u"
_ERASE_LINE = "\033[2K"


class ReplInput:
    """Raw-terminal REPL input with particles, ghost text, and Tab completion."""

    _HISTORY: list[str] = []
    _HISTORY_IDX = -1

    def __init__(
        self,
        prompt: str = "c4reqber ❯ ",
        spark: CursorSparkEffect | None = None,
        cogload: int = 1,
    ) -> None:
        self._prompt = prompt
        self._spark = spark or CursorSparkEffect()
        self._cogload = cogload
        self._cursor_col = len(prompt)

    def set_cogload(self, level: int) -> None:
        self._cogload = max(1, min(3, level))

    def set_prompt(self, prompt: str) -> None:
        """Set prompt."""
        self._prompt = prompt
        self._cursor_col = len(prompt)

    def readline(self) -> str | None:
        """Read a line with spark particles and ghost text. Returns None on EOF."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            return self._raw_readline()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _raw_readline(self) -> str | None:
        buffer: list[str] = []
        ghost: str | None = None
        col = 0

        self._cursor_style()
        self._redraw(buffer, col, ghost, initial=True)

        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if not ch:
                    return None
                ord_ch = ord(ch)

                if ord_ch in (10, 13):  # Enter
                    sys.stdout.write(f"\r{_ERASE_LINE}\r{self._prompt}")
                    result = "".join(buffer)
                    sys.stdout.write(result + "\r\n")
                    sys.stdout.flush()
                    if result.strip():
                        if not self._HISTORY or self._HISTORY[-1] != result:
                            self._HISTORY.append(result)
                        self._HISTORY_IDX = len(self._HISTORY)
                    return result

                elif ord_ch == 127 or ch == "\b":  # Backspace
                    if col > 0:
                        col -= 1
                        buffer.pop(col)
                        ghost = find_ghost_completion("".join(buffer))
                    self._redraw(buffer, col, ghost)

                elif ord_ch == 9:  # Tab
                    current = "".join(buffer)
                    ghost_suffix = find_ghost_completion(current)
                    if ghost_suffix:
                        buffer.extend(list(ghost_suffix))
                        col = len(buffer)
                        ghost = None
                        self._spark.burst(self._cursor_col + col, 2)
                    self._redraw(buffer, col, ghost)

                elif ord_ch == 27:  # Escape sequence (arrows)
                    seq = ""
                    for _ in range(2):
                        if select.select([sys.stdin], [], [], 0.05)[0]:
                            seq += sys.stdin.read(1)
                    if seq == "[C" and col < len(buffer):  # Right arrow
                        col += 1
                        self._redraw(buffer, col, ghost)
                    elif seq == "[D" and col > 0:  # Left arrow
                        col -= 1
                        self._redraw(buffer, col, ghost)
                    elif seq == "[A" and self._HISTORY:  # Up arrow
                        if self._HISTORY_IDX > 0:
                            self._HISTORY_IDX -= 1
                            buffer[:] = list(self._HISTORY[self._HISTORY_IDX])
                            col = len(buffer)
                            ghost = None
                            self._redraw(buffer, col, ghost)
                    elif seq == "[B" and self._HISTORY:  # Down arrow
                        if self._HISTORY_IDX < len(self._HISTORY) - 1:
                            self._HISTORY_IDX += 1
                            buffer[:] = list(self._HISTORY[self._HISTORY_IDX])
                            col = len(buffer)
                            ghost = None
                            self._redraw(buffer, col, ghost)
                        elif self._HISTORY_IDX == len(self._HISTORY) - 1:
                            self._HISTORY_IDX = len(self._HISTORY)
                            buffer.clear()
                            col = 0
                            ghost = None
                            self._redraw(buffer, col, ghost)

                elif ch == "\x03":  # Ctrl+C
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    raise KeyboardInterrupt

                elif ch == "\x04":  # Ctrl+D
                    if not buffer:
                        return None
                    # Delete forward (like readline)
                    if col < len(buffer):
                        buffer.pop(col)
                        ghost = find_ghost_completion("".join(buffer))
                    self._redraw(buffer, col, ghost)

                elif ord_ch >= 32:  # Printable
                    buffer.insert(col, ch)
                    col += 1
                    self._spark.burst(self._cursor_col + col, 2)
                    ghost = find_ghost_completion("".join(buffer))
                    self._redraw(buffer, col, ghost)

            # Process spark particles even when no key pressed
            if self._spark.is_alive():
                self._paint_sparks()
                time.sleep(0.02)

    def _redraw(
        self,
        buffer: list[str],
        col: int,
        ghost: str | None,
        initial: bool = False,
    ) -> None:
        """Redraw the input line with cursor at col."""
        text = "".join(buffer)
        display = render_ghost_text(text, ghost)

        self._paint_sparks()

        sys.stdout.write(f"\r{_ERASE_LINE}\r{self._prompt}{display}")
        if col < len(buffer):
            sys.stdout.write(f"\r{self._prompt}{text[:col]}")
        sys.stdout.flush()

    def _paint_sparks(self) -> None:
        """Render spark particles near the cursor line."""
        if not self._spark.is_alive():
            return

        now = time.monotonic()
        dt = 0.03
        for col_p, row_p, char, ansi in self._spark.tick(dt):
            if row_p >= 0:
                sys.stdout.write(f"{_CURSOR_SAVE}\033[{1};{col_p + 1}H{ansi}{char}{_RESET}{_CURSOR_RESTORE}")

    def _cursor_style(self) -> None:
        """Set cursor style based on CogLoad depth."""
        if self._cogload >= 3:
            sys.stdout.write("\033[1 q")  # blinking block
        elif self._cogload >= 2:
            sys.stdout.write("\033[3 q")  # blinking underline
        else:
            sys.stdout.write("\033[5 q")  # blinking bar
        sys.stdout.write("\033]12;#06d6a0\a")  # cursor color cyan


def repl_input(prompt: str = "c4reqber ❯ ") -> str | None:
    """Convenience function — drop-in replacement for input()."""
    return ReplInput(prompt=prompt).readline()
