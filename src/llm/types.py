# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: dict[str, int]
    latency_ms: float = 0.0
    provider: str = "unknown"
    raw_response: dict | None = None  # type: ignore[type-arg]
