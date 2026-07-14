"""Detect contradictions between claims"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .extractor import Claim


@dataclass
class Contradiction:
    """Contradiction."""
    claim_a: str
    claim_b: str
    type: str  # direct, polarity, implicit
    confidence: float
    evidence: str = ""

@dataclass
class ContradictionResult:
    """ContradictionResult."""
    contradictions: list[Contradiction]
    total_pairs_checked: int
    contradiction_rate: float

class ContradictionDetector:
    """ContradictionDetector."""
    NEGATION_WORDS = {
        "not", "no", "never", "neither", "nor",
        "nothing", "nowhere", "hardly", "barely", "scarcely",
    }

    OPPOSITE_PAIRS = {
        ("increase", "decrease"),
        ("high", "low"),
        ("positive", "negative"),
        ("strong", "weak"),
        ("fast", "slow"),
        ("large", "small"),
        ("cause", "prevent"),
        ("improve", "worsen"),
        ("reduce", "enhance"),
    }

    def detect(self, claims: list[Any]) -> ContradictionResult:
        """Detect."""
        contradictions: list[Contradiction] = []
        n = len(claims)
        pairs = n * (n - 1) // 2

        for i in range(n):
            for j in range(i + 1, n):
                c1, c2 = claims[i], claims[j]

                if self._detect_direct_negation(c1, c2, contradictions):
                    continue

                if self._detect_opposite_pair(c1, c2, contradictions):
                    continue

                self._detect_polarity_mismatch(c1, c2, contradictions)

        return ContradictionResult(
            contradictions=contradictions,
            total_pairs_checked=pairs,
            contradiction_rate=len(contradictions) / max(pairs, 1),
        )

    def _detect_direct_negation(
        self, c1: Claim, c2: Claim, contradictions: list[Contradiction],
    ) -> bool:
        neg1 = self._has_negation(c1.predicate)
        neg2 = self._has_negation(c2.predicate)
        if neg1 == neg2:
            return False

        t1 = c1.predicate.replace("not ", "").strip()
        t2 = c2.predicate.replace("not ", "").strip()
        if t1.lower() == t2.lower() and c1.subject.lower() == c2.subject.lower():
            contradictions.append(
                Contradiction(
                    claim_a=c1.id,
                    claim_b=c2.id,
                    type="direct",
                    confidence=0.9,
                )
            )
            return True
        return False

    def _detect_opposite_pair(
        self, c1: Claim, c2: Claim, contradictions: list[Contradiction],
    ) -> bool:
        for w1, w2 in self.OPPOSITE_PAIRS:
            if w1 in c1.predicate.lower() and w2 in c2.predicate.lower():
                if c1.subject.lower() == c2.subject.lower():
                    contradictions.append(
                        Contradiction(
                            claim_a=c1.id,
                            claim_b=c2.id,
                            type="polarity",
                            confidence=0.7,
                            evidence=f"{w1} vs {w2}",
                        )
                    )
                    return True
            if w2 in c1.predicate.lower() and w1 in c2.predicate.lower():
                if c1.subject.lower() == c2.subject.lower():
                    contradictions.append(
                        Contradiction(
                            claim_a=c1.id,
                            claim_b=c2.id,
                            type="polarity",
                            confidence=0.7,
                            evidence=f"{w2} vs {w1}",
                        )
                    )
                    return True
        return False

    def _detect_polarity_mismatch(
        self, c1: Claim, c2: Claim, contradictions: list[Contradiction],
    ) -> None:
        if c1.polarity != c2.polarity and c1.subject.lower() == c2.subject.lower():
            if c1.polarity in ("positive", "negative") and c2.polarity in (
                "positive",
                "negative",
            ):
                contradictions.append(
                    Contradiction(
                        claim_a=c1.id,
                        claim_b=c2.id,
                        type="polarity",
                        confidence=0.5,
                    )
                )

    def _has_negation(self, text: str) -> bool:
        words = set(text.lower().split())
        return bool(words & self.NEGATION_WORDS)

def detect_contradictions(claims: list[Any]) -> ContradictionResult:
    return ContradictionDetector().detect(claims)
