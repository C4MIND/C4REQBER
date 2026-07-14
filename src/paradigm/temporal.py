"""Temporal knowledge graph analysis for paradigm shifts"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.paradigm.models import Anomaly


class TemporalAnalyzer:
    """Analyzes temporal patterns in anomaly data to detect paradigm shifts"""

    def analyze_trend(self, anomalies: list[Anomaly]) -> dict[str, Any]:
        """Analyze trend."""
        if not anomalies:
            return {"trend": "stable", "acceleration": 0.0, "direction": "flat"}

        severities = sorted(
            [(a.first_detected, a.severity) for a in anomalies],
            key=lambda x: x[0],
        )

        if len(severities) < 2:
            return {
                "trend": "stable",
                "acceleration": 0.0,
                "direction": "flat",
                "first_date": severities[0][0],
                "last_date": severities[0][0],
                "data_points": len(severities),
                "avg_severity": severities[0][1],
            }

        first_sev = severities[0][1]
        last_sev = severities[-1][1]
        direction = "increasing" if last_sev > first_sev else "decreasing" if last_sev < first_sev else "flat"

        severity_values = [s[1] for s in severities]

        acceleration = 0.0
        if len(severity_values) >= 3:
            first_half_avg = sum(severity_values[:len(severity_values)//2]) / (len(severity_values)//2)
            second_half_avg = sum(severity_values[len(severity_values)//2:]) / (len(severity_values) - len(severity_values)//2)
            acceleration = second_half_avg - first_half_avg

        avg_severity = sum(severity_values) / len(severity_values)

        trend = "escalating" if avg_severity > 0.7 else "moderate" if avg_severity > 0.4 else "stable"

        return {
            "trend": trend,
            "acceleration": round(acceleration, 4),
            "direction": direction,
            "avg_severity": round(avg_severity, 4),
            "first_date": severities[0][0],
            "last_date": severities[-1][0],
            "data_points": len(severities),
        }

    def compute_momentum(self, anomalies: list[Anomaly]) -> float:
        """Compute momentum."""
        if not anomalies:
            return 0.0

        severities = [a.severity for a in anomalies]
        citations = [a.citations_affected for a in anomalies]
        max_citations = max(citations) if citations else 1

        weighted_severity = sum(s * (c / max_citations) for s, c in zip(severities, citations, strict=False))
        return weighted_severity / len(anomalies) if anomalies else 0.0

    def predict_next_anomaly_window(self, anomalies: list[Anomaly]) -> str | None:
        """Predict next anomaly window."""
        if len(anomalies) < 2:
            return None

        dates = sorted([datetime.strptime(a.first_detected, "%Y-%m-%d") for a in anomalies])
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

        if not intervals:
            return None

        avg_interval = sum(intervals) / len(intervals)
        next_date = dates[-1] + timedelta(days=int(avg_interval))
        return next_date.strftime("%Y-%m-%d")

    def detect_severity_clusters(self, anomalies: list[Anomaly]) -> list[dict[str, Any]]:
        """Detect severity clusters."""
        if not anomalies:
            return []

        sorted_anomalies = sorted(anomalies, key=lambda a: a.severity, reverse=True)
        clusters = []
        current_cluster = [sorted_anomalies[0]]
        threshold = 0.1

        for i in range(1, len(sorted_anomalies)):
            if abs(sorted_anomalies[i].severity - sorted_anomalies[i-1].severity) <= threshold:
                current_cluster.append(sorted_anomalies[i])
            else:
                clusters.append({
                    "severity_range": (
                        min(a.severity for a in current_cluster),
                        max(a.severity for a in current_cluster),
                    ),
                    "count": len(current_cluster),
                    "descriptions": [a.description for a in current_cluster],
                })
                current_cluster = [sorted_anomalies[i]]

        if current_cluster:
            clusters.append({
                "severity_range": (
                    min(a.severity for a in current_cluster),
                    max(a.severity for a in current_cluster),
                ),
                "count": len(current_cluster),
                "descriptions": [a.description for a in current_cluster],
            })

        return clusters

    def time_window_filter(self, anomalies: list[Anomaly], days: int) -> list[Anomaly]:
        """Time window filter."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            a for a in anomalies
            if datetime.strptime(a.first_detected, "%Y-%m-%d") >= cutoff
        ]
