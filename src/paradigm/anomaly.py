"""Anomaly detection in scientific consensus"""
from __future__ import annotations

from typing import Any

from src.paradigm.models import Anomaly


class AnomalyTracker:
    """Tracks and manages scientific anomalies across fields"""

    def __init__(self) -> None:
        self.anomalies_by_field: dict[str, list[Anomaly]] = {
            "physics": [
                Anomaly("a1", "physics", "Muon g-2 anomaly", 0.85, "2021-04-07", 1200),
                Anomaly("a2", "physics", "Hubble tension", 0.90, "2019-03-15", 2500),
                Anomaly("a3", "physics", "Dark matter detection null results", 0.78, "2020-11-01", 3200),
                Anomaly("a4", "physics", "W boson mass discrepancy", 0.82, "2022-04-07", 1800),
            ],
            "biology": [
                Anomaly("a5", "biology", "Prion-like proteins in memory", 0.70, "2020-06-01", 800),
                Anomaly("a6", "biology", "Horizontal gene transfer prevalence", 0.65, "2019-09-12", 1500),
                Anomaly("a7", "biology", "Non-Mendelian inheritance patterns", 0.72, "2021-02-28", 950),
            ],
            "ai": [
                Anomaly("a8", "ai", "Emergent capabilities in LLMs", 0.75, "2022-08-15", 5000),
                Anomaly("a9", "ai", "Groking phenomenon", 0.65, "2023-01-20", 1500),
                Anomaly("a10", "ai", "Inverse scaling failures", 0.68, "2022-11-05", 2200),
                Anomaly("a11", "ai", "Unexplained in-context learning", 0.80, "2023-03-10", 3800),
            ],
            "neuroscience": [
                Anomaly("a12", "neuroscience", "Psychedelic neuroplasticity", 0.74, "2021-07-15", 1100),
                Anomaly("a13", "neuroscience", "Quantum effects in cognition", 0.62, "2022-01-08", 600),
            ],
            "climate_science": [
                Anomaly("a14", "climate_science", "Accelerating feedback loops", 0.88, "2022-06-20", 4500),
                Anomaly("a15", "climate_science", "AMOC slowdown", 0.85, "2021-12-03", 3200),
                Anomaly("a16", "climate_science", "Permafrost methane unexpected release", 0.82, "2023-02-14", 2100),
            ],
        }

    def get_by_field(self, field: str) -> list[Anomaly]:
        return self.anomalies_by_field.get(field.lower(), [])

    def get_high_severity(self, field: str, threshold: float = 0.7) -> list[Anomaly]:
        return [a for a in self.get_by_field(field) if a.severity >= threshold]

    def add_anomaly(self, anomaly: Anomaly) -> None:
        """Add anomaly."""
        field = anomaly.field.lower()
        if field not in self.anomalies_by_field:
            self.anomalies_by_field[field] = []
        self.anomalies_by_field[field].append(anomaly)

    def get_all_fields(self) -> list[str]:
        return list(self.anomalies_by_field.keys())

    def field_summary(self, field: str) -> dict[str, Any]:
        """Field summary."""
        anomalies = self.get_by_field(field)
        if not anomalies:
            return {"field": field, "anomaly_count": 0, "avg_severity": 0.0, "total_citations": 0}

        avg_sev = sum(a.severity for a in anomalies) / len(anomalies)
        total_cit = sum(a.citations_affected for a in anomalies)
        return {
            "field": field,
            "anomaly_count": len(anomalies),
            "avg_severity": round(avg_sev, 3),
            "total_citations": total_cit,
            "max_severity": max(a.severity for a in anomalies),
        }

    def search_anomalies(self, query: str) -> list[Anomaly]:
        """Search anomalies."""
        query_lower = query.lower()
        results = []
        for anomalies in self.anomalies_by_field.values():
            for a in anomalies:
                if query_lower in a.description.lower() or query_lower in a.field.lower():
                    results.append(a)
        return results
