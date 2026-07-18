from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.discovery.already_shifted import AlreadyShiftedDetector


_llm_reason: Any | None = None
try:
    from src.plugins._llm_base import _llm_reason as _llm_reason_impl

    _llm_reason = _llm_reason_impl
except ImportError:
    pass

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _HAVE_SKLEARN = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    _HAVE_SKLEARN = False


logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """N-version gate verdict — voted by multiple implementations."""

    passed: bool | None
    score: float
    confidence: float
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    dissenting: list[GateResult] = field(default_factory=list)
    abstained: bool = False


@runtime_checkable
class GateFunction(Protocol):
    """Protocol for redundant gate implementations.

    Each implementation must be an async callable that accepts **kwargs
    and returns a GateResult. Different gate types pass different kwargs
    (e.g. paradigm gates receive hypothesis/papers, novelty gates receive
    text/known_corpus, review gates receive draft/rules).
    """

    async def check(self, **kwargs: Any) -> GateResult: ...


class RedundantGate:
    """N-version programming gate — runs multiple implementations in parallel.

    An N-version gate exists because critical quality decisions (novelty,
    paradigm-shift, self-critique) are too easy for a single model to fudge.
    By running 3 independent implementations and requiring a minimum agreement
    threshold, we reduce the risk of a wrong PASS slipping through.

    Agreement threshold (min_agreement) defaults to 0.5 — a simple majority.
    Set to 0.67 (2/3) or 1.0 (unanimous) for higher-stakes gates.
    """

    def __init__(self, implementations: list[GateFunction], min_agreement: float = 0.5) -> None:
        if not implementations:
            raise ValueError("At least one implementation required")
        if not 0.0 <= min_agreement <= 1.0:
            raise ValueError("min_agreement must be between 0.0 and 1.0")
        self._implementations = implementations
        self._min_agreement = min_agreement

    @property
    def min_agreement(self) -> float:
        return self._min_agreement

    async def check(self, **kwargs: Any) -> GateResult:
        results: list[GateResult] = list(
            await asyncio.gather(*(impl.check(**kwargs) for impl in self._implementations))
        )

        voters = [r for r in results if r.confidence > 0.0] or results
        total = len(voters)
        votes = sum(1 for r in voters if r.passed)
        required = total * self._min_agreement
        passed = votes >= required
        confidence = votes / total if total > 0 else 0.0

        dissenting = [r for r in voters if not r.passed]
        scores = [r.score for r in voters]
        all_scores = [r.score for r in results]

        if dissenting:
            rationales = "; ".join(d.message for d in dissenting if d.message)
            logger.warning(
                "RedundantGate disagreement: %d/%d passed (threshold=%.0f%%). Dissenting: %s",
                votes,
                total,
                self._min_agreement * 100,
                rationales,
            )

        return GateResult(
            passed=passed,
            score=sum(all_scores) / len(all_scores) if all_scores else 0.0,
            confidence=confidence,
            message=f"Consensus: {votes}/{total} implementations agree",
            details={
                "votes": votes,
                "total": total,
                "total_with_stubs": len(results),
                "min_agreement": self._min_agreement,
                "required_votes": int(required) if required == int(required) else required,
                "individual_scores": scores,
            },
            dissenting=dissenting,
        )


# ── ParadigmShiftGate implementations ──────────────────────────────────


class ParadigmShiftKeywordVariant:
    """Variant 1: keyword-based AlreadyShiftedDetector.

    Wraps the existing AlreadyShiftedDetector from src.discovery.already_shifted
    and converts its dict return into a GateResult.
    """

    def __init__(self) -> None:
        self._detector = AlreadyShiftedDetector()

    async def check(self, **kwargs: Any) -> GateResult:
        hypothesis = kwargs.get("hypothesis", "")
        papers = kwargs.get("papers", [])
        citation_timeline = kwargs.get("citation_timeline")
        domain = kwargs.get("domain", "general")

        result: dict[str, Any] = await self._detector.check(
            hypothesis=hypothesis,
            papers=papers,
            citation_timeline=citation_timeline,
            domain=domain,
        )

        already_shifted: bool = result.get("already_shifted", False)
        confidence_val: float = result.get("confidence", 0.0)
        passed = not already_shifted  # PASS if NOT already shifted

        return GateResult(
            passed=passed,
            score=1.0 - confidence_val if already_shifted else confidence_val,
            confidence=confidence_val,
            message=result.get("verdict", result.get("explanation", "")),
            details=result,
        )


