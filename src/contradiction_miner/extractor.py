"""Extract scientific claims from text"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Claim:
    """Claim."""
    id: str
    text: str
    subject: str
    predicate: str
    polarity: str  # positive, negative, neutral
    confidence: float
    source: str = ""
    section: str = ""

@dataclass
class ExtractionResult:
    """ExtractionResult."""
    claims: list[Claim]
    total_sentences: int
    claims_per_sentence: float

class ClaimExtractor:
    """Extract claims using pattern matching"""

    PATTERNS = [
        r"(\w+(?:\s\w+){0,5})\s+(is|are|was|were|has|have|can|could|may|might|must|should|will|would)\s+(.+)",
        r"(.+)\s+(causes?|leads? to|results? in|produces?|generates?|triggers?)\s+(.+)",
        r"(.+)\s+(increases?|decreases?|reduces?|improves?|worsens?)\s+(.+)",
        r"it\s+is\s+(\w+)\s+that\s+(.+)",
        r"evidence\s+suggests\s+(that\s+)?(.+)",
    ]

    NEGATION_WORDS = {
        "not", "no", "never", "neither", "nor",
        "nothing", "nowhere", "hardly", "barely", "scarcely",
    }

    def extract(self, text: str) -> ExtractionResult:
        """Extract."""
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        claims: list[Claim] = []

        for i, sent in enumerate(sentences):
            matched = False
            for pat in self.PATTERNS:
                m = re.search(pat, sent, re.IGNORECASE)
                if m:
                    groups = m.groups()
                    if len(groups) >= 2:
                        subject = (groups[0] or "").strip()
                        predicate = groups[1].strip() if groups[1] else "exists"
                        polarity = self._classify_polarity(sent)
                        claim = Claim(
                            id=f"C{i}_{len(claims)}",
                            text=sent,
                            subject=subject,
                            predicate=predicate,
                            polarity=polarity,
                            confidence=0.7,
                        )
                        claims.append(claim)
                        matched = True
                        break
            if not matched:
                if len(sent.split()) > 3:
                    polarity = self._classify_polarity(sent)
                    claims.append(
                        Claim(
                            id=f"C{i}_w",
                            text=sent,
                            subject=sent[:50],
                            predicate="exists",
                            polarity=polarity,
                            confidence=0.3,
                        )
                    )

        return ExtractionResult(
            claims=claims,
            total_sentences=len(sentences),
            claims_per_sentence=len(claims) / max(len(sentences), 1),
        )

    def _classify_polarity(self, text: str) -> str:
        words = set(text.lower().split())
        if words & self.NEGATION_WORDS:
            return "negative"
        return "positive"

def extract_claims(text: str) -> ExtractionResult:
    return ClaimExtractor().extract(text)
