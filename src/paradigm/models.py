"""Data models for paradigm shift detection"""
from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class Anomaly:
    """An anomaly in scientific consensus"""

    id: str
    field: str
    description: str
    severity: float  # 0.0 to 1.0
    first_detected: str
    citations_affected: int = 0

@dataclasses.dataclass
class ParadigmShiftSignal:
    """A signal indicating potential paradigm shift"""

    id: str
    field: str
    anomalies: list[Anomaly]
    confidence: float
    estimated_impact: str
    alternative_paradigms: list[str]
    evidence: list[str]
    warning_level: str = "info"  # info, warning, alert, critical

@dataclasses.dataclass
class DetectRequest:
    """Request for paradigm shift detection"""

    field: str
    time_window_days: int = 365
    min_anomalies: int = 3
    include_details: bool = True

@dataclasses.dataclass
class DetectResult:
    """Result of paradigm shift detection"""

    request_id: str
    field: str
    signals: list[ParadigmShiftSignal]
    anomalies_detected: int
    summary: str
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict[str, Any])
