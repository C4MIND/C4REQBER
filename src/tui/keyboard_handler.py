"""
TUI: Keyboard Handler
Non-blocking keyboard input reader using raw terminal mode.
"""
from __future__ import annotations

import select
import sys
import termios
import tty
from typing import Any


class KeyboardReader:
    """Non-blocking keyboard input reader using raw terminal mode."""

    def __init__(self) -> None:
        self.fd = sys.stdin.fileno()
        self.old_settings: list[Any] | None = None

    def __enter__(self) -> KeyboardReader:
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        return self

    def __exit__(self, *args) -> None:
        assert self.old_settings is not None
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def read_key(self, timeout: float = 0.1) -> tuple[str, ...] | str | None:
        """Read a single keypress with timeout. Returns None if no key."""
        r, _, _ = select.select([sys.stdin], [], [], timeout)
        if r:
            ch = sys.stdin.read(1)
            if ch == '\x03':
                raise KeyboardInterrupt()
            if ch == '\x1b':
                r2, _, _ = select.select([sys.stdin], [], [], 0.0)
                if r2:
                    next_ch = sys.stdin.read(1)
                    if next_ch == '[':
                        r3, _, _ = select.select([sys.stdin], [], [], 0.0)
                        if r3:
                            third = sys.stdin.read(1)
                            if third == 'A':
                                return ('arrow', 'up')
                            elif third == 'B':
                                return ('arrow', 'down')
                            elif third == 'C':
                                return ('arrow', 'right')
                            elif third == 'D':
                                return ('arrow', 'left')
                        return ('esc_bracket',)
                    elif next_ch == 'O':
                        return ('esc_O',)
                else:
                    return ('esc',)
            if ch == '\t':
                return ('tab',)
            if ch == '\n' or ch == '\r':
                return ('enter',)
            if ch == '\x7f' or ch == '\x08':
                return ('backspace',)
            if ch == ' ':
                return ('space',)
            return ('char', ch)
        return None
