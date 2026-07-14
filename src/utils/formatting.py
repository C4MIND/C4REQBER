# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Number and unit formatters — no raw floats in UI. Premium feel.

fmt_count(1234)       → "1.2K"
fmt_dollars(0.041231) → "$0.041"
fmt_duration(134.7)   → "2m 14s"
fmt_bytes(1_500_000)  → "1.4 MB"
fmt_percent(0.85612)  → "85.6%"
"""
from __future__ import annotations

import time


Number = int | float


def fmt_count(n: Number) -> str:
    """Human-readable count: 1234 → '1.2K', 1_500_000 → '1.5M'."""
    n = int(n)
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}K"
    if n < 1_000_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n / 1_000_000_000:.1f}B"


def fmt_dollars(n: Number) -> str:
    """Compact dollar amount: 0.041231 → '$0.041', 0.0 → '$0.000'."""
    if n == 0:
        return "$0.000"
    n = float(n)
    if abs(n) < 0.001:
        return f"${n:.6f}".rstrip("0").rstrip(".")
    if abs(n) < 0.01:
        return f"${n:.5f}".rstrip("0").rstrip(".")
    if abs(n) < 1.0:
        return f"${n:.4f}".rstrip("0").rstrip(".")
    if abs(n) < 10.0:
        return f"${n:.3f}".rstrip("0").rstrip(".")
    return f"${n:.2f}"


def fmt_duration(seconds: Number) -> str:
    """Human-readable duration: 134.7 → '2m 14s', 3600 → '1h 0m'."""
    s = float(seconds)
    if s < 0.001:
        return "0s"
    if s < 1.0:
        return f"{s * 1000:.0f}ms"
    if s < 60.0:
        return f"{s:.1f}s"
    if s < 3600.0:
        m = int(s // 60)
        sec = s % 60
        if sec < 0.5:
            return f"{m}m"
        return f"{m}m {int(sec)}s"
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


def fmt_bytes(n: Number) -> str:
    """Human-readable bytes: 1_500_000 → '1.4 MB'."""
    n = float(n)
    if n < 1024:
        return f"{int(n)} B"
    for unit in ("KB", "MB", "GB", "TB", "PB"):
        n /= 1024.0
        if n < 1024.0:
            if n < 10.0:
                return f"{n:.1f} {unit}"
            return f"{int(n)} {unit}"
    return f"{n:.1f} PB"


def fmt_percent(fraction: Number) -> str:
    """Fraction to percentage: 0.85612 → '85.6%', 0.023 → '2.3%'."""
    p = float(fraction) * 100.0
    if p >= 99.95:
        return "100%"
    if p <= 0.049:
        return "<0.1%"
    if p < 1.0:
        return f"{p:.2f}%"
    if p < 10.0:
        return f"{p:.1f}%"
    return f"{p:.0f}%"


def fmt_tokens(n: Number) -> str:
    """Token count: 12345 → '12.3K tok'."""
    return f"{fmt_count(n)} tok"


def fmt_latency(ms: Number) -> str:
    """Latency: 234.5 → '234ms', 45 → '45ms', 1200 → '1.2s'."""
    ms = float(ms)
    if ms <= 0:
        return "---"
    if ms < 1000.0:
        return f"{ms:.0f}ms"
    return f"{ms / 1000:.1f}s"


def fmt_rate(per_second: Number) -> str:
    """Rate: 45.3 → '45.3/s', 0.5 → '0.5/s'."""
    r = float(per_second)
    if r >= 1000:
        return f"{r/1000:.1f}K/s"
    if r >= 1.0:
        return f"{r:.1f}/s"
    return f"{r:.2f}/s"


def fmt_estimate(seconds: Number) -> str:
    """Fuzzy estimate: 15 → '~15s', 90 → '~1.5m', 3600 → '~1h'."""
    s = float(seconds)
    if s < 5.0:
        return "<5s"
    if s < 60.0:
        return f"~{int(s)}s"
    if s < 3600.0:
        m = s / 60.0
        if m < 2.0:
            return f"~{int(m)}m"
        return f"~{m:.1f}m"
    h = s / 3600.0
    if h < 2.0:
        return f"~{int(h)}h"
    return f"~{h:.1f}h"


class ElapsedTimer:
    """Track elapsed time with formatted output."""

    def __init__(self) -> None:
        self._start = time.monotonic()

    def reset(self) -> None:
        self._start = time.monotonic()

    def elapsed(self) -> float:
        return time.monotonic() - self._start

    def elapsed_fmt(self) -> str:
        return fmt_duration(self.elapsed())

    def rate(self, count: int) -> str:
        """Rate."""
        e = self.elapsed()
        if e < 0.001:
            return "---/s"
        return fmt_rate(count / e)
