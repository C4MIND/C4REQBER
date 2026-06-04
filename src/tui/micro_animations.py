# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Micro-animations — the things you don't notice until they're gone.

ShakeVibrato: subtle horizontal shake on cube navigation (2-cell, 150ms).
PhaseSwoosh: directional sweep between pipeline stages (A→B→C...).
"""
from __future__ import annotations

import math
import time


class ShakeVibrato:
    """Subtle horizontal shake — like haptic feedback, but visual.

    When navigating the cube, applies a brief horizontal wobble:
    `"  ◆  "` → `" ◆   "` → `"  ◆  "` → settles.
    """

    DURATION = 0.15
    AMPLITUDE = 2
    FREQUENCY = 20.0

    def __init__(self) -> None:
        self._start: float | None = None
        self._amplitude: float = float(self.AMPLITUDE)

    def trigger(self, intensity: float = 1.0) -> None:
        """Trigger."""
        self._start = time.monotonic()
        self._amplitude = self.AMPLITUDE * intensity

    @property
    def active(self) -> bool:
        """Active."""
        if self._start is None:
            return False
        return (time.monotonic() - self._start) < self.DURATION

    def offset(self) -> int:
        """Current horizontal offset (−amplitude to +amplitude)."""
        if not self.active or self._start is None:
            return 0
        elapsed = time.monotonic() - self._start
        decay = 1.0 - (elapsed / self.DURATION)
        wave = math.sin(elapsed * self.FREQUENCY * 2.0 * math.pi)
        return int(self._amplitude * decay * wave)


class PhaseSwoosh:
    """Directional sweep between pipeline phases.

    When advancing from phase A to B, shows a brief cyan→magenta
    directional arrow sweep across one line.
    """

    SWOOSH_CHARS = "▁▂▃▄▅▆▇█"
    DURATION = 0.18

    def __init__(self, width: int = 40) -> None:
        self.width = width
        self._start: float | None = None
        self._from_phase = "A"
        self._to_phase = "B"

    def trigger(self, from_phase: str, to_phase: str) -> None:
        """Trigger."""
        self._start = time.monotonic()
        self._from_phase = from_phase
        self._to_phase = to_phase

    @property
    def active(self) -> bool:
        """Active."""
        if self._start is None:
            return False
        return (time.monotonic() - self._start) < self.DURATION

    def render_rich(self) -> str:
        """Rich-markup swoosh bar for TUI display."""
        if not self.active or self._start is None:
            return ""
        elapsed = time.monotonic() - self._start
        t = min(1.0, elapsed / self.DURATION)

        pos = int(t * self.width)
        bar = ["·"] * self.width

        l = len(self.SWOOSH_CHARS)
        for i in range(pos):
            idx = min(l - 1, i % l)
            bar[i] = self.SWOOSH_CHARS[idx]
        for i in range(max(0, pos - 2), min(self.width, pos + 3)):
            bar[i] = "█"

        swoosh = "".join(bar)
        return (
            f"[dim]{self._from_phase}[/] "
            f"[bold #06d6a0]{swoosh}[/] "
            f"[bold #e040fb]{self._to_phase}[/]"
        )

    def render_plain(self) -> str:
        """Plain ANSI swoosh for non-Rich contexts (REPL)."""
        if not self.active or self._start is None:
            return ""
        elapsed = time.monotonic() - self._start
        t = min(1.0, elapsed / self.DURATION)
        pos = int(t * self.width)
        bar = ["·"] * self.width
        for i in range(pos):
            bar[i] = "█"
        for i in range(max(0, pos - 1), min(self.width, pos + 2)):
            bar[i] = "▓"

        return (
            f"\033[2m{self._from_phase}\033[0m "
            f"\033[96m{''.join(bar)}\033[0m "
            f"\033[95m{self._to_phase}\033[0m"
        )


class AdaptiveWaiter:
    """Rotating contextual wait messages — not just 'Initializing...'."""

    _POOLS: dict[str, list[str]] = {
        "startup": [
            "Waking the cube...",
            "Loading C4 topology...",
            "Theorem 11: connecting states...",
            "Calibrating 27 dimensions...",
            "6 operators warming up...",
        ],
        "search": [
            "Scanning 28 knowledge sources...",
            "arXiv · Semantic Scholar · PubMed...",
            "Reddit · HN · NewsAPI collecting...",
            "Indexing recent papers...",
            "Semantic dedup in progress...",
        ],
        "verify": [
            "Lean4 prover initializing...",
            "Coq tactics prepared...",
            "Z3 SAT solver warming...",
            "MathDetector classifying...",
            "Formal verification guardrails active...",
        ],
        "simulate": [
            "Physics engine booting...",
            "OpenMM · Vina · COBRApy loading...",
            "GPU compute ready...",
            "In-silico environment preparing...",
            "Monte Carlo seeds planted...",
        ],
        "export": [
            "Formatting dissertation...",
            "Preparing LaTeX package...",
            "BibTeX references compiling...",
            "Generating HTML dashboard...",
            "Export pipeline running...",
        ],
    }

    def __init__(self, pool: str = "startup") -> None:
        self._pool = pool
        self._idx = 0
        self._last_rotation = time.monotonic()
        self._rotation_interval = 0.8

    def tick(self, phase: str = "") -> str:
        """Get current wait message, rotating every 0.8s."""
        now = time.monotonic()
        if now - self._last_rotation > self._rotation_interval:
            self._last_rotation = now
            self._idx += 1

        if phase and phase in self._POOLS:
            messages = self._POOLS.get(phase, self._POOLS["startup"])
        else:
            messages = self._POOLS.get(self._pool, self._POOLS["startup"])

        return messages[self._idx % len(messages)]

    def set_phase(self, phase: str) -> None:
        """Set phase."""
        self._pool = phase
        self._idx = 0
