"""Kuhnian paradigm shift detection for scientific literature."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np


try:
    from sklearn.ensemble import IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


@dataclass
class ScientificClaim:
    """A single scientific claim with metadata."""

    text: str
    timestamp: datetime
    source: str
    citations: int = 0
    domain: str = ""
    confidence: float = 1.0


@dataclass
class AnomalyResult:
    """Result of anomaly detection in consensus."""

    claim: ScientificClaim
    anomaly_score: float
    is_anomaly: bool
    deviation_from_consensus: float


@dataclass
class CrisisSignal:
    """Crisis indicator in a scientific domain."""

    domain: str
    severity: float  # 0.0 - 1.0
    indicators: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ParadigmShiftWarning:
    """Early warning of a potential paradigm shift."""

    domain: str
    probability: float  # 0.0 - 1.0
    contributing_factors: list[str] = field(default_factory=list)
    estimated_timeframe: str = ""
    confidence: float = 0.0


class AnomalyDetector:
    """Detect anomalies in scientific consensus using NLP + statistical methods."""

    def __init__(self, contamination: float = 0.1, ngram_range: tuple[int, int] = (1, 2)) -> None:
        self.contamination = contamination
        self.vectorizer = TfidfVectorizer(ngram_range=ngram_range, stop_words="english")
        self.model: IsolationForest | None = None
        self._claim_texts: list[str] = []
        self._claims: list[ScientificClaim] = []

    def fit(self, claims: list[ScientificClaim]) -> AnomalyDetector:
        """Fit the anomaly detector on a corpus of claims."""
        if not claims:
            return self
        self._claims = claims
        self._claim_texts = [c.text for c in claims]
        X = self.vectorizer.fit_transform(self._claim_texts)
        self.model = IsolationForest(contamination=self.contamination, random_state=42)
        self.model.fit(X.toarray())
        return self

    def detect(self, claim: ScientificClaim) -> AnomalyResult:
        """Detect if a claim is anomalous relative to the fitted consensus."""
        if self.model is None or not self._claim_texts:
            return AnomalyResult(
                claim=claim, anomaly_score=0.0, is_anomaly=False, deviation_from_consensus=0.0
            )
        X = self.vectorizer.transform([claim.text])
        score = float(self.model.decision_function(X.toarray())[0])
        pred = int(self.model.predict(X.toarray())[0])

        # Deviation from consensus = 1 - max cosine similarity to existing claims
        if len(self._claim_texts) > 0:
            all_X = self.vectorizer.transform(self._claim_texts)
            sims = cosine_similarity(X, all_X)[0]
            deviation = 1.0 - float(np.max(sims)) if len(sims) > 0 else 1.0
        else:
            deviation = 1.0

        return AnomalyResult(
            claim=claim,
            anomaly_score=-score,  # higher = more anomalous
            is_anomaly=pred == -1,
            deviation_from_consensus=deviation,
        )

    def batch_detect(self, claims: list[ScientificClaim]) -> list[AnomalyResult]:
        """Detect anomalies for a batch of claims."""
        return [self.detect(c) for c in claims]


class CrisisIndicator:
    """Identify crisis indicators in a scientific domain."""

    CRISIS_KEYWORDS: list[str] = [
        "contradict",
        "inconsistent",
        "anomaly",
        "unexpected",
        "failed to replicate",
        "discrepancy",
        "paradox",
        "challenge",
        "refute",
        "question",
        "revised",
        "overturn",
    ]

    def __init__(self, keyword_weight: float = 0.3, citation_drop_threshold: float = 0.5) -> None:
        self.keyword_weight = keyword_weight
        self.citation_drop_threshold = citation_drop_threshold

    def analyze(self, claims: list[ScientificClaim], domain: str = "") -> CrisisSignal:
        """Analyze a set of claims for crisis indicators."""
        if not claims:
            return CrisisSignal(domain=domain, severity=0.0)

        indicators: list[str] = []
        keyword_hits = 0
        total_words = 0
        citation_trend: list[float] = []

        sorted_claims = sorted(claims, key=lambda c: c.timestamp)
        for claim in sorted_claims:
            words = claim.text.lower().split()
            total_words += len(words)
            for kw in self.CRISIS_KEYWORDS:
                if kw in claim.text.lower():
                    keyword_hits += 1
            citation_trend.append(float(claim.citations))

        severity = 0.0
        if total_words > 0:
            kw_ratio = keyword_hits / total_words
            severity += min(kw_ratio * 10, 1.0) * self.keyword_weight
            if kw_ratio > 0.01:
                indicators.append(f"Elevated crisis keywords: {keyword_hits} hits")

        # Citation drop detection
        if len(citation_trend) >= 3:
            recent_avg = float(np.mean(citation_trend[-1:]))  # Most recent data point
            older_part = citation_trend[:-1]  # All older data points
            older_avg = float(np.mean(older_part)) if older_part else recent_avg
            if older_avg > 0 and (older_avg - recent_avg) / older_avg > self.citation_drop_threshold:
                severity += 0.4
                indicators.append("Significant citation drop detected")

        # Anomaly density
        ad = AnomalyDetector()
        ad.fit(sorted_claims)
        anomalies = ad.batch_detect(sorted_claims)
        anomaly_rate = sum(1 for a in anomalies if a.is_anomaly) / len(anomalies) if anomalies else 0.0
        if anomaly_rate > 0.2:
            severity += 0.3
            indicators.append(f"High anomaly rate: {anomaly_rate:.2%}")

        severity = min(severity, 1.0)
        return CrisisSignal(domain=domain, severity=severity, indicators=indicators)


class TemporalClaimAnalyzer:
    """Analyze how scientific claims evolve over time."""

    def __init__(self, window_days: int = 365) -> None:
        self.window_days = window_days

    def temporal_variance(self, claims: list[ScientificClaim]) -> dict[str, Any]:
        """Measure variance in claim semantics over time windows."""
        if not claims:
            return {"variance": 0.0, "trend": "stable", "windows": []}

        sorted_claims = sorted(claims, key=lambda c: c.timestamp)
        vectorizer = TfidfVectorizer(stop_words="english")
        texts = [c.text for c in sorted_claims]
        X = vectorizer.fit_transform(texts)

        # Sliding window similarity
        window_size = max(2, len(sorted_claims) // 4)
        similarities: list[float] = []
        windows: list[dict[str, Any]] = []

        for i in range(0, len(sorted_claims) - window_size + 1, max(1, window_size // 2)):
            window_claims = sorted_claims[i : i + window_size]
            window_texts = [c.text for c in window_claims]
            if len(window_texts) < 2:
                continue
            Wx = vectorizer.transform(window_texts)
            sim_matrix = cosine_similarity(Wx)
            # Mean pairwise similarity (excluding diagonal)
            mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
            mean_sim = float(sim_matrix[mask].mean()) if mask.any() else 1.0
            similarities.append(mean_sim)
            windows.append({
                "start": window_claims[0].timestamp.isoformat(),
                "end": window_claims[-1].timestamp.isoformat(),
                "mean_similarity": mean_sim,
                "claim_count": len(window_claims),
            })

        variance = float(np.var(similarities)) if similarities else 0.0
        if len(similarities) >= 2:
            trend = "diverging" if similarities[-1] < similarities[0] else "converging"
        else:
            trend = "stable"

        return {"variance": variance, "trend": trend, "windows": windows}

    def consensus_drift(self, claims: list[ScientificClaim]) -> dict[str, Any]:
        """Measure drift in consensus over time using centroid distance."""
        if len(claims) < 4:
            return {"drift": 0.0, "early_centroid": None, "late_centroid": None}

        sorted_claims = sorted(claims, key=lambda c: c.timestamp)
        mid = len(sorted_claims) // 2
        early = sorted_claims[:mid]
        late = sorted_claims[mid:]

        # Ensure both halves have at least 2 claims for meaningful comparison
        if len(early) < 2 or len(late) < 2:
            return {"drift": 0.0, "early_centroid": None, "late_centroid": None}

        vectorizer = TfidfVectorizer(stop_words="english")
        all_texts = [c.text for c in sorted_claims]
        vectorizer.fit(all_texts)

        early_X = vectorizer.transform([c.text for c in early]).toarray()
        late_X = vectorizer.transform([c.text for c in late]).toarray()

        early_centroid = np.mean(early_X, axis=0)
        late_centroid = np.mean(late_X, axis=0)

        drift = float(np.linalg.norm(early_centroid - late_centroid))
        return {
            "drift": drift,
            "early_centroid": early_centroid.tolist(),
            "late_centroid": late_centroid.tolist(),
        }


class ParadigmShiftDetector:
    """Kuhnian paradigm shift detection combining anomaly, crisis, and temporal analysis."""

    def __init__(
        self,
        anomaly_threshold: float = 0.6,
        crisis_threshold: float = 0.5,
        drift_threshold: float = 0.3,
    ) -> None:
        self.anomaly_threshold = anomaly_threshold
        self.crisis_threshold = crisis_threshold
        self.drift_threshold = drift_threshold
        self.anomaly_detector = AnomalyDetector()
        self.crisis_indicator = CrisisIndicator()
        self.temporal_analyzer = TemporalClaimAnalyzer()

    def analyze(self, claims: list[ScientificClaim], domain: str = "") -> ParadigmShiftWarning:
        """Analyze claims for paradigm shift signals."""
        if not claims:
            return ParadigmShiftWarning(domain=domain, probability=0.0, confidence=1.0)

        factors: list[str] = []

        # 1. Anomaly analysis
        self.anomaly_detector.fit(claims)
        anomalies = self.anomaly_detector.batch_detect(claims)
        anomaly_rate = sum(1 for a in anomalies if a.is_anomaly) / len(anomalies) if anomalies else 0.0
        max_score = max((a.anomaly_score for a in anomalies), default=0.0)
        if anomaly_rate > 0.15 or max_score > self.anomaly_threshold:
            factors.append(f"Anomaly rate: {anomaly_rate:.2%}, max score: {max_score:.3f}")

        # 2. Crisis analysis
        crisis = self.crisis_indicator.analyze(claims, domain)
        if crisis.severity > self.crisis_threshold:
            factors.extend(crisis.indicators)
            factors.append(f"Crisis severity: {crisis.severity:.3f}")

        # 3. Temporal drift
        drift_result = self.temporal_analyzer.consensus_drift(claims)
        drift = drift_result["drift"]
        if drift > self.drift_threshold:
            factors.append(f"Consensus drift: {drift:.3f}")

        variance_result = self.temporal_analyzer.temporal_variance(claims)
        if variance_result["trend"] == "diverging":
            factors.append("Claims diverging over time")

        # Compute probability
        prob = 0.0
        prob += min(anomaly_rate * 2, 0.3)
        prob += crisis.severity * 0.3
        prob += min(drift * 0.5, 0.25)
        if variance_result["trend"] == "diverging":
            prob += 0.15
        prob = min(prob, 1.0)

        # Confidence based on data volume
        confidence = min(len(claims) / 20, 1.0)

        # Timeframe estimate
        if prob > 0.7:
            timeframe = "Imminent (0-2 years)"
        elif prob > 0.4:
            timeframe = "Near-term (2-5 years)"
        elif prob > 0.2:
            timeframe = "Medium-term (5-10 years)"
        else:
            timeframe = "Stable"

        return ParadigmShiftWarning(
            domain=domain,
            probability=prob,
            contributing_factors=factors,
            estimated_timeframe=timeframe,
            confidence=confidence,
        )

    def detect_breakthrough_claims(self, claims: list[ScientificClaim]) -> list[ScientificClaim]:
        """Identify claims that may represent breakthrough ideas."""
        if not claims:
            return []
        self.anomaly_detector.fit(claims)
        anomalies = self.anomaly_detector.batch_detect(claims)
        # Return anomalies with score above threshold OR top anomalies if none meet threshold
        breakthroughs = [a.claim for a in anomalies if a.is_anomaly and a.anomaly_score > self.anomaly_threshold]
        if not breakthroughs:
            # Fallback: return most anomalous claims
            sorted_anomalies = sorted([a for a in anomalies if a.is_anomaly], key=lambda x: x.anomaly_score, reverse=True)
            if sorted_anomalies:
                breakthroughs = [sorted_anomalies[0].claim]
        return breakthroughs
