# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class ParadigmShiftAssessment:
    """Complete paradigm shift evaluation using Kuhn's criteria."""

    # 4-stage model
    stage: str  # "normal_science" | "anomaly_accumulation" | "crisis" | "revolution" | "new_paradigm"
    stage_confidence: float  # 0.0-1.0

    # Kuhn's 5 shared values (each 0.0-1.0)
    accuracy: float  # Does the work explain known phenomena better?
    consistency: float  # Internal + external (with other theories)
    scope: float  # Consequences beyond original data
    simplicity: float  # Unifies otherwise disparate phenomena
    fruitfulness: float  # Opens new research directions

    # Anomaly metrics
    anomaly_count: int
    anomaly_severity: float  # 0.0-1.0, how "troublesome" are the anomalies
    anomalies_explained_away: int  # Count of anomalies the existing paradigm dismisses

    # Novelty & Generational
    gestalt_switch_potential: float  # 0.0-1.0 — does it reframe seeing the same data?
    generational_readiness: float  # 0.0-1.0 — Planck's principle: new generation ready?
    incommensurability_index: float  # 0.0-1.0 — how much does language/meaning shift?

    # Overall
    paradigm_shift_score: float  # 0.0-1.0 composite
    is_paradigm_shift: bool  # Final verdict

    # Crisis indicators (Kuhn, ch.7) — default field must come after all required fields
    crisis_indicators: list[str] = field(default_factory=list)
    # e.g. "proliferation of competing articulations", "recourse to philosophy",
    # "debate over fundamentals", "explicit expression of discontent"

    def summary(self) -> str:
        return (
            f"Paradigm Shift Score: {self.paradigm_shift_score:.2f} | {self.stage.upper()} | "
            f"Accuracy={self.accuracy:.2f} Consistency={self.consistency:.2f} "
            f"Scope={self.scope:.2f} Simplicity={self.simplicity:.2f} Fruitfulness={self.fruitfulness:.2f} | "
            f"Anomalies: {self.anomaly_count} (severity {self.anomaly_severity:.2f}) | "
            f"Gestalt: {self.gestalt_switch_potential:.2f}"
        )