class ParadigmShiftSemanticVariant:
    """Variant 2: semantic similarity against known-shifted corpora via TfidfVectorizer."""

    _KNOWN_SHIFTED_ABSTRACTS: list[str] = [
        "The theory of general relativity fundamentally alters our understanding of gravity, showing that massive objects curve spacetime. This paradigm shift replaced Newton's absolute space and time with a dynamic geometric framework.",
        "Quantum mechanics introduces fundamental indeterminacy at the microscopic scale, replacing classical determinism with probabilistic wave functions and observer-dependent measurement outcomes.",
        "Continental drift and plate tectonics revolutionized geology by demonstrating that Earth's continents are not fixed but move on large-scale plates, explaining earthquakes, volcanoes, and mountain formation.",
        "The discovery that DNA carries genetic information through a double-helix structure transformed biology, establishing molecular genetics as the foundation for understanding heredity and evolution.",
        "The Copernican revolution displaced Earth from the center of the universe, establishing a heliocentric model that fundamentally reorganized astronomy and natural philosophy.",
        "Germ theory of disease replaced miasma theory by demonstrating that microorganisms cause infectious diseases, transforming medicine, public health, and surgery.",
        "Information theory established a mathematical framework for communication, quantifying information entropy and channel capacity, which reshaped telecommunications, computing, and cryptography.",
        "Evolution by natural selection provided a mechanistic explanation for the diversity of life without invoking design, fundamentally altering biology, psychology, and philosophy.",
        "The endosymbiotic theory proposed that eukaryotic organelles originated from free-living prokaryotes engulfed by ancestral cells, revolutionizing our understanding of cellular evolution.",
        "The holographic principle suggests that all information contained in a volume of space can be represented on its boundary, potentially resolving the black hole information paradox and unifying quantum mechanics with gravity.",
        "CRISPR-Cas9 gene editing has transformed molecular biology by enabling precise, programmable modification of genomes, shifting the paradigm from reading DNA to writing it at will.",
        "Deep learning has overturned decades of feature engineering in AI, demonstrating that hierarchical representations learned from raw data can surpass hand-crafted systems across vision, language, and reasoning.",
    ]

    async def check(self, **kwargs: Any) -> GateResult:
        hypothesis: str = kwargs.get("hypothesis", "")
        if not hypothesis:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="No hypothesis provided",
            )
        if not _HAVE_SKLEARN:
            logger.warning("sklearn unavailable — falling back to stub")
            return GateResult(
                passed=None,
                score=0.0,
                confidence=0.0,
                message="abstained: sklearn not installed",
                details={},
                abstained=True,
            )

        corpus = [hypothesis] + self._KNOWN_SHIFTED_ABSTRACTS
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        max_sim = float(similarities.max())
        threshold = kwargs.get("threshold", 0.15)
        passed = max_sim > threshold
        confidence = min(0.7, max(0.3, max_sim * 2.0))
        score = max_sim

        return GateResult(
            passed=passed,
            score=score,
            confidence=confidence,
            message=f"{'PARADIGM-SHIFT-LIKE' if passed else 'NOT-SHIFT-LIKE'} — max cosine similarity={max_sim:.3f} (threshold={threshold})",
            details={
                "max_cosine_similarity": round(max_sim, 4),
                "threshold": threshold,
                "method": "tfidf",
            },
        )


