"""Profiler — detect user's MP profile from text input.

Maps detected profiles to C4 attractor clusters and suggests
cognitive shifts for problem-solving.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from .core import (
    ALL_METAPROGRAMS,
    AgencyAxis,
    C4Coord,
    Metaprogram,
    ScaleAxis,
    TemporalAxis,
)


# ─── Scoring weights ──────────────────────────────────────────────────────
KEYWORD_MATCH_WEIGHT: Final[float] = 1.0
KEYWORD_DENSITY_BONUS: Final[float] = 0.3
CATEGORY_NORMALIZATION: Final[bool] = True


@dataclass(frozen=True)
class MPScore:
    """Score for a single metaprogram detection."""

    metaprogram: Metaprogram
    raw_score: float
    keyword_hits: int
    matched_keywords: tuple[str, ...]

    @property
    def normalized_score(self) -> float:
        """Score normalized by keyword count (more keywords = more reliable)."""
        return self.raw_score * (1 + KEYWORD_DENSITY_BONUS * self.keyword_hits)


@dataclass
class UserProfile:
    """Complete MP profile for a user/text."""

    scores: list[MPScore] = field(default_factory=list)
    dominant_temporal: TemporalAxis | None = None
    dominant_scale: ScaleAxis | None = None
    dominant_agency: AgencyAxis | None = None
    text_sample: str = ""

    @property
    def dominant_mps(self) -> list[MPScore]:
        """Top-scoring metaprograms, sorted descending."""
        return sorted(self.scores, key=lambda s: s.normalized_score, reverse=True)

    def top_n(self, n: int = 5) -> list[MPScore]:
        """Top N metaprograms by normalized score."""
        return self.dominant_mps[:n]

    @property
    def c4_centroid(self) -> C4Coord | None:
        """Compute the average C4 coordinate of detected MPs."""
        if not self.scores:
            return None
        total_weight = sum(s.normalized_score for s in self.scores)
        if total_weight == 0:
            return None

        t_sum = s_sum = a_sum = 0.0
        for s in self.scores:
            t, s_val, a = s.metaprogram.c4.to_tuple()
            w = s.normalized_score / total_weight
            t_sum += t * w
            s_sum += s_val * w
            a_sum += a * w

        # Map back to nearest enum value
        t_map = [TemporalAxis.PAST, TemporalAxis.PRESENT, TemporalAxis.FUTURE]
        s_map = [ScaleAxis.CONCRETE, ScaleAxis.ABSTRACT, ScaleAxis.META]
        a_map = [AgencyAxis.SELF, AgencyAxis.OTHER, AgencyAxis.SYSTEM]

        return C4Coord(
            t_map[round(t_sum)],
            s_map[round(s_sum)],
            a_map[round(a_sum)],
        )

    def category_distribution(self) -> dict[str, float]:
        """Relative strength per category."""
        cat_scores: dict[str, float] = {}
        for s in self.scores:
            cat = s.metaprogram.category
            cat_scores[cat] = cat_scores.get(cat, 0.0) + s.normalized_score
        total = sum(cat_scores.values()) or 1.0
        return {cat: score / total for cat, score in cat_scores.items()}


def _tokenize(text: str) -> list[str]:
    """Lowercase and tokenize text into words."""
    return re.findall(r"[a-zA-Z']+", text.lower())


def detect_profile(text: str, min_score_threshold: float = 0.5) -> UserProfile:
    """Analyze text and return a UserProfile with detected MPs.

    Uses keyword matching + heuristics (no mock data).
    """
    tokens = _tokenize(text)
    token_set = set(tokens)
    text_lower = text.lower()
    scores: list[MPScore] = []

    for mp in ALL_METAPROGRAMS:
        matched: list[str] = []
        for kw in mp.keywords:
            # Phrase matching (multi-word keywords)
            if " " in kw:
                if kw in text_lower:
                    matched.append(kw)
            else:
                if kw in token_set:
                    matched.append(kw)

        if not matched:
            continue

        raw_score = len(matched) * KEYWORD_MATCH_WEIGHT
        # Bonus for repeated keyword occurrences
        for kw in matched:
            if " " in kw:
                raw_score += text_lower.count(kw) * 0.5
            else:
                raw_score += tokens.count(kw) * 0.5

        if raw_score < min_score_threshold:
            continue

        scores.append(
            MPScore(
                metaprogram=mp,
                raw_score=raw_score,
                keyword_hits=len(matched),
                matched_keywords=tuple(matched),
            )
        )

    profile = UserProfile(scores=scores, text_sample=text[:200])

    # Determine dominant axes from top MPs
    if profile.dominant_mps:
        top = profile.dominant_mps[:7]
        t_counts: dict[TemporalAxis, float] = {}
        s_counts: dict[ScaleAxis, float] = {}
        a_counts: dict[AgencyAxis, float] = {}

        for s in top:
            c4 = s.metaprogram.c4
            w = s.normalized_score
            t_counts[c4.temporal] = t_counts.get(c4.temporal, 0.0) + w
            s_counts[c4.scale] = s_counts.get(c4.scale, 0.0) + w
            a_counts[c4.agency] = a_counts.get(c4.agency, 0.0) + w

        profile.dominant_temporal = max(t_counts, key=t_counts.get)  # type: ignore[arg-type]
        profile.dominant_scale = max(s_counts, key=s_counts.get)  # type: ignore[arg-type]
        profile.dominant_agency = max(a_counts, key=a_counts.get)  # type: ignore[arg-type]

    return profile


# ─── Cognitive Shift Suggestions ──────────────────────────────────────────

SHIFT_SUGGESTIONS: Final[dict[tuple[str, str], list[str]]] = {
    # Temporal shifts
    ("Temporal", "Past Orientation"): [
        "Try shifting to Present: what can you do right now?",
        "Future: what outcome do you want to create from this?",
    ],
    ("Temporal", "Present Orientation"): [
        "Past: what patterns from history apply here?",
        "Future: where is this leading if unchanged?",
    ],
    ("Temporal", "Future Orientation"): [
        "Present: what is the very next step you can take today?",
        "Past: what has worked before that you can reuse?",
    ],
    # Scale shifts
    ("Scale", "Concrete-Detail"): [
        "Abstract: what general principle connects these details?",
        "Meta: what system generates these concrete phenomena?",
    ],
    ("Scale", "Abstract-General"): [
        "Concrete: give one specific example of this principle.",
        "Meta: what framework contains this abstraction?",
    ],
    ("Scale", "Meta-Systemic"): [
        "Concrete: what is one tangible instance of this system?",
        "Abstract: what pattern emerges across system instances?",
    ],
    # Agency shifts
    ("Agency", "Self-Agency"): [
        "Other: who else is affected and what do they need?",
        "System: what structural forces are shaping this situation?",
    ],
    ("Agency", "External-Agency"): [
        "Self: what is within your direct control right now?",
        "System: what emergent properties are at play?",
    ],
    ("Agency", "System-Agency"): [
        "Self: what is one action you can personally take?",
        "Other: who can you collaborate with directly?",
    ],
    # Process shifts
    ("Process", "Action-Oriented"): [
        "Reflect: what assumptions are driving this action?",
        "Iterate: how will you learn from the outcome?",
    ],
    ("Process", "Reflection-Oriented"): [
        "Action: what is the smallest experiment you can run?",
        "Iterate: set a timer and act when it rings.",
    ],
    # Result shifts
    ("Result", "Goal-Focused"): [
        "Journey: what are you learning along the way?",
        "Satisfice: is good enough better than perfect here?",
    ],
    ("Result", "Journey-Focused"): [
        "Goal: what specific outcome would indicate success?",
        "Legacy: what enduring impact do you want?",
    ],
    # Communication shifts
    ("Communication", "Internal-Reference"): [
        "External: what does the data or feedback say?",
        "Empathetic: how do others experience this?",
    ],
    ("Communication", "External-Reference"): [
        "Internal: what is your gut telling you?",
        "Visual: can you picture the ideal outcome?",
    ],
    # Meta-cognitive shifts
    ("Meta-cognitive", "Observer-O0"): [
        "O1: step back — notice that you are thinking this.",
        "O2: observe the pattern of when you get stuck.",
    ],
    ("Meta-cognitive", "Observer-O1"): [
        "O0: immerse fully — what does it feel like to just think?",
        "O2: notice how you notice — what triggers awareness?",
    ],
    ("Meta-cognitive", "Observer-O2"): [
        "O1: drop one level — observe a single thought directly.",
        "O0: fully immerse in raw experience without analysis.",
    ],
}


def suggest_shifts(profile: UserProfile, top_k: int = 3) -> list[dict[str, str]]:
    """Suggest cognitive shifts based on detected dominant MPs.

    Returns list of dicts with 'from_mp', 'to_suggestions' keys.
    """
    suggestions: list[dict[str, str]] = []
    seen_cats: set[str] = set()

    for score in profile.dominant_mps:
        mp = score.metaprogram
        if mp.category in seen_cats:
            continue
        seen_cats.add(mp.category)

        key = (mp.category, mp.name)
        shifts = SHIFT_SUGGESTIONS.get(key, [])
        if shifts:
            suggestions.append(
                {
                    "from_mp": f"{mp.code}: {mp.name}",
                    "category": mp.category,
                    "c4": repr(mp.c4),
                    "suggestions": " | ".join(shifts),
                }
            )

        if len(suggestions) >= top_k:
            break

    return suggestions


def profile_to_attractor_cluster(profile: UserProfile) -> str:
    """Map a user profile to a named C4 attractor cluster.

    Clusters are named by their dominant T/S/A combination.
    """
    if profile.c4_centroid is None:
        return "undetermined"

    c4 = profile.c4_centroid
    t_name = c4.temporal.name.lower()
    s_name = c4.scale.name.lower()
    a_name = c4.agency.name.lower()

    # Named clusters
    cluster_names: dict[tuple[str, str, str], str] = {
        ("present", "concrete", "self"): "experiential-actor",
        ("present", "concrete", "other"): "compassionate-presence",  # Φ
        ("present", "abstract", "self"): "reflective-awareness",
        ("present", "abstract", "other"): "dialogical-understanding",
        ("present", "meta", "system"): "systemic-observer",
        ("future", "concrete", "self"): "goal-driven-achiever",
        ("future", "abstract", "system"): "strategic-architect",
        ("past", "concrete", "self"): "experiential-learner",
        ("past", "abstract", "system"): "historical-analyst",
        ("future", "meta", "system"): "visionary-designer",
    }

    return cluster_names.get(
        (t_name, s_name, a_name),
        f"{t_name}-{s_name}-{a_name}",
    )