class KuhnCriteria:
    """Apply Kuhn's paradigm shift criteria to research discoveries."""

    # Crisis indicators from Kuhn (1962, ch.7-8)
    CRISIS_PATTERNS: ClassVar[list[str]] = [
        "proliferation of competing",
        "willingness to try anything",
        "explicit discontent",
        "recourse to philosophy",
        "debate over fundamentals",
        "questioning the paradigm",
        "loss of confidence",
        "extraordinary research",
        "pushing boundaries",
    ]

    # Anomaly severity keywords (troublesome anomalies, Kuhn ch.6)
    ANOMALY_SEVERITY_KEYWORDS: ClassVar[dict[str, float]] = {
        "contradiction": 0.9,
        "falsifies": 1.0,
        "inconsistent": 0.8,
        "paradox": 0.85,
        "cannot explain": 0.9,
        "unexplained": 0.7,
        "violates": 0.95,
        "breaks": 0.8,
        "challenges": 0.6,
        "requires revision": 0.7,
        "fundamentally incompatible": 0.95,
    }

    @classmethod
    def assess(cls, discovery: dict, gaps: list[dict], hypotheses: list[dict], verification: dict, novelty: dict) -> ParadigmShiftAssessment:
        """Assess a research discovery using Kuhn's criteria."""

        # 1. Five values
        accuracy = cls._score_accuracy(hypotheses, verification)
        consistency = cls._score_consistency(gaps, hypotheses)
        scope = cls._score_scope(gaps, discovery)
        simplicity = cls._score_simplicity(hypotheses, gaps)
        fruitfulness = cls._score_fruitfulness(gaps, hypotheses)

        # 2. Anomaly analysis
        anomaly_count, anomaly_severity, explained_away = cls._count_anomalies(gaps)

        # 3. Crisis detection
        crisis_indicators = cls._detect_crisis(gaps, hypotheses, discovery)

        # 4. Stage determination (4-stage model)
        if len(crisis_indicators) >= 3 and anomaly_severity > 0.7:
            stage = "crisis"
            stage_confidence = min(1.0, len(crisis_indicators) / 5)
        elif anomaly_count >= 3 and anomaly_severity > 0.5:
            stage = "anomaly_accumulation"
            stage_confidence = anomaly_severity
        elif novelty.get("shift_detected", False):
            stage = "revolution"
            stage_confidence = novelty.get("confidence", 0.5)
        elif anomaly_count == 0:
            stage = "normal_science"
            stage_confidence = 0.9
        else:
            stage = "anomaly_accumulation"
            stage_confidence = 0.5

        # 5. Gestalt switch potential
        gestalt = cls._gestalt_switch_potential(gaps, hypotheses)

        # 6. Generational readiness (proxy: novelty score × anomaly severity)
        generational = novelty.get("score", 0.5) * anomaly_severity

        # 7. Incommensurability index
        incomm = cls._incommensurability_index(gaps, hypotheses, discovery)

        # 8. Composite score
        composite = (
            0.25 * accuracy
            + 0.20 * consistency
            + 0.15 * scope
            + 0.10 * simplicity
            + 0.10 * fruitfulness
            + 0.10 * anomaly_severity
            + 0.05 * gestalt
            + 0.05 * generational
        )

        return ParadigmShiftAssessment(
            stage=stage,
            stage_confidence=stage_confidence,
            accuracy=accuracy,
            consistency=consistency,
            scope=scope,
            simplicity=simplicity,
            fruitfulness=fruitfulness,
            anomaly_count=anomaly_count,
            anomaly_severity=anomaly_severity,
            anomalies_explained_away=explained_away,
            crisis_indicators=crisis_indicators,
            gestalt_switch_potential=gestalt,
            generational_readiness=generational,
            incommensurability_index=incomm,
            paradigm_shift_score=composite,
            is_paradigm_shift=composite > 0.6,
        )

    @classmethod
    def _score_accuracy(cls, hypotheses: list[dict], verification: dict) -> float:
        if not hypotheses:
            return 0.4
        verif = verification.get("passed", verification.get("status") == "verified")
        matched = sum(1 for h in hypotheses if h.get("confidence", 0) > 0.5)
        base = matched / max(len(hypotheses), 1)
        return min(1.0, base + (0.3 if verif else 0.0))

    @classmethod
    def _score_consistency(cls, gaps: list[dict], hypotheses: list[dict]) -> float:
        if not gaps or not hypotheses:
            return 0.5
        gap_areas = {g.get("area", "") for g in gaps}
        hyp_titles = {h.get("title", "") for h in hypotheses}
        return 0.7 if len(gap_areas) <= len(hyp_titles) else 0.4

    @classmethod
    def _score_scope(cls, gaps: list[dict], discovery: dict) -> float:
        domain_count = len({g.get("area", "")[:30] for g in gaps})
        return min(1.0, 0.3 + 0.1 * domain_count)

    @classmethod
    def _score_simplicity(cls, hypotheses: list[dict], gaps: list[dict]) -> float:
        if not hypotheses:
            return 0.3
        avg_words = sum(len(h.get("title", "").split()) for h in hypotheses) / len(hypotheses)
        return 1.0 if avg_words < 12 else 0.7 if avg_words < 20 else 0.4

    @classmethod
    def _score_fruitfulness(cls, gaps: list[dict], hypotheses: list[dict]) -> float:
        gap_count = len(gaps)
        hyp_count = len(hypotheses)
        if gap_count == 0:
            return 0.2
        return min(1.0, 0.3 + 0.15 * hyp_count + 0.05 * gap_count)

    @classmethod
    def _count_anomalies(cls, gaps: list[dict]) -> tuple[int, float, int]:
        count = 0
        total_severity = 0.0
        explained = 0
        for g in gaps:
            evidence = g.get("evidence", "").lower()
            area = g.get("area", "").lower()
            combined = evidence + " " + area
            for kw, sev in cls.ANOMALY_SEVERITY_KEYWORDS.items():
                if kw in combined:
                    count += 1
                    total_severity += sev
                    if "explained" in combined or "dismissed" in combined:
                        explained += 1
                    break
        avg_sev = total_severity / max(count, 1)
        return count, avg_sev, explained

    @classmethod
    def _detect_crisis(cls, gaps: list[dict], hypotheses: list[dict], discovery: dict) -> list[str]:
        indicators = []
        all_text = " ".join(
            g.get("evidence", "") + g.get("area", "") for g in gaps
        ) + " ".join(h.get("title", "") for h in hypotheses)
        all_lower = all_text.lower()
        for pat in cls.CRISIS_PATTERNS:
            if pat in all_lower:
                indicators.append(pat)
        return indicators

    @classmethod
    def _gestalt_switch_potential(cls, gaps: list[dict], hypotheses: list[dict]) -> float:
        if not gaps:
            return 0.3
        reframe_keywords = ["reframe", "reinterpret", "new perspective", "gestalt", "see differently", "paradigm"]
        all_text = " ".join(g.get("area", "") for g in gaps) + " ".join(h.get("title", "") for h in hypotheses)
        all_lower = all_text.lower()
        hits = sum(1 for kw in reframe_keywords if kw in all_lower)
        return min(1.0, 0.3 + 0.15 * hits)

    @classmethod
    def _incommensurability_index(cls, gaps: list[dict], hypotheses: list[dict], discovery: dict) -> float:
        new_terms = set()
        for h in hypotheses:
            for word in h.get("title", "").lower().split():
                if len(word) > 8 and word not in NEWTONIAN_WORDS:
                    new_terms.add(word)
        return min(1.0, len(new_terms) * 0.1)


# Common scientific vocabulary — terms that DON'T signal incommensurability
NEWTONIAN_WORDS: set[str] = {
    "hypothesis", "analysis", "research", "scientific", "theoretical", "experimental",
    "framework", "mechanism", "structure", "function", "system", "model", "approach",
    "evidence", "correlation", "causation", "prediction", "observation", "measurement",
}