class ParadigmShiftLLMVariant:
    """Variant 3: LLM-based paradigm shift judge via _llm_reason."""

    _PROMPT = """You are a scientific paradigm expert evaluating whether a research hypothesis represents a genuine paradigm shift.

A paradigm shift redefines fundamental assumptions in a field, opens entirely new research directions, and cannot be reduced to incremental improvement of existing frameworks.

Hypothesis:
{hypothesis}

Rate this hypothesis on a scale from 0 (purely incremental) to 10 (truly revolutionary paradigm shift).
Then state PASS or FAIL based on whether the score >= 6.

Respond ONLY with valid JSON in this exact format:
{{"score": <int 0-10>, "verdict": "PASS" or "FAIL", "confidence": <float 0.0-1.0>, "rationale": "<1-2 sentence explanation>"}}"""

    async def check(self, **kwargs: Any) -> GateResult:
        hypothesis: str = kwargs.get("hypothesis", "")
        if not hypothesis:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="No hypothesis provided",
            )

        if _llm_reason is None:
            logger.warning("_llm_base unavailable — falling back to stub")
            return GateResult(
                passed=None,
                score=0.0,
                confidence=0.0,
                message="abstained: _llm_base not available",
                details={},
                abstained=True,
            )

        prompt = self._PROMPT.format(hypothesis=hypothesis[:3000])
        response = await asyncio.to_thread(
            _llm_reason,
            prompt,
            "You are a rigorous scientific paradigm evaluator. Return only JSON.",
            600,
            0.3,
        )

        if not response:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM unavailable — neutral abstain",
                details={"error": "no_response"},
            )

        try:
            data = self._parse_json(response)
        except Exception as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM response parse error — neutral abstain",
                details={"error": str(e), "raw": response[:200]},
            )

        verdict: str = data.get("verdict", "").upper().strip()
        score_val: float = float(data.get("score", 0)) / 10.0
        confidence_val: float = min(0.9, max(0.5, float(data.get("confidence", 0.5))))
        passed = verdict == "PASS"

        return GateResult(
            passed=passed,
            score=score_val,
            confidence=confidence_val,
            message=data.get("rationale", verdict),
            details={"llm_verdict": verdict, "llm_score": data.get("score"), "method": "llm_judge"},
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)


# ── NoveltyGate implementations ────────────────────────────────────────


class NoveltyJaccardVariant:
    """Variant 1: Jaccard-based keyword similarity against known corpus."""

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(text.lower().split())

    async def check(self, **kwargs: Any) -> GateResult:
        text: str = kwargs.get("text", "")
        known_corpus: list[str] = kwargs.get("known_corpus", [])
        threshold: float = kwargs.get("threshold", 0.3)

        if not text:
            return GateResult(
                passed=True,
                score=0.5,
                confidence=0.0,
                message="Empty input — cannot assess novelty",
            )

        tokens = self._tokenize(text)
        max_similarity: float = 0.0
        closest: str = ""

        for doc in known_corpus:
            sim = self._jaccard(tokens, self._tokenize(doc))
            if sim > max_similarity:
                max_similarity = sim
                closest = doc[:120]

        novel = max_similarity < threshold
        score = 1.0 - max_similarity
        return GateResult(
            passed=novel,
            score=score,
            confidence=1.0 - max_similarity,
            message=f"{'NOVEL' if novel else 'DUPLICATE'} — max Jaccard={max_similarity:.3f} (threshold={threshold})",
            details={
                "max_jaccard": round(max_similarity, 4),
                "threshold": threshold,
                "closest_doc_preview": closest,
                "corpus_size": len(known_corpus),
            },
        )


