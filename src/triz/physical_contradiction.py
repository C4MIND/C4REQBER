"""
TRIZ Physical Contradictions: Detection, Analysis, and Resolution.

Implements the 4 separation principles for resolving physical contradictions,
with C4 state-space mapping for cognitive transitions.
"""
from __future__ import annotations

import re
from typing import Any
from dataclasses import dataclass, field
from enum import Enum, auto

from src.c4.state import C4State


class SeparationType(Enum):
    """The four classical TRIZ separation principles for physical contradictions."""

    IN_TIME = auto()          # 1. Separation in Time
    IN_SPACE = auto()         # 2. Separation in Space
    PARTS_WHOLE = auto()      # 3. Separation between Parts and Whole
    UNDER_CONDITIONS = auto() # 4. Separation under Conditions


@dataclass(frozen=True)
class PhysicalContradiction:
    """
    A physical contradiction: an object must simultaneously possess
    a property and its opposite.

    Example: "The object must be HOT and COLD simultaneously."
    """
    object_name: str
    property: str
    opposite: str
    context: str = ""

    def __str__(self) -> str:
        base = f"'{self.object_name}' must be both {self.property} AND {self.opposite}"
        if self.context:
            base += f" in context: {self.context}"
        return base

    def to_dict(self) -> dict[str, str]:
        return {
            "object_name": self.object_name,
            "property": self.property,
            "opposite": self.opposite,
            "context": self.context,
            "contradiction_text": str(self),
        }


@dataclass
class SeparationStrategy:
    """
    A strategy for resolving a physical contradiction using one of the
    four separation principles, mapped to C4 cognitive transitions.
    """
    separation_type: SeparationType
    description: str
    c4_shift: str           # e.g., "time_shift", "scale_shift", "agency_shift"
    c4_trajectory: list[tuple[int, int, int]]  # Sequence of C4 state tuples
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "separation_type": self.separation_type.name,
            "description": self.description,
            "c4_shift": self.c4_shift,
            "c4_trajectory": self.c4_trajectory,
            "examples": self.examples,
        }


# =============================================================================
# DETECTION PATTERNS
# =============================================================================

# Semantic patterns for detecting physical contradictions in natural language
PHYSICAL_CONTRADICTION_PATTERNS: list[tuple[re.Pattern, int, int, int]] = [
    # Pattern: "X must be both [property] and [opposite]"
    (re.compile(
        r"(?P<object>\w+(?:\s+\w+){0,5})\s+must\s+be\s+both\s+(?P<prop>\w+)\s+and\s+(?P<opp>\w+)",
        re.IGNORECASE
    ), 1, 2, 3),
    # Pattern: "X needs to be [property] and [opposite] at the same time"
    (re.compile(
        r"(?P<object>\w+(?:\s+\w+){0,5})\s+(?:needs?|has)\s+to\s+be\s+(?P<prop>\w+)\s+and\s+(?P<opp>\w+)\s+at\s+the\s+same\s+time",
        re.IGNORECASE
    ), 1, 2, 3),
    # Pattern: "X should be [property] yet [opposite]"
    (re.compile(
        r"(?P<object>\w+(?:\s+\w+){0,5})\s+should\s+be\s+(?P<prop>\w+)\s+yet\s+(?P<opp>\w+)",
        re.IGNORECASE
    ), 1, 2, 3),
    # Pattern: "X must be [property] and [opposite] simultaneously"
    (re.compile(
        r"(?P<object>\w+(?:\s+\w+){0,5})\s+must\s+be\s+(?P<prop>\w+)\s+and\s+(?P<opp>\w+)\s+simultaneously",
        re.IGNORECASE
    ), 1, 2, 3),
    # Pattern: "X has to be [property] but also [opposite]"
    (re.compile(
        r"(?P<object>\w+(?:\s+\w+){0,5})\s+has\s+to\s+be\s+(?P<prop>\w+)\s+but\s+also\s+(?P<opp>\w+)",
        re.IGNORECASE
    ), 1, 2, 3),
]

