# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Staged error animations — no startle reflex.

Error messages appear neutral, then smoothly transition to warning,
then to error color. This gives the brain time to read the message
BEFORE the color signals 'bad'. Removes the startle response.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto


class ErrorStage(Enum):
    """ErrorStage."""
    NEUTRAL = auto()
    WARNING = auto()
    ERROR = auto()
    FADING = auto()


@dataclass
class StagedError:
    """StagedError."""
    message: str
    _started_at: float
    _stage: ErrorStage = ErrorStage.NEUTRAL

    NEUTRAL_DURATION = 0.3
    WARNING_DURATION = 0.2
    ERROR_DURATION = 3.0
    FADE_DURATION = 0.4

    @property
    def stage(self) -> ErrorStage:
        """Stage."""
        elapsed = time.monotonic() - self._started_at
        if elapsed < self.NEUTRAL_DURATION:
            return ErrorStage.NEUTRAL
        elif elapsed < self.NEUTRAL_DURATION + self.WARNING_DURATION:
            return ErrorStage.WARNING
        elif elapsed < self.NEUTRAL_DURATION + self.WARNING_DURATION + self.ERROR_DURATION:
            return ErrorStage.ERROR
        return ErrorStage.FADING

    @property
    def is_expired(self) -> bool:
        """Check if expired."""
        total = (
            self.NEUTRAL_DURATION
            + self.WARNING_DURATION
            + self.ERROR_DURATION
            + self.FADE_DURATION
        )
        return (time.monotonic() - self._started_at) > total

    def ansi_color(self) -> str:
        """Ansi color."""
        s = self.stage
        elapsed = time.monotonic() - self._started_at

        if s == ErrorStage.NEUTRAL:
            return "\033[96m"  # cyan — neutral, readable
        elif s == ErrorStage.WARNING:
            t = elapsed - self.NEUTRAL_DURATION
            fade = t / max(0.001, self.WARNING_DURATION)
            r = int(0x06 + (0xE0 - 0x06) * fade * 0.5)
            g = int(0xD6 + (0x40 - 0xD6) * fade * 0.5)
            b = int(0xA0 + (0xFB - 0xA0) * fade * 0.5)
            return f"\033[38;2;{r};{g};{b}m"
        elif s == ErrorStage.ERROR:
            return "\033[91m"  # red — now it's safe to signal 'bad'
        elif s == ErrorStage.FADING:
            t = elapsed - (self.NEUTRAL_DURATION + self.WARNING_DURATION + self.ERROR_DURATION)
            fade = 1.0 - (t / max(0.001, self.FADE_DURATION))
            r = int(0x80 * fade)
            g = int(0x40 * fade)
            b = int(0x40 * fade)
            return f"\033[38;2;{r};{g};{b}m"
        # FADING branch already handles the return

    def rich_color(self) -> str:
        """Rich-markup color for staged error."""
        s = self.stage
        if s == ErrorStage.NEUTRAL:
            return "#06d6a0"
        elif s == ErrorStage.WARNING:
            return "#FFD93D"
        elif s == ErrorStage.ERROR:
            return "#e040fb"
        return "dim"

    def render(self) -> str:
        """Full ANSI-styled error string."""
        return f"{self.ansi_color()}{self.message}\033[0m"


def staged_error(message: str) -> StagedError:
    """Create a staged error — returns immediately, animates over time."""
    return StagedError(message=message, _started_at=time.monotonic())


def print_staged_error(message: str) -> None:
    """Print error message with staged color transition."""
    err = staged_error(message)
    import sys
    sys.stdout.write(f"\n{err.render()}\n")
    sys.stdout.flush()