class NoveltySemanticVariant:
    """Variant 2: semantic embedding similarity via TfidfVectorizer against known corpus."""

    async def check(self, **kwargs: Any) -> GateResult:
        text: str = kwargs.get("text", "")
        known_corpus: list[str] = kwargs.get("known_corpus", [])
        threshold: float = kwargs.get("threshold", 0.3)

        if not text:
            return GateResult(
                passed=True,
                score=0.5,
                confidence=0.0,
                message="Empty input — cannot assess novelty",
            )

        if not known_corpus:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="No corpus provided — cannot assess novelty",
                abstained=True,
            )

        if not _HAVE_SKLEARN:
            logger.warning("sklearn unavailable — falling back to stub")
            return GateResult(
                passed=None,
                score=0.0,
                confidence=0.0,
                message="abstained: sklearn not installed",
                details={},
                abstained=True,
            )

        corpus = [text] + known_corpus
        vectorizer = TfidfVectorizer(stop_words="english", max_features=800)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        max_sim = float(similarities.max())
        closest_idx = int(similarities.argmax())
        closest_preview = known_corpus[closest_idx][:120] if closest_idx < len(known_corpus) else ""
        novel = max_sim < threshold
        score = 1.0 - max_sim

        return GateResult(
            passed=novel,
            score=score,
            confidence=1.0 - max_sim,
            message=f"{'NOVEL' if novel else 'DUPLICATE'} — max cosine={max_sim:.3f} (threshold={threshold})",
            details={
                "max_cosine_similarity": round(max_sim, 4),
                "threshold": threshold,
                "closest_doc_preview": closest_preview,
                "corpus_size": len(known_corpus),
                "method": "tfidf",
            },
        )


class NoveltyLLMJudgeVariant:
    """Variant 3: LLM judge for novelty assessment via _llm_reason."""

    _PROMPT = """You are a scientific novelty assessor. Determine whether the following research claim is genuinely novel or if it overlaps substantially with the provided corpus of existing work.

Text to evaluate:
{text}

Known corpus (excerpts):
{corpus}

Rate novelty from 0 (completely known, trivial overlap) to 10 (entirely novel, no overlap).
State PASS if the claim is substantially novel (score >= 6) and FAIL otherwise.

Respond ONLY with valid JSON in this exact format:
{{"score": <int 0-10>, "verdict": "PASS" or "FAIL", "confidence": <float 0.0-1.0>, "rationale": "<1-2 sentence explanation>"}}"""

    async def check(self, **kwargs: Any) -> GateResult:
        text: str = kwargs.get("text", "")
        known_corpus: list[str] = kwargs.get("known_corpus", [])

        if not text:
            return GateResult(
                passed=True,
                score=0.5,
                confidence=0.0,
                message="Empty input — cannot assess novelty",
            )

        if _llm_reason is None:
            logger.warning("_llm_base unavailable — falling back to stub")
            return GateResult(
                passed=None,
                score=0.0,
                confidence=0.0,
                message="abstained: _llm_base not available",
                details={},
                abstained=True,
            )

        corpus_snippet = (
            "\n".join(f"- {doc[:200]}" for doc in known_corpus[:5])
            if known_corpus
            else "(no corpus provided)"
        )

        prompt = self._PROMPT.format(text=text[:3000], corpus=corpus_snippet[:3000])
        response = await asyncio.to_thread(
            _llm_reason, prompt, "You are a rigorous novelty assessor. Return only JSON.", 600, 0.3
        )

        if not response:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM unavailable — neutral abstain",
                details={"error": "no_response"},
            )

        try:
            data = self._parse_json(response)
        except Exception as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM response parse error — neutral abstain",
                details={"error": str(e), "raw": response[:200]},
            )

        verdict: str = data.get("verdict", "").upper().strip()
        score_val: float = float(data.get("score", 0)) / 10.0
        confidence_val: float = min(0.9, max(0.5, float(data.get("confidence", 0.5))))
        passed = verdict == "PASS"

        return GateResult(
            passed=passed,
            score=score_val,
            confidence=confidence_val,
            message=data.get("rationale", verdict),
            details={"llm_verdict": verdict, "llm_score": data.get("score"), "method": "llm_judge"},
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)


# ── SelfCritiqueGate implementations ────────────────────────────────────


