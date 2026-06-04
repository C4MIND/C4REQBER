"""Cross-paper contradiction mining for scientific literature."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Sentiment(Enum):
    """Sentiment."""
    SUPPORTING = "supporting"
    DISPUTING = "disputing"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class Claim:
    """Extracted scientific claim."""

    text: str
    source: str
    context: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContradictionResult:
    """Result of contradiction detection between two claims."""

    claim_a: Claim
    claim_b: Claim
    contradiction_score: float  # 0.0 - 1.0
    semantic_similarity: float  # 0.0 - 1.0
    sentiment_a_to_b: Sentiment
    sentiment_b_to_a: Sentiment
    explanation: str = ""
    confidence: float = 0.0


class ClaimExtractor:
    """Extract scientific claims from text using NLP patterns."""

    # Regex patterns for claim detection
    CLAIM_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"[Ww]e (?:show|demonstrate|prove|find|observe) that ([^.]+)"),
        re.compile(r"[Rr]esults (?:indicate|suggest|show|demonstrate) that ([^.]+)"),
        re.compile(r"[Oo]ur (?:findings|results|data) (?:suggest|indicate|show|support) that ([^.]+)"),
        re.compile(r"[Tt]his (?:study|paper|work) (?:shows|demonstrates|proves|finds) that ([^.]+)"),
        re.compile(r"[Ii]t (?:is|was) (?:shown|demonstrated|found|observed) that ([^.]+)"),
        re.compile(r"([^.]{20,200}?)(?:is|are) (?:inconsistent with|contradict|oppose|challenge) ([^.]{20,200}?)"),
    ]

    NEGATION_WORDS: set[str] = {
        "not", "no", "never", "none", "neither", "nor", "without",
        "does not", "do not", "did not", "cannot", "can't", "won't",
        "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't",
    }

    def __init__(self, min_claim_length: int = 20, max_claim_length: int = 300) -> None:
        self.min_claim_length = min_claim_length
        self.max_claim_length = max_claim_length

    def _is_likely_claim(self, text: str) -> bool:
        """Check if text contains scientific claim indicators."""
        claim_indicators = [
            "show", "demonstrate", "prove", "find", "observe", "indicate",
            "suggest", "results", "findings", "data", "study", "paper",
            "work", "shown", "demonstrated", "found", "observed",
            "consistent with", "contradict", "oppose", "challenge",
            "because", "since", "due to", "causes", "leads to", "therefore",
            "thus", "however", "although", "whereas", "while",
        ]
        text_lower = text.lower()
        return any(ind in text_lower for ind in claim_indicators)

    def extract(self, text: str, source: str = "") -> list[Claim]:
        """Extract claims from a text."""
        claims: list[Claim] = []
        sentences = self._split_sentences(text)

        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < self.min_claim_length:
                continue

            # Pattern-based extraction
            for pattern in self.CLAIM_PATTERNS:
                for match in pattern.finditer(sent):
                    claim_text = match.group(1).strip() if match.lastindex else match.group(0).strip()
                    if self.min_claim_length <= len(claim_text) <= self.max_claim_length:
                        confidence = self._score_claim(claim_text, sent)
                        claims.append(Claim(
                            text=claim_text,
                            source=source,
                            context=sent,
                            confidence=confidence,
                        ))

            # Fallback: sentence-level claim detection
            if not any(p.search(sent) for p in self.CLAIM_PATTERNS):
                confidence = self._score_claim(sent, sent)
                if confidence > 0.3 and self._is_likely_claim(sent):
                    claims.append(Claim(
                        text=sent,
                        source=source,
                        context=sent,
                        confidence=confidence,
                    ))

        # Deduplicate by text similarity
        return self._deduplicate(claims)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        text = re.sub(r"([.!?])\s+", r"\1|SPLIT|", text)
        return [s.strip() for s in text.split("|SPLIT|") if s.strip()]

    def _score_claim(self, claim_text: str, context: str) -> float:
        """Score how likely a text fragment is a scientific claim."""
        score = 0.5

        # Length heuristic
        length = len(claim_text)
        if 50 <= length <= 200:
            score += 0.1

        # Contains numerical data
        if re.search(r"\d+(?:\.\d+)?%?|\b\d{4}\b", claim_text):
            score += 0.1

        # Contains causal language
        causal_words = {"because", "since", "due to", "causes", "leads to", "results in", "therefore", "thus"}
        if any(w in claim_text.lower() for w in causal_words):
            score += 0.1

        # Contains uncertainty qualifiers (scientific hedging)
        hedge_words = {"may", "might", "could", "suggest", "indicate", "likely", "probably", "approximately"}
        if any(w in claim_text.lower() for w in hedge_words):
            score += 0.05

        # Negation penalty (claims are usually positive assertions)
        if any(w in claim_text.lower() for w in self.NEGATION_WORDS):
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _deduplicate(self, claims: list[Claim], threshold: float = 0.85) -> list[Claim]:
        """Remove near-duplicate claims."""
        if len(claims) <= 1:
            return claims

        texts = [c.text for c in claims]
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            X = vectorizer.fit_transform(texts)
        except ValueError:
            return claims

        sim_matrix = cosine_similarity(X)
        keep = [True] * len(claims)

        for i in range(len(claims)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(claims)):
                if sim_matrix[i, j] > threshold:
                    keep[j] = False

        return [claims[i] for i in range(len(claims)) if keep[i]]


class ContradictionDetector:
    """Detect contradictions between scientific claims."""

    # Lexical contradiction markers
    CONTRADICTION_MARKERS: list[str] = [
        "not", "no", "never", "none", "contradict", "inconsistent",
        "oppose", "challenge", "refute", "dispute", "disagree",
        "unlike", "rather than", "instead of", "false", "incorrect",
    ]

    # Entailment / paraphrase indicators
    ALIGNMENT_MARKERS: list[str] = [
        "support", "confirm", "agree", "consistent", "similar",
        "likewise", "also", "furthermore", "moreover", "in addition",
    ]

    def __init__(self, similarity_threshold: float = 0.35, contradiction_threshold: float = 0.5) -> None:
        self.similarity_threshold = similarity_threshold
        self.contradiction_threshold = contradiction_threshold
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def detect(self, claim_a: Claim, claim_b: Claim) -> ContradictionResult:
        """Detect contradiction between two claims."""
        # Semantic similarity
        texts = [claim_a.text, claim_b.text]
        try:
            X = self.vectorizer.fit_transform(texts)
            sim = float(cosine_similarity(X[0:1], X[1:2])[0, 0])
        except ValueError:
            sim = 0.0

        # Check for direct negation even with low semantic similarity
        a_text = claim_a.text.lower()
        b_text = claim_b.text.lower()
        direct_negation = self._is_direct_negation(a_text, b_text)

        # Topic relevance filter — bypass if direct negation detected
        if sim < self.similarity_threshold and not direct_negation:
            return ContradictionResult(
                claim_a=claim_a,
                claim_b=claim_b,
                contradiction_score=0.0,
                semantic_similarity=sim,
                sentiment_a_to_b=Sentiment.NEUTRAL,
                sentiment_b_to_a=Sentiment.NEUTRAL,
                explanation="Claims are on different topics (low semantic similarity)",
                confidence=0.8,
            )

        # Contradiction scoring
        contradiction_score = self._score_contradiction(claim_a, claim_b, sim)
        # Boost score for direct negation pairs
        if direct_negation:
            contradiction_score = max(contradiction_score, 0.5)

        sentiment_a_to_b = self._classify_sentiment(claim_a, claim_b)
        sentiment_b_to_a = self._classify_sentiment(claim_b, claim_a)

        is_contradiction = contradiction_score >= self.contradiction_threshold

        if is_contradiction:
            explanation = (
                f"High contradiction score ({contradiction_score:.3f}) between "
                f"semantically similar claims (sim={sim:.3f})"
            )
        else:
            explanation = (
                f"No significant contradiction detected (score={contradiction_score:.3f}, "
                f"sim={sim:.3f})"
            )

        confidence = min(sim * 2, 1.0) if is_contradiction else 1.0 - contradiction_score

        return ContradictionResult(
            claim_a=claim_a,
            claim_b=claim_b,
            contradiction_score=contradiction_score,
            semantic_similarity=sim,
            sentiment_a_to_b=sentiment_a_to_b,
            sentiment_b_to_a=sentiment_b_to_a,
            explanation=explanation,
            confidence=confidence,
        )

    def _score_contradiction(self, claim_a: Claim, claim_b: Claim, semantic_sim: float) -> float:
        """Score the likelihood of contradiction between two claims."""
        score = 0.0

        # Base: high similarity + opposite polarity = contradiction
        a_text = claim_a.text.lower()
        b_text = claim_b.text.lower()

        # Polarity analysis
        a_neg = sum(1 for w in self.CONTRADICTION_MARKERS if w in a_text)
        b_neg = sum(1 for w in self.CONTRADICTION_MARKERS if w in b_text)

        # One positive, one negative on same topic = contradiction
        polarity_diff = abs(a_neg - b_neg)
        if polarity_diff > 0 and semantic_sim > 0.4:
            score += 0.3 * polarity_diff

        # Direct negation detection
        if self._is_direct_negation(a_text, b_text):
            score += 0.5

        # Numeric contradiction
        numeric_contra = self._numeric_contradiction(a_text, b_text)
        if numeric_contra > 0:
            score += numeric_contra

        # Semantic similarity modulation
        # Very similar claims with opposite polarity = strong contradiction
        if semantic_sim > 0.7 and polarity_diff > 0:
            score += 0.2

        return min(score, 1.0)

    def _is_direct_negation(self, text_a: str, text_b: str) -> bool:
        """Check if one text is a direct negation of the other."""
        # Check for explicit negation patterns first
        negation_patterns = [
            r"\bnot\b", r"\bno\b", r"\bnever\b", r"\bnone\b",
            r"\bneither\b", r"\bnor\b", r"\bwithout\b",
            r"\bdoes not\b", r"\bdo not\b", r"\bdid not\b",
            r"\bcannot\b", r"\bcan't\b", r"\bwon't\b",
            r"\bisn't\b", r"\baren't\b", r"\bwasn't\b",
            r"\bweren't\b", r"\bhasn't\b", r"\bhaven't\b",
        ]
        a_has_neg = any(re.search(p, text_a) for p in negation_patterns)
        b_has_neg = any(re.search(p, text_b) for p in negation_patterns)

        # Both negated or neither negated = not a direct negation pair
        if a_has_neg == b_has_neg:
            return False

        # Remove negation words and compare
        def clean_negation(text: str) -> str:
            """Clean negation."""
            for p in negation_patterns:
                text = re.sub(p, "", text)
            # Remove orphaned auxiliary verbs left by negation removal
            text = re.sub(r"\b(does|do|did|is|are|was|were|has|have|can|will)\b", "", text)
            return re.sub(r"\s+", " ", text).strip()

        clean_a = clean_negation(text_a)
        clean_b = clean_negation(text_b)

        # If texts are similar after removing negation, they may be negations
        if not clean_a or not clean_b:
            return False

        # Simple word overlap
        words_a = set(clean_a.split())
        words_b = set(clean_b.split())
        if not words_a or not words_b:
            return False
        overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
        return overlap >= 0.5

    def _numeric_contradiction(self, text_a: str, text_b: str) -> float:
        """Detect contradictions in numeric claims."""
        nums_a = [float(m) for m in re.findall(r"\b(\d+(?:\.\d+)?)\b", text_a)]
        nums_b = [float(m) for m in re.findall(r"\b(\d+(?:\.\d+)?)\b", text_b)]

        if not nums_a or not nums_b:
            return 0.0

        # Compare closest numbers
        contradictions = 0
        for na in nums_a:
            for nb in nums_b:
                if na != 0 and abs(na - nb) / na > 0.5:
                    contradictions += 1
                elif na == 0 and nb != 0:
                    contradictions += 1

        return min(contradictions * 0.15, 0.5)

    def _classify_sentiment(self, from_claim: Claim, to_claim: Claim) -> Sentiment:
        """Classify sentiment of one claim toward another."""
        from_text = from_claim.text.lower()
        to_text = to_claim.text.lower()

        # Check for explicit dispute
        dispute_count = sum(1 for w in self.CONTRADICTION_MARKERS if w in from_text)
        support_count = sum(1 for w in self.ALIGNMENT_MARKERS if w in from_text)

        if dispute_count > support_count:
            return Sentiment.DISPUTING
        elif support_count > dispute_count:
            return Sentiment.SUPPORTING

        # Check if from_claim references to_claim's findings negatively
        combined = from_text + " " + to_text
        if any(w in from_text for w in self.CONTRADICTION_MARKERS):
            # Check semantic similarity to see if they're about same topic
            try:
                X = self.vectorizer.fit_transform([from_text, to_text])
                sim = float(cosine_similarity(X[0:1], X[1:2])[0, 0])
                if sim > 0.4:
                    return Sentiment.DISPUTING
            except ValueError:
                pass

        return Sentiment.NEUTRAL

    def find_all_contradictions(self, claims: list[Claim]) -> list[ContradictionResult]:
        """Find all contradictions in a set of claims (O(n²))."""
        results: list[ContradictionResult] = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                result = self.detect(claims[i], claims[j])
                if result.contradiction_score >= self.contradiction_threshold:
                    results.append(result)
        return results


class CitationSentimentAnalyzer:
    """Analyze sentiment of citations (supporting vs disputing)."""

    SUPPORTING_CUES: list[str] = [
        "support", "confirm", "validate", "replicate", "extend", "build upon",
        "consistent with", "in line with", "agree with", "corroborate",
        "strengthen", "reinforce", "affirm", "uphold",
    ]

    DISPUTING_CUES: list[str] = [
        "contradict", "challenge", "refute", "dispute", "question",
        "inconsistent with", "fail to replicate", "not support",
        "undermine", "weaken", "cast doubt", "disagree with",
        "oppose", "rebut", "counter",
    ]

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def analyze(self, citing_text: str, cited_work: str = "") -> Sentiment:
        """Analyze sentiment of a citation context."""
        text_lower = citing_text.lower()

        support_score = sum(1 for cue in self.SUPPORTING_CUES if cue in text_lower)
        dispute_score = sum(1 for cue in self.DISPUTING_CUES if cue in text_lower)

        if support_score > dispute_score:
            return Sentiment.SUPPORTING
        elif dispute_score > support_score:
            return Sentiment.DISPUTING
        return Sentiment.NEUTRAL

    def score_citation(self, citing_text: str, cited_work: str = "") -> dict[str, Any]:
        """Score a citation with detailed metrics."""
        text_lower = citing_text.lower()

        support_hits = [cue for cue in self.SUPPORTING_CUES if cue in text_lower]
        dispute_hits = [cue for cue in self.DISPUTING_CUES if cue in text_lower]

        sentiment = self.analyze(citing_text, cited_work)

        # Confidence based on cue density
        total_cues = len(support_hits) + len(dispute_hits)
        words = len(text_lower.split())
        confidence = min(total_cues / max(words / 50, 1), 1.0)

        return {
            "sentiment": sentiment.value,
            "support_cues": support_hits,
            "dispute_cues": dispute_hits,
            "confidence": confidence,
            "cited_work": cited_work,
        }

    def batch_analyze(self, citations: list[tuple[str, str]]) -> list[dict[str, Any]]:
        """Analyze multiple citations."""
        return [self.score_citation(text, work) for text, work in citations]
