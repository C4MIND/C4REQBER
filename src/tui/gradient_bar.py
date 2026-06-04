# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Unicode gradient progress bars with dual-color glow.

▊▊▊▊▋▋▌▌▍▍▎▏ — 8-block gradient from solid → faint.
Plus trailing glow: last 3 chars in accent color.
"""
from __future__ import annotations

import math
import time


GRADIENT_CHARS = "█▊▋▌▍▎▏░"
FULL_BLOCK_7 = "█▓▒░ ░▒▓█"
FULL_BLOCK_4 = "█▓▒░"


def make_gradient_bar(
    fraction: float,
    width: int = 30,
    glow_color: str = "",
    base_color: str = "",
    gradient_chars: str = GRADIENT_CHARS,
    glow_width: int = 3,
    pulse: bool = False,
    pulse_phase: float | None = None,
) -> str:
    """Build a Unicode gradient progress bar.

    Args:
        fraction: 0.0 to 1.0 progress
        width: total bar width in characters
        glow_color: ANSI/Rich color for the glow tail (e.g. '#e040fb')
        base_color: ANSI/Rich color for the solid portion
        gradient_chars: sequence of chars from solid to faint
        glow_width: how many chars at the transition edge get glow_color
        pulse: if True, the glow section oscillates
        pulse_phase: override automatic pulse phase

    Returns:
        Rich-markup string or plain string (depending on colors passed)
    """
    fraction = max(0.0, min(1.0, fraction))
    filled_units = fraction * width * 8  # 8 sub-units per char
    full_chars = int(filled_units // 8)
    remainder = int(filled_units % 8)

    g_len = len(gradient_chars)

    bar = ""
    for i in range(width):
        if i < full_chars:
            bar += gradient_chars[0]
        elif i == full_chars and remainder > 0:
            idx = min(g_len - 1, max(1, g_len - remainder))
            bar += gradient_chars[g_len - idx]
        else:
            bar += gradient_chars[-1]

    if not glow_color:
        return bar

    bar_list = list(bar)
    pulse_amt = 0.0
    if pulse:
        if pulse_phase is None:
            pulse_phase = (time.monotonic() * 0.7) % 1.0
        pulse_amt = (math.sin(pulse_phase * math.pi * 2.0) + 1.0) / 2.0

    actual_glow = max(1, int(glow_width * (1.0 - pulse_amt * 0.5)))
    glow_start = max(0, full_chars - actual_glow + 1)
    glow_end = min(width, full_chars + 2)

    result = ""
    for i, ch in enumerate(bar_list):
        if glow_start <= i <= glow_end:
            if glow_color.startswith("#"):
                result += f"[{glow_color}]{ch}[/{glow_color}]"
            else:
                result += f"{glow_color}{ch}"
        elif base_color and i < full_chars:
            if base_color.startswith("#"):
                result += f"[{base_color}]{ch}[/{base_color}]"
            else:
                result += ch
        else:
            result += ch

    return result


def make_dual_gradient(
    fraction: float,
    width: int = 30,
    primary_color: str = "#06d6a0",
    accent_color: str = "#e040fb",
) -> str:
    """Rich-markup gradient bar with primary-fill and accent-glow tail."""
    return make_gradient_bar(
        fraction=fraction,
        width=width,
        glow_color=accent_color,
        base_color=primary_color,
        glow_width=3,
    )


def make_pulsing_bar(
    fraction: float,
    width: int = 30,
) -> str:
    """Gradient bar that pulses the glow area. Use inside a 60fps loop."""
    return make_gradient_bar(
        fraction=fraction,
        width=width,
        glow_color="#e040fb",
        base_color="#06d6a0",
        glow_width=4,
        pulse=True,
    )


def make_substep_bar(
    current: int,
    total: int,
    substeps: int = 8,
    width: int = 20,
) -> str:
    """Fixed-width bar with finer resolution via Unicode 1/8 blocks.

    Each main step gets substeps sub-units, rendered with █▊▋▌▍▎▏░.
    """
    if total <= 0:
        return GRADIENT_CHARS[-1] * width
    total_units = total * substeps
    current_units = current * substeps
    fraction = current_units / max(1, total_units)
    return make_gradient_bar(fraction, width)


def make_spark_bar(
    fraction: float,
    width: int = 30,
) -> str:
    """Bidirectional gradient: ░▒▓█▓▒░ — peak at progress point."""
    fraction = max(0.0, min(1.0, fraction))
    center = int(fraction * (width - 1))
    chars: list[str] = []

    for i in range(width):
        dist = abs(i - center)
        max_dist = max(center, width - 1 - center, 1)
        t = dist / max_dist
        if t <= 0.125:
            chars.append("█")
        elif t <= 0.25:
            chars.append("▓")
        elif t <= 0.5:
            chars.append("▒")
        elif t <= 0.75:
            chars.append("░")
        else:
            chars.append(" ")

    return "".join(chars)


def make_phase_bar(
    phase: str,
    fraction: float,
    width: int = 30,
) -> str:
    """Progress bar with cyan→magenta phase label before the bar.

    phase: 'A' through 'G' or custom label
    """
    label = f"[bold #06d6a0]{phase}[/bold #06d6a0] "
    bar_width = max(5, width - len(phase) - 2)
    bar = make_dual_gradient(fraction, bar_width)
    return f"{label}{bar}"