class StructuredReviewerVariant:
    """Variant 1: structured reviewer — checks draft against a rubric."""

    RUBRIC: list[dict[str, Any]] = [
        {
            "name": "clarity",
            "keywords": ["unclear", "ambiguous", "vague", "confusing", "obscure"],
            "checks": ["Abstract present and concise", "Claims are testable"],
        },
        {
            "name": "rigor",
            "keywords": ["handwaving", "untestable", "unfalsifiable", "speculative"],
            "checks": ["Numerical predictions present", "Methodology described"],
        },
        {
            "name": "novelty",
            "keywords": ["incremental", "well-known", "trivial", "established", "already shown"],
            "checks": ["Avoids trivial extensions", "Surprising or non-obvious claim"],
        },
        {
            "name": "coherence",
            "keywords": ["contradicts", "inconsistent", "paradox", "conflict"],
            "checks": ["Internal logic consistent", "No self-contradiction"],
        },
    ]

    async def check(self, **kwargs: Any) -> GateResult:
        draft: str = kwargs.get("draft", "")
        if not draft:
            return GateResult(
                passed=True,
                score=0.0,
                confidence=0.0,
                message="No draft provided for review",
            )

        draft_lower = draft.lower()
        issues: list[str] = []
        total_checks = 0
        failed_checks = 0

        for category in self.RUBRIC:
            for kw in category["keywords"]:
                if kw in draft_lower:
                    issues.append(f"[{category['name']}] found keyword '{kw}'")
                    failed_checks += 1
                total_checks += 1

        score = 1.0 - (failed_checks / total_checks) if total_checks > 0 else 1.0
        passed = score >= 0.5
        return GateResult(
            passed=passed,
            score=score,
            confidence=0.8,
            message=f"Structured review: {failed_checks}/{total_checks} issues found"
            if issues
            else "Structured review: no issues found",
            details={
                "issues": issues,
                "failed_checks": failed_checks,
                "total_checks": total_checks,
            },
        )


