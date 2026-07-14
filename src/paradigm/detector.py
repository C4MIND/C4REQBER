"""Paradigm Shift Detector - Core detection engine"""
from __future__ import annotations

import uuid
from typing import Any, cast

from src.paradigm.anomaly import AnomalyTracker
from src.paradigm.models import Anomaly, DetectRequest, DetectResult, ParadigmShiftSignal
from src.paradigm.temporal import TemporalAnalyzer


class ParadigmShiftDetector:
    """Detects signs of paradigm shifts in scientific fields"""

    def __init__(self) -> None:
        self.anomaly_tracker = AnomalyTracker()
        self.temporal_analyzer = TemporalAnalyzer()

    @property
    def anomaly_database(self) -> dict[str, list[Anomaly]]:
        return cast(dict[str, list[Anomaly]], self.anomaly_tracker.anomalies_by_field)  # type: ignore[redundant-cast]

    def detect_anomalies(self, field: str, time_window_days: int) -> list[Anomaly]:
        """Detect anomalies."""
        anomalies: list[Anomaly] = self.anomaly_tracker.get_by_field(field)
        if time_window_days > 0:
            anomalies = self.temporal_analyzer.time_window_filter(anomalies, time_window_days)
        return cast(list[Anomaly], anomalies)  # type: ignore[redundant-cast]

    def analyze_temporal_patterns(self, anomalies: list[Anomaly]) -> dict[str, Any]:
        """Analyze temporal patterns."""
        trend = self.temporal_analyzer.analyze_trend(anomalies)
        momentum = self.temporal_analyzer.compute_momentum(anomalies)
        clusters = self.temporal_analyzer.detect_severity_clusters(anomalies)
        next_window = self.temporal_analyzer.predict_next_anomaly_window(anomalies)

        return {
            "trend": trend["trend"],
            "acceleration": trend["acceleration"],
            "momentum": round(momentum, 4),
            "cumulative_citations": sum(a.citations_affected for a in anomalies),
            "clusters": clusters,
            "predicted_next_anomaly": next_window,
            "direction": trend["direction"],
        }

    def assess_paradigm_shift(self, anomalies: list[Anomaly]) -> float:
        """Assess paradigm shift."""
        if not anomalies:
            return 0.0

        severity_sum = sum(a.severity for a in anomalies)
        count_factor = min(len(anomalies) / 10.0, 1.0)
        citation_factor = min(
            sum(a.citations_affected for a in anomalies) / 20000.0, 1.0
        )

        base_score = severity_sum / max(len(anomalies), 1)
        adjusted = base_score * (0.4 + 0.3 * count_factor + 0.3 * citation_factor)
        return min(adjusted, 1.0)

    def get_alternative_paradigms(self, field: str, anomalies: list[Anomaly]) -> list[str]:
        """Get alternative paradigms."""
        alternatives = {
            "physics": [
                "Modified gravity (MOND)",
                "String theory landscape",
                "Digital physics",
                "Emergent spacetime",
                "Superfluid vacuum theory",
            ],
            "biology": [
                "Extended evolutionary synthesis",
                "Cellular cognition",
                "Morphic fields",
                "Constructal law",
            ],
            "ai": [
                "Scaling laws paradigm",
                "Neurosymbolic integration",
                "Embodied intelligence",
                "Free energy principle",
                "World models approach",
            ],
            "neuroscience": [
                "Predictive processing",
                "Integrated information theory",
                "Global workspace theory",
                "Orchestrated objective reduction",
            ],
            "climate_science": [
                "Gaia hypothesis 2.0",
                "Planetary boundaries framework",
                "Earth system resilience theory",
                "Tipping cascades model",
            ],
        }

        field_alternatives = alternatives.get(field.lower(), ["Paradigm extension", "Alternative framework"])

        # If we have high-severity anomalies, suggest more radical alternatives
        if any(a.severity > 0.85 for a in anomalies):
            radical = {
                "physics": ["Simulation hypothesis", "Consciousness-based physics"],
                "biology": ["Panpsychism in biology", "Teleological evolution"],
                "ai": ["AI consciousness thesis", "Synthetic phenomenology"],
            }
            radical_additions = radical.get(field.lower(), [])
            field_alternatives = radical_additions + field_alternatives

        return field_alternatives[:5]

    def detect(self, request: DetectRequest) -> DetectResult:
        """Detect."""
        anomalies = self.detect_anomalies(request.field, request.time_window_days)

        if len(anomalies) < request.min_anomalies:
            return DetectResult(
                request_id=str(uuid.uuid4()),
                field=request.field,
                signals=[],
                anomalies_detected=len(anomalies),
                summary=f"Insufficient anomalies detected in {request.field} to assess paradigm shift risk. Found {len(anomalies)}, need at least {request.min_anomalies}.",
                metadata={"threshold": request.min_anomalies},
            )

        temporal = self.analyze_temporal_patterns(anomalies)
        confidence = self.assess_paradigm_shift(anomalies)
        alternatives = self.get_alternative_paradigms(request.field, anomalies)

        if confidence > 0.8:
            warning_level = "critical"
        elif confidence > 0.6:
            warning_level = "alert"
        elif confidence > 0.4:
            warning_level = "warning"
        else:
            warning_level = "info"

        signal = ParadigmShiftSignal(
            id=str(uuid.uuid4()),
            field=request.field,
            anomalies=anomalies if request.include_details else [],
            confidence=round(confidence, 4),
            estimated_impact="HIGH" if confidence > 0.7 else "MEDIUM" if confidence > 0.4 else "LOW",
            alternative_paradigms=alternatives[:3],
            evidence=[a.description for a in anomalies] if request.include_details else [],
            warning_level=warning_level,
        )

        return DetectResult(
            request_id=str(uuid.uuid4()),
            field=request.field,
            signals=[signal],
            anomalies_detected=len(anomalies),
            summary=(
                f"Detected {len(anomalies)} anomalies in {request.field} with "
                f"{confidence:.0%} confidence of paradigm shift. Warning level: {warning_level}."
            ),
            metadata={"temporal_analysis": temporal} if request.include_details else {},
        )
