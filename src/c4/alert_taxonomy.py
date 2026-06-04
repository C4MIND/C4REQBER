# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class C4Alert:
    """C4Alert."""
    severity: str  # "C1:INFO" | "C2:PROGRESS" | "C3:CRITICAL"
    layer: int  # 1-3
    title: str
    message: str
    source: str  # "pipeline" | "mcp" | "verification"
    timestamp: float = field(default_factory=time.time)

    @property
    def color(self) -> str:
        return {"C1:INFO": "dim cyan", "C2:PROGRESS": "yellow", "C3:CRITICAL": "bold red"}.get(self.severity, "white")

    @property
    def ttl(self) -> float:
        return {"C1:INFO": 10.0, "C2:PROGRESS": 30.0, "C3:CRITICAL": float("inf")}.get(self.severity, 10.0)


class AlertClassifier:
    """AlertClassifier."""
    PATTERNS: ClassVar[dict[str, list[str]]] = {
        "C3:CRITICAL": [
            "contradiction found", "verification failed", "counterexample",
            "proof error", "falsification", "pipeline crash", "novelty gate failed",
            "already shifted", "dead end",
        ],
        "C2:PROGRESS": [
            "hypothesis confirmed", "stage complete", "verification passed",
            "discovery found", "paradigm shift", "novelty confirmed",
            "dissertation generated", "quality gate passed",
        ],
        "C1:INFO": [
            "step started", "searching", "loading", "cache hit",
            "model selected", "plugin loaded", "pipeline started",
        ],
    }

    @classmethod
    def classify(cls, message: str, source: str = "pipeline") -> C4Alert:
        """Classify."""
        lower = message.lower()
        for sev, patterns in cls.PATTERNS.items():
            for pat in patterns:
                if pat in lower:
                    layer = int(sev[1])
                    return C4Alert(severity=sev, layer=layer, title=pat.replace("_", " ").title(), message=message, source=source)
        return C4Alert(severity="C1:INFO", layer=1, title="Status", message=message, source=source)