# Common opposites dictionary for expansion
COMMON_OPPOSITES: dict[str, str] = {
    "hot": "cold",
    "cold": "hot",
    "fast": "slow",
    "slow": "fast",
    "big": "small",
    "small": "big",
    "hard": "soft",
    "soft": "hard",
    "heavy": "light",
    "light": "heavy",
    "thick": "thin",
    "thin": "thick",
    "long": "short",
    "short": "long",
    "wide": "narrow",
    "narrow": "wide",
    "strong": "weak",
    "weak": "strong",
    "transparent": "opaque",
    "opaque": "transparent",
    "rigid": "flexible",
    "flexible": "rigid",
    "smooth": "rough",
    "rough": "smooth",
    "visible": "invisible",
    "invisible": "visible",
    "conductive": "insulating",
    "insulating": "conductive",
    "porous": "dense",
    "dense": "porous",
    "magnetic": "non-magnetic",
    "wet": "dry",
    "dry": "wet",
    "open": "closed",
    "closed": "open",
    "sharp": "blunt",
    "blunt": "sharp",
}


# =============================================================================
# SEPARATION STRATEGIES DATABASE
# =============================================================================

SEPARATION_STRATEGIES: dict[SeparationType, SeparationStrategy] = {
    SeparationType.IN_TIME: SeparationStrategy(
        separation_type=SeparationType.IN_TIME,
        description=(
            "Resolve the contradiction by making the object possess the property "
            "at one time and the opposite property at another time. "
            "The object alternates between states."
        ),
        c4_shift="time_shift",
        c4_trajectory=[
            (0, 0, 0),  # Past, Concrete, Self  (O0)
            (1, 0, 0),  # Present, Concrete, Self
            (2, 0, 0),  # Future, Concrete, Self  (time shift)
            (1, 0, 0),  # Back to Present
        ],
        examples=[
            "Folding umbrella: compact when closed, large when open.",
            "Shape-memory alloy: deformed at low temp, original shape at high temp.",
            "Night-vision goggles: infrared at night, normal vision during day.",
            "Chameleon color: green on leaves, brown on tree bark.",
            "Traffic lights: red (stop), green (go) in time sequence.",
        ],
    ),
    SeparationType.IN_SPACE: SeparationStrategy(
        separation_type=SeparationType.IN_SPACE,
        description=(
            "Resolve the contradiction by making the object possess the property "
            "in one location and the opposite property in another location. "
            "Different parts of the system have different properties."
        ),
        c4_shift="scale_shift",
        c4_trajectory=[
            (1, 0, 0),  # Present, Concrete, Self  (O0)
            (1, 1, 0),  # Present, Abstract, Self
            (1, 2, 0),  # Present, Meta, Self  (scale shift)
            (1, 1, 0),  # Back to Abstract
        ],
        examples=[
            "Multi-layer windshield: rigid outer glass, soft inner film.",
            "Functionally graded materials: ceramic on hot side, metal on cold side.",
            "Ergonomic knife: sharp blade, soft handle.",
            "Gradient-index lens: varying refractive index from center to edge.",
            "Thermal protection tile: hot outer surface, cool inner structure.",
        ],
    ),
    SeparationType.PARTS_WHOLE: SeparationStrategy(
        separation_type=SeparationType.PARTS_WHOLE,
        description=(
            "Resolve the contradiction by making the object as a whole possess "
            "one property while its parts possess the opposite property. "
            "The system and its components have contradictory properties."
        ),
        c4_shift="agency_shift",
        c4_trajectory=[
            (1, 0, 0),  # Present, Concrete, Self  (O0)
            (1, 0, 1),  # Present, Concrete, Other
            (1, 0, 2),  # Present, Concrete, System  (agency shift)
            (1, 0, 1),  # Back to Other
        ],
        examples=[
            "Chain: rigid as a whole (cannot stretch), flexible in links (can bend).",
            "Bicycle wheel: rigid overall structure, flexible spokes.",
            "Water as a wave: whole wave moves forward, water particles oscillate in place.",
            "Team: individual members have different skills, team acts unified.",
            "Mesh structure: solid as a sheet, porous as individual holes.",
        ],
    ),
    SeparationType.UNDER_CONDITIONS: SeparationStrategy(
        separation_type=SeparationType.UNDER_CONDITIONS,
        description=(
            "Resolve the contradiction by making the object possess the property "
            "under one set of conditions and the opposite property under another set. "
            "Conditions (temperature, pressure, field, etc.) determine which property dominates."
        ),
        c4_shift="combined_shift",
        c4_trajectory=[
            (1, 0, 0),  # Present, Concrete, Self  (O0)
            (2, 1, 1),  # Future, Abstract, Other  (combined multi-axis shift)
            (0, 2, 2),  # Past, Meta, System
            (1, 1, 1),  # Balanced state
        ],
        examples=[
            "Thermochromic paint: red when hot, blue when cold.",
            "Non-Newtonian fluid: liquid under low shear, solid under high shear.",
            "Piezoelectric crystal: insulator at rest, conductor under pressure.",
            "Superconductor: resistive above critical temp, zero resistance below.",
            "Photochromic lenses: transparent indoors, dark in sunlight.",
        ],
    ),
}


