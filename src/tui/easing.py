# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Physics easing curves for smooth animations — cubic, elastic, inertia.

Usage:
    pos = ease_out_cubic(t)          # t in [0.0, 1.0] → eased position
    step = inertia_step(velocity, dt, friction=0.92)  # physics simulation
"""
from __future__ import annotations

import math
import time
from typing import Callable


EasingFn = Callable[[float], float]


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out — fast start, gradual deceleration. Like a rolling ball."""
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out — smooth acceleration then deceleration. Flywheel feel."""
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out — overshoots then settles. Like a spring doorstop."""
    if t == 0.0 or t == 1.0:
        return t
    c4 = (2.0 * math.pi) / 3.0
    return pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) + 1.0


def ease_out_back(t: float) -> float:
    """Back ease-out — overshoots slightly, then returns. Premium UI feel."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(t - 1.0, 3) + c1 * pow(t - 1.0, 2)


def ease_out_quart(t: float) -> float:
    """Quartic ease-out — faster than cubic, heavier deceleration."""
    return 1.0 - pow(1.0 - t, 4)


def ease_out_expo(t: float) -> float:
    """Exponential ease-out — very fast start, long tail. Particle-like."""
    if t == 1.0:
        return 1.0
    return 1.0 - pow(2.0, -10.0 * t)


EASING_MAP: dict[str, EasingFn] = {
    "cubic": ease_out_cubic,
    "in_out_cubic": ease_in_out_cubic,
    "elastic": ease_out_elastic,
    "back": ease_out_back,
    "quart": ease_out_quart,
    "expo": ease_out_expo,
}


class InertiaSimulation:
    """Simulates physical inertia for UI elements (cube, cursors, scroll).

    Like a car coasting — velocity decays with friction.
    Position is the integral of velocity over time.
    """

    def __init__(self, friction: float = 0.92, mass: float = 1.0) -> None:
        self.friction = friction
        self.mass = mass
        self.velocity = 0.0
        self.position = 0.0
        self._last_tick: float | None = None

    def tick(self, dt: float) -> float:
        """Advance physics by dt seconds. Returns new position."""
        self.velocity *= self.friction
        self.position += self.velocity * dt
        return self.position

    def push(self, force: float) -> None:
        """Apply instantaneous impulse."""
        self.velocity += force / self.mass

    def auto_tick(self) -> float:
        """Tick using real elapsed time since last call."""
        now = time.monotonic()
        if self._last_tick is None:
            self._last_tick = now
            return self.position
        dt = now - self._last_tick
        self._last_tick = now
        return self.tick(dt)

    def is_still(self, threshold: float = 0.001) -> bool:
        """True when velocity is negligible."""
        return abs(self.velocity) < threshold
