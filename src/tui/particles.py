# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Particle system for cursor sparkles and discovery fireworks.

CursorParticles — spark bursts on keypress (REPL/TUI input).
Fireworks — Unicode confetti on high-confidence discovery completion.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterator


PARTICLE_CHARS = ["·", "✦", "◈", "◇", "◆", "•", "⋆", "✧", ".", "*"]


@dataclass
class Particle:
    """Particle."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    char: str
    color: str = ""


class CursorSparkEffect:
    """Brief particle burst from cursor position on keypress.

    Renders as inline ANSI: sparks fly right and fade in ~300ms.
    Non-blocking — meant to be ticked concurrently with the REPL loop.
    """

    GRAVITY = 2.5      # symbols/s² — gentle downward arc
    FRICTION = 0.85    # per tick velocity decay
    MAX_LIFE = 0.35    # seconds
    SPAWN_COUNT = 5    # particles per burst

    def __init__(self) -> None:
        self._particles: list[Particle] = []

    def is_alive(self) -> bool:
        return len(self._particles) > 0

    def burst(self, cursor_col: int = 0, cursor_row: int = 0) -> None:
        """Spawn a spark burst at cursor position."""
        for _ in range(self.SPAWN_COUNT):
            angle = random.uniform(-0.3, 0.6)
            speed = random.uniform(4.0, 12.0)
            p = Particle(
                x=float(cursor_col),
                y=float(cursor_row),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - 2.0,
                life=random.uniform(0.2, self.MAX_LIFE),
                char=random.choice(PARTICLE_CHARS),
                color=random.choice(["#06d6a0", "#e040fb", "#FFD93D"]),
            )
            self._particles.append(p)

    def tick(self, dt: float) -> Iterator[tuple[int, int, str, str]]:
        """Advance physics by dt. Yields (col, row, char, ansi_color) for rendering."""
        alive: list[Particle] = []

        for p in self._particles:
            p.life -= dt
            if p.life <= 0.0:
                continue
            p.vy += self.GRAVITY * dt
            p.vx *= self.FRICTION
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)

            col = int(p.x)
            row = int(p.y)
            if col < 0 or row < 0:
                continue

            opacity = min(1.0, p.life / self.MAX_LIFE)
            if opacity < 0.15:
                continue

            ansi = _make_ansi(p.color, opacity)
            yield (col, row, p.char, ansi)

        self._particles = alive


class DiscoveryFireworks:
    """Confetti explosion on high-confidence discovery (>80%).

    Spawns 80-120 particles with physics, gravity, and color cycling.
    Renders over multiple frames (~2 seconds).
    """

    GRAVITY = 9.8
    SPAWN_COUNT = 100
    DURATION = 2.0

    def __init__(self, width: int = 80, height: int = 20) -> None:
        self.width = width
        self.height = height
        self._particles: list[Particle] = []
        self._elapsed = 0.0
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def start(self) -> None:
        """Detonate fireworks from center of screen."""
        cx = self.width / 2.0
        cy = self.height * 0.6

        colors = [
            "#06d6a0", "#e040fb", "#FFD93D", "#4ECDC4",
            "#FF6B6B", "#FFE66D", "#A78BFA", "#34D399",
        ]

        for _ in range(self.SPAWN_COUNT):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3.0, 18.0)
            p = Particle(
                x=cx,
                y=cy,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - random.uniform(3.0, 10.0),
                life=random.uniform(1.2, self.DURATION),
                char=random.choice(PARTICLE_CHARS),
                color=random.choice(colors),
            )
            self._particles.append(p)

        self._elapsed = 0.0
        self._active = True

    def tick(self, dt: float) -> Iterator[tuple[int, int, str, str]]:
        """Advance physics. Yields (col, row, char, ansi_color)."""
        self._elapsed += dt
        alive: list[Particle] = []

        for p in self._particles:
            p.life -= dt
            if p.life <= 0.0:
                continue
            p.vy += self.GRAVITY * dt
            p.vx *= 0.99
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)

            col = int(p.x)
            row = int(p.y)
            if not (0 <= col < self.width and 0 <= row < self.height):
                continue

            opacity = min(1.0, p.life / self.DURATION)
            if opacity < 0.1:
                continue

            ansi = _make_ansi(p.color, opacity)
            yield (col, row, p.char, ansi)

        self._particles = alive
        if not alive and self._elapsed > 0.3:
            self._active = False

    def render_frame(self, dt: float) -> str:
        """Render one frame of fireworks to a screen-sized string.

        Returns plain text with ANSI escape codes — overwrites entire
        screen. Use only for standalone fireworks display, not during
        TUI operation.
        """
        grid = [[" "] * self.width for _ in range(self.height)]

        for col, row, char, ansi in self.tick(dt):
            grid[row][col] = f"{ansi}{char}\033[0m"

        return "\n".join("".join(row) for row in grid)

    def render_overlay(self, dt: float, base_frame: str) -> str:
        """Overlay fireworks particles on top of a base frame string.

        Returns the combined frame for direct terminal output.
        """
        lines = base_frame.split("\n")
        pending: list[tuple[int, int, str, str]] = list(self.tick(dt))

        if not pending:
            return base_frame

        for col, row, char, ansi in pending:
            if 0 <= row < len(lines) and 0 <= col < len(lines[row]):
                orig = lines[row]
                lines[row] = orig[:col] + f"{ansi}{char}\033[0m" + orig[col + 1:]

        return "\n".join(lines)


def _make_ansi(hex_color: str, opacity: float) -> str:
    """ANSI truecolor with optional dim for opacity simulation."""
    if not hex_color or not hex_color.startswith("#"):
        return ""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return ""
    r = int(int(h[0:2], 16) * opacity)
    g = int(int(h[2:4], 16) * opacity)
    b = int(int(h[4:6], 16) * opacity)
    return f"\033[38;2;{r};{g};{b}m"