# =============================================================================
# PHYSICAL CONTRADICTION ANALYZER
# =============================================================================

class PhysicalContradictionAnalyzer:
    """
    Detects physical contradictions in text and resolves them using
    the four separation principles, mapped to C4 state transitions.
    """

    def __init__(self) -> None:
        self.patterns = PHYSICAL_CONTRADICTION_PATTERNS
        self.opposites = COMMON_OPPOSITES
        self.strategies = SEPARATION_STRATEGIES

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect(self, text: str) -> list[PhysicalContradiction]:
        """
        Scan *text* for physical contradiction patterns.
        Returns a list of zero or more PhysicalContradiction instances.
        """
        found: list[PhysicalContradiction] = []
        seen: set[str] = set()

        for pattern, obj_grp, prop_grp, opp_grp in self.patterns:
            for match in pattern.finditer(text):
                obj = match.group(obj_grp).strip()
                # Strip leading articles
                obj_lower = obj.lower()
                for article in ("the ", "a ", "an "):
                    if obj_lower.startswith(article):
                        obj = obj[len(article):]
                        break
                prop = match.group(prop_grp).strip().lower()
                opp = match.group(opp_grp).strip().lower()
                key = f"{obj}:{prop}:{opp}"
                if key in seen:
                    continue
                seen.add(key)
                found.append(PhysicalContradiction(
                    object_name=obj,
                    property=prop,
                    opposite=opp,
                    context=text[:200],
                ))

        # Fallback: look for known opposite pairs in close proximity
        found.extend(self._detect_by_opposites(text, seen))
        return found

    def _detect_by_opposites(
        self, text: str, already_seen: set[str]
    ) -> list[PhysicalContradiction]:
        """
        Heuristic: if a sentence contains both words of an opposite pair,
        treat it as a potential physical contradiction.
        """
        found: list[PhysicalContradiction] = []
        sentences = re.split(r'[.!?;]+', text)

        # Check each sentence individually
        for sent in sentences:
            sent_lower = sent.lower()
            for word, opposite in self.opposites.items():
                if word in sent_lower and opposite in sent_lower:
                    obj = self._extract_object(sent, word, opposite)
                    key = f"{obj}:{word}:{opposite}"
                    if key not in already_seen:
                        already_seen.add(key)
                        found.append(PhysicalContradiction(
                            object_name=obj,
                            property=word,
                            opposite=opposite,
                            context=sent.strip(),
                        ))

        # Also check the full text (for opposites spread across sentences)
        text_lower = text.lower()
        for word, opposite in self.opposites.items():
            if word in text_lower and opposite in text_lower:
                key = f"the system:{word}:{opposite}"
                if key not in already_seen:
                    already_seen.add(key)
                    found.append(PhysicalContradiction(
                        object_name="the system",
                        property=word,
                        opposite=opposite,
                        context=text[:200],
                    ))

        return found

    def _extract_object(self, sentence: str, word1: str, word2: str) -> str:
        """Crude noun-phrase extraction for the object causing the contradiction."""
        # Find earliest occurrence of either word
        idx1 = sentence.lower().find(word1)
        idx2 = sentence.lower().find(word2)
        earliest = min(i for i in (idx1, idx2) if i >= 0)
        prefix = sentence[:earliest]
        # Take last 2-4 words as object
        words = prefix.strip().split()
        if len(words) >= 2:
            return " ".join(words[-3:])
        return "the system"

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        contradiction: PhysicalContradiction,
        strategy_hint: SeparationType | None = None,
    ) -> dict[str, Any]:
        """
        Given a physical contradiction, recommend the best separation
        principle(s) and map to C4 cognitive trajectories.
        """
        candidates = self._rank_strategies(contradiction)
        if strategy_hint:
            candidates = [c for c in candidates if c[0] == strategy_hint] or candidates

        recommendations = []
        for sep_type, score, reason in candidates:
            strat = self.strategies[sep_type]
            recommendations.append({
                "separation_type": sep_type.name,
                "score": round(score, 3),
                "reason": reason,
                "strategy": strat.to_dict(),
            })

        return {
            "contradiction": contradiction.to_dict(),
            "recommendations": recommendations,
            "best_strategy": recommendations[0] if recommendations else None,
        }

    def _rank_strategies(
        self, pc: PhysicalContradiction
    ) -> list[tuple[SeparationType, float, str]]:
        """
        Rank the four separation strategies by relevance to the contradiction.
        Returns list of (SeparationType, score, reason) sorted by score desc.
        """
        prop = pc.property.lower()
        opp = pc.opposite.lower()
        scores: list[tuple[SeparationType, float, str]] = []

        # Keyword-based heuristics
        time_keywords = {"fast", "slow", "before", "after", "during", "when",
                         "temporal", "simultaneous", "sequence", "periodic"}
        space_keywords = {"big", "small", "long", "short", "wide", "narrow",
                          "thick", "thin", "location", "position", "area", "volume"}
        conditions_keywords = {"temperature", "pressure", "field", "light",
                               "heat", "magnetic", "electric", "stress", "strain"}
        parts_keywords = {"rigid", "flexible", "strong", "weak", "hard", "soft",
                          "structure", "material", "component", "assembly"}

        prop_set = {prop, opp}

        # Time score
        time_score = 0.5
        if prop_set & time_keywords:
            time_score += 0.4
        if "time" in pc.context.lower():
            time_score += 0.2
        scores.append((SeparationType.IN_TIME, min(time_score, 1.0),
                       "Contradiction involves temporal or speed properties."))

        # Space score
        space_score = 0.5
        if prop_set & space_keywords:
            space_score += 0.4
        if "space" in pc.context.lower() or "location" in pc.context.lower():
            space_score += 0.2
        scores.append((SeparationType.IN_SPACE, min(space_score, 1.0),
                       "Contradiction involves spatial or size properties."))

        # Conditions score
        cond_score = 0.5
        if prop_set & conditions_keywords:
            cond_score += 0.4
        if any(k in pc.context.lower() for k in conditions_keywords):
            cond_score += 0.2
        scores.append((SeparationType.UNDER_CONDITIONS, min(cond_score, 1.0),
                       "Contradiction may be resolved by changing external conditions."))

        # Parts/Whole score
        parts_score = 0.5
        if prop_set & parts_keywords:
            parts_score += 0.4
        if "part" in pc.context.lower() or "whole" in pc.context.lower():
            parts_score += 0.2
        scores.append((SeparationType.PARTS_WHOLE, min(parts_score, 1.0),
                       "Contradiction may be resolved at different system levels."))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    # ------------------------------------------------------------------
    # C4 Integration
    # ------------------------------------------------------------------

    def map_to_c4_transition(
        self, contradiction: PhysicalContradiction, strategy: SeparationType
    ) -> dict[str, Any]:
        """
        Map the resolution of a physical contradiction to a C4 state transition.
        """
        strat = self.strategies[strategy]
        c4_states = [C4State(T=t, S=s, A=a) for t, s, a in strat.c4_trajectory]
        return {
            "contradiction": str(contradiction),
            "separation_type": strategy.name,
            "c4_shift": strat.c4_shift,
            "c4_trajectory": [str(s) for s in c4_states],
            "c4_coordinates": [s.to_tuple() for s in c4_states],
            "observer_transition": self._observer_transition_label(c4_states),
        }

    def _observer_transition_label(self, states: list[C4State]) -> str:
        """Label the observer state transition (O0 -> O1 -> O2)."""
        if not states:
            return "unknown"
        start = states[0]
        end = states[-1]
        # Simple heuristic based on distance
        dist = start.hamming_distance(end)
        if dist == 0:
            return "O0 (no change)"
        elif dist == 1:
            return "O0->O1 (single-axis shift)"
        elif dist == 2:
            return "O1->O2 (double-axis shift)"
        else:
            return "O2 (maximal shift)"

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------

    def analyze_text(self, text: str) -> dict[str, Any]:
        """
        Full pipeline: detect contradictions, resolve each, and return
        a structured report.
        """
        contradictions = self.detect(text)
        resolutions = [self.resolve(c) for c in contradictions]
        return {
            "input_preview": text[:120],
            "contradictions_found": len(contradictions),
            "contradictions": [c.to_dict() for c in contradictions],
            "resolutions": resolutions,
        }