class AdversarialReviewerVariant:
    """Variant 2: adversarial reviewer — LLM-powered hostile review via _llm_reason."""

    _PROMPT = """You are a hostile journal reviewer. Your job is to find every possible flaw in the following research draft. Be relentlessly critical.

Draft:
{draft}

Identify the most critical flaws. Then respond ONLY with valid JSON in this exact format:
{{"has_critical_flaws": true or false, "severity": <int 0-10 where 10=fatal>, "confidence": <float 0.0-1.0>, "flaws": ["<flaw 1>", "<flaw 2>", ...], "summary": "<1-2 sentence verdict>"}}"""

    async def check(self, **kwargs: Any) -> GateResult:
        draft: str = kwargs.get("draft", "")
        if not draft:
            return GateResult(
                passed=True,
                score=0.0,
                confidence=0.0,
                message="No draft provided for review",
            )

        if _llm_reason is None:
            logger.warning("_llm_base unavailable — falling back to stub")
            return GateResult(
                passed=None,
                score=0.0,
                confidence=0.0,
                message="abstained: _llm_base not available",
                details={},
                abstained=True,
            )

        prompt = self._PROMPT.format(draft=draft[:4000])
        response = await asyncio.to_thread(
            _llm_reason, prompt, "You are a hostile peer reviewer. Return only JSON.", 800, 0.4
        )

        if not response:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM unavailable — neutral abstain",
                details={"error": "no_response"},
            )

        try:
            data = self._parse_json(response)
        except Exception as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM response parse error — neutral abstain",
                details={"error": str(e), "raw": response[:200]},
            )

        has_critical: bool = data.get("has_critical_flaws", False)
        severity: int = data.get("severity", 0)
        confidence_val: float = min(0.9, max(0.5, float(data.get("confidence", 0.5))))
        passed = not has_critical and severity < 7
        score = 1.0 - (severity / 10.0)

        return GateResult(
            passed=passed,
            score=score,
            confidence=confidence_val,
            message=data.get("summary", "Adversarial review complete"),
            details={
                "has_critical_flaws": has_critical,
                "severity": severity,
                "flaws": data.get("flaws", []),
                "method": "llm_adversarial",
            },
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        match = re.search(r"\{[^{}]*\[.*?\][^{}]*\}", text, re.DOTALL) or re.search(
            r"\{[^{}]*\}", text, re.DOTALL
        )
        if match:
            return json.loads(match.group())
        return json.loads(text)


class DevilsAdvocateVariant:
    """Variant 3: devil's advocate — LLM-powered counter-argument via _llm_reason."""

    _PROMPT = """You are a devil's advocate. Argue against the following research hypothesis from every possible angle — theoretical, methodological, empirical, philosophical. Find every weakness, every unstated assumption, every counter-argument.

Hypothesis:
{hypothesis}

Respond ONLY with valid JSON in this exact format:
{{"arguments_are_convincing": true or false, "counterargument_strength": <int 0-10>, "confidence": <float 0.0-1.0>, "top_arguments": ["<arg 1>", "<arg 2>", "<arg 3>"], "summary": "<1-2 sentence verdict>"}}"""

    async def check(self, **kwargs: Any) -> GateResult:
        hypothesis: str = kwargs.get("hypothesis", "")
        if not hypothesis:
            return GateResult(
                passed=True,
                score=0.0,
                confidence=0.0,
                message="No hypothesis provided for devil's advocate review",
            )

        if _llm_reason is None:
            logger.warning("_llm_base unavailable — falling back to stub")
            return GateResult(
                passed=None,
                score=0.0,
                confidence=0.0,
                message="abstained: _llm_base not available",
                details={},
                abstained=True,
            )

        prompt = self._PROMPT.format(hypothesis=hypothesis[:4000])
        response = await asyncio.to_thread(
            _llm_reason,
            prompt,
            "You are a relentless devil's advocate. Return only JSON.",
            800,
            0.4,
        )

        if not response:
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM unavailable — neutral abstain",
                details={"error": "no_response"},
            )

        try:
            data = self._parse_json(response)
        except Exception as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            return GateResult(
                passed=False,
                score=0.0,
                confidence=0.0,
                message="LLM response parse error — neutral abstain",
                details={"error": str(e), "raw": response[:200]},
            )

        convincing: bool = data.get("arguments_are_convincing", False)
        strength: int = data.get("counterargument_strength", 0)
        confidence_val: float = min(0.9, max(0.5, float(data.get("confidence", 0.5))))
        passed = not convincing and strength < 7
        score = 1.0 - (strength / 10.0)

        return GateResult(
            passed=passed,
            score=score,
            confidence=confidence_val,
            message=data.get("summary", "Devil's advocate review complete"),
            details={
                "arguments_are_convincing": convincing,
                "counterargument_strength": strength,
                "top_arguments": data.get("top_arguments", []),
                "method": "llm_devils_advocate",
            },
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        match = re.search(r"\{[^{}]*\[.*?\][^{}]*\}", text, re.DOTALL) or re.search(
            r"\{[^{}]*\}", text, re.DOTALL
        )
        if match:
            return json.loads(match.group())
        return json.loads(text)


# ── Pre-built redundant gate configurations ────────────────────────────


def create_paradigm_shift_gate(min_agreement: float = 0.5) -> RedundantGate:
    return RedundantGate(
        implementations=[
            ParadigmShiftKeywordVariant(),
            ParadigmShiftSemanticVariant(),
            ParadigmShiftLLMVariant(),
        ],
        min_agreement=min_agreement,
    )


def create_novelty_gate(min_agreement: float = 0.5) -> RedundantGate:
    return RedundantGate(
        implementations=[
            NoveltyJaccardVariant(),
            NoveltySemanticVariant(),
            NoveltyLLMJudgeVariant(),
        ],
        min_agreement=min_agreement,
    )


def create_self_critique_gate(min_agreement: float = 0.5) -> RedundantGate:
    return RedundantGate(
        implementations=[
            StructuredReviewerVariant(),
            AdversarialReviewerVariant(),
            DevilsAdvocateVariant(),
        ],
        min_agreement=min_agreement,
    )
