# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Cube breathing idle animation — frequency by CogLoad.

When TUI/REPL is idle for N seconds, the cube begins a slow
pulse animation. Breathing rate adapts to cognitive load level.

C1 (light):  slow breath  — 4s cycle, subtle
C2 (medium): normal breath — 2.5s cycle
C3 (heavy):  fast breath   — 1.5s cycle, tense
"""
from __future__ import annotations

import math
import time


BREATHING_CHARS_LIGHT = [" ", "░", "▒", "▓"]
BREATHING_CHARS_HEAVY = [" ", "·", "◈", "◇", "◆"]


class CubeBreathing:
    """Idle breathing animation controller."""

    def __init__(
        self,
        idle_threshold: float = 5.0,
        cogload: int = 1,
    ) -> None:
        self.idle_threshold = idle_threshold
        self.cogload = cogload
        self._last_activity = time.monotonic()
        self._breath_start: float | None = None

    @property
    def is_breathing(self) -> bool:
        """True when the cube should be animating its breath."""
        if self._breath_start is not None:
            return True
        idle_time = time.monotonic() - self._last_activity
        return idle_time >= self.idle_threshold

    def activity(self) -> None:
        """Reset idle timer — user performed an action."""
        self._last_activity = time.monotonic()
        self._breath_start = None

    def start_breathing(self) -> None:
        self._breath_start = time.monotonic()

    def stop_breathing(self) -> None:
        self._breath_start = None

    def set_cogload(self, level: int) -> None:
        self.cogload = max(1, min(3, level))

    def cycle_duration(self) -> float:
        """Seconds per breath cycle based on CogLoad."""
        durations = {1: 4.0, 2: 2.5, 3: 1.5}
        return durations.get(self.cogload, 2.5)

    def breath_phase(self) -> float:
        """Current phase of the breath: 0.0 (rest) → 1.0 (expand) → 0.0.

        Uses a sine wave shaped to look like natural breathing:
        slow inhale (0→1 over 60%), hold (60-65%), faster exhale (65→100%).
        """
        if self._breath_start is None:
            return 0.0

        elapsed = time.monotonic() - self._breath_start
        cycle = self.cycle_duration()
        t = (elapsed % cycle) / cycle

        if t < 0.60:
            phase = t / 0.60
            return math.sin(phase * math.pi / 2.0)
        elif t < 0.65:
            return 1.0
        else:
            phase = (t - 0.65) / 0.35
            return 1.0 - math.sin(phase * math.pi / 2.0)

    def intensity(self) -> float:
        """Breath intensity 0.0 → 1.0, with CogLoad-dependent amplitude."""
        base = self.breath_phase()
        amplitudes = {1: 0.3, 2: 0.6, 3: 0.9}
        amp = amplitudes.get(self.cogload, 0.6)
        return base * amp


def breathing_pulse_frame(
    base_char: str = "▐",
    phase: float = 0.0,
    chars: list[str] | None = None,
) -> str:
    """Select a breathing character based on phase [0, 1].

    At phase=0 → base_char (normal).
    At phase=1 → maximum pulse character (e.g., '◆' or '▓').
    """
    if chars is None:
        chars = BREATHING_CHARS_LIGHT
    idx = int(phase * (len(chars) - 1))
    idx = max(0, min(len(chars) - 1, idx))
    return chars[idx]


def breathing_glow_ansi(phase: float, cogload: int = 1) -> str:
    """ANSI escape for frame-glowing border based on breath phase."""
    cyan = (0x06, 0xD6, 0xA0)
    magenta = (0xE0, 0x40, 0xFB)
    intensity = phase * (0.3 if cogload <= 1 else 0.7 if cogload == 2 else 1.0)
    r = int(cyan[0] + (magenta[0] - cyan[0]) * phase * 0.5)
    g = int(cyan[1] + (magenta[1] - cyan[1]) * phase * 0.5)
    b = int(cyan[2] + (magenta[2] - cyan[2]) * phase * 0.5)

    r2 = int(r * (0.6 + 0.4 * intensity))
    g2 = int(g * (0.6 + 0.4 * intensity))
    b2 = int(b * (0.6 + 0.4 * intensity))

    return f"\033[38;2;{r2};{g2};{b2}m"