# =============================================================================
# CLASSIC EXAMPLES DATABASE
# =============================================================================

CLASSIC_PHYSICAL_CONTRADICTIONS: list[dict[str, str]] = [
    {
        "object": "coffee cup",
        "property": "hot",
        "opposite": "cold",
        "context": "The coffee cup must be hot to keep coffee warm but cold to avoid burning hands.",
    },
    {
        "object": "airplane wing",
        "property": "large",
        "opposite": "small",
        "context": "The wing must be large for takeoff/landing lift but small for low cruise drag.",
    },
    {
        "object": "knife blade",
        "property": "sharp",
        "opposite": "blunt",
        "context": "The blade must be sharp to cut but blunt to avoid injury.",
    },
    {
        "object": "door",
        "property": "open",
        "opposite": "closed",
        "context": "The door must be open for ventilation but closed for security.",
    },
    {
        "object": "spring",
        "property": "rigid",
        "opposite": "flexible",
        "context": "The spring must be rigid to support load but flexible to absorb shock.",
    },
    {
        "object": "information",
        "property": "visible",
        "opposite": "invisible",
        "context": "The information must be visible to authorized users but invisible to attackers.",
    },
    {
        "object": "vehicle",
        "property": "fast",
        "opposite": "slow",
        "context": "The vehicle must be fast for emergency response but slow for safety in crowds.",
    },
    {
        "object": "container",
        "property": "porous",
        "opposite": "dense",
        "context": "The container must be porous to breathe but dense to hold liquid.",
    },
    {
        "object": "diving suit",
        "property": "thick",
        "opposite": "thin",
        "context": "The diving suit must be thick for thermal insulation but thin for flexibility.",
    },
    {
        "object": "tire",
        "property": "wide",
        "opposite": "narrow",
        "context": "The tire must be wide for traction but narrow for low rolling resistance.",
    },
]


def get_classic_examples() -> list[PhysicalContradiction]:
    """Return the 10 classic physical contradictions as typed objects."""
    return [
        PhysicalContradiction(
            object_name=e["object"],
            property=e["property"],
            opposite=e["opposite"],
            context=e["context"],
        )
        for e in CLASSIC_PHYSICAL_CONTRADICTIONS
    ]


def detect_physical_contradiction(text: str) -> list[PhysicalContradiction]:
    """Convenience function: detect contradictions in text."""
    return PhysicalContradictionAnalyzer().detect(text)


def resolve_physical_contradiction(
    contradiction: PhysicalContradiction,
    strategy_hint: SeparationType | None = None,
) -> dict[str, Any]:
    """Convenience function: resolve a single contradiction."""
    return PhysicalContradictionAnalyzer().resolve(contradiction, strategy_hint)
