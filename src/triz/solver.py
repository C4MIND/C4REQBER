"""
TRIZ Solver - Auto-suggest engine for inventive principles.
Based on the classical TRIZ methodology.
"""

import re
from dataclasses import dataclass

from .matrix import (
    PARAMETERS,
    count_cells,
    get_parameter_name,
    get_recommended_principles,
)
from .principles import Principle, get_principle


@dataclass
class SuggestedPrinciple:
    """A suggested principle with explanation and relevance score."""
    number: int
    name: str
    description: str
    explanation: str
    relevance_score: float  # 0.0 to 1.0
    examples: list[str]


@dataclass
class SolverResult:
    """Result from the TRIZ solver."""
    improving_param_id: int
    improving_param_name: str
    worsening_param_id: int
    worsening_param_name: str
    principles: list[SuggestedPrinciple]


# =============================================================================
# NLP PARAMETER EXTRACTION
# =============================================================================

# Keywords mapped to parameter IDs for NLP extraction
PARAMETER_KEYWORDS: dict[int, list[str]] = {
    1: ["weight", "mass", "heavy", "light", "heavier", "lighter", "weigh", "kg", "pounds", "grams", "ton"],
    2: ["weight", "mass", "heavy", "light", "stationary weight", "fixed weight"],
    3: ["length", "long", "short", "elongate", "extend", "shrink", "size", "dimension", "longer", "shorter"],
    4: ["length", "long", "short", "stationary length", "fixed length"],
    5: ["area", "surface", "wide", "narrow", "broad", "surface area", "footprint", "coverage"],
    6: ["area", "surface", "stationary area", "fixed area"],
    7: ["volume", "space", "compact", "bulky", "capacity", "cubic", "liters", "gallons"],
    8: ["volume", "space", "stationary volume", "fixed volume"],
    9: ["speed", "fast", "slow", "velocity", "quick", "rapid", "accelerate", "decelerate", "faster", "slower", "time"],
    10: ["force", "strength", "powerful", "weak", "load", "stress", "pressure", "torque", "thrust"],
    11: ["pressure", "tension", "stress", "compression", "psi", "bar", "atmospheric", "hydraulic"],
    12: ["shape", "form", "geometry", "contour", "profile", "configuration", "morphology"],
    13: ["stability", "stable", "unstable", "balance", "equilibrium", "steady", "wobble", "vibration", "oscillation"],
    14: ["strength", "strong", "weak", "durability", "tough", "fragile", "robust", "resilience", "sturdy"],
    15: ["durability", "wear", "fatigue", "lifespan", "moving durability", "moving wear"],
    16: ["durability", "wear", "fatigue", "lifespan", "stationary durability", "stationary wear"],
    17: ["temperature", "heat", "cold", "hot", "warm", "thermal", "cooling", "heating", "freeze", "melt"],
    18: ["brightness", "light", "dark", "illumination", "luminosity", "visible", "glow", "dim", "bright"],
    19: ["energy", "power consumption", "efficiency", "moving energy", "fuel", "battery", "electricity", "consumption"],
    20: ["energy", "power consumption", "stationary energy", "idle energy", "standby power"],
    21: ["power", "output", "horsepower", "wattage", "capacity", "performance", "throughput"],
    22: ["waste energy", "heat loss", "energy loss", "inefficiency", "dissipation", "friction loss"],
    23: ["waste substance", "material loss", "scrap", "emission", "pollution", "byproduct", "waste material"],
    24: ["information", "data loss", "signal", "noise", "communication", "measurement error", "uncertainty"],
    25: ["time", "duration", "delay", "waiting", "slow process", "bottleneck", "lead time", "cycle time"],
    26: ["amount", "quantity", "material", "substance", "mass", "volume of material", "consumption"],
    27: ["reliability", "dependable", "failure", "breakdown", "malfunction", "uptime", "consistent", "trustworthy"],
    28: ["accuracy", "precision", "measurement", "exact", "approximate", "tolerance", "error", "resolution"],
    29: ["manufacturing accuracy", "tolerance", "machining", "fabrication", "production precision", "assembly"],
    30: ["harmful factor", "danger", "hazard", "risk", "toxic", "radiation", "corrosion", "damage", "harm"],
    31: ["side effect", "unintended", "consequence", "collateral", "secondary effect", "byproduct harm"],
    32: ["manufacturability", "production", "fabrication", "assembly", "build", "make", "construct", "process"],
    33: ["usability", "convenience", "user friendly", "ergonomic", "comfort", "ease of use", "intuitive", "accessible"],
    34: ["repair", "maintenance", "service", "fix", "replace", "overhaul", "servicing", "upkeep"],
    35: ["adaptability", "flexible", "versatile", "adjustable", "customizable", "modular", "reconfigurable"],
    36: ["complexity", "complicated", "sophisticated", "intricate", "simple", "device complexity"],
    37: ["control complexity", "difficult to control", "automation difficulty", "regulation", "monitoring"],
    38: ["automation", "automatic", "robotic", "self-operating", "unattended", "autonomous", "manual"],
    39: ["productivity", "efficiency", "throughput", "output", "yield", "performance", "capacity utilization"],
}


def extract_parameters_from_text(text: str) -> tuple[int | None, int | None]:
    """
    Extract improving and worsening parameters from natural language problem description.

    Looks for patterns like:
    - "improve X but Y gets worse"
    - "want more X but less Y"
    - "increase X without increasing Y"
    - "better X but worse Y"

    Returns:
        Tuple of (improving_param_id, worsening_param_id) or (None, None) if not found
    """
    text_lower = text.lower()

    # Try to find explicit contradiction patterns
    contradiction_patterns = [
        # "improve A but B worsens"
        r"(?:improve|increase|enhance|better|more|higher|faster|stronger)\s+(\w+(?:\s+\w+){0,3})\s+(?:but|however|yet|though|although)\s+(\w+(?:\s+\w+){0,3})\s+(?:worsen|worse|decrease|reduce|less|lower|weaker|suffer)",
        # "A improves but B suffers"
        r"(\w+(?:\s+\w+){0,3})\s+(?:improves|increases|gets better)\s+(?:but|however)\s+(\w+(?:\s+\w+){0,3})\s+(?:worsens|decreases|gets worse|suffers)",
        # "more A but less B"
        r"(?:more|higher|greater)\s+(\w+(?:\s+\w+){0,3})\s+(?:but|and)\s+(?:less|lower|fewer)\s+(\w+(?:\s+\w+){0,3})",
        # "increase A without increasing B"
        r"(?:increase|improve|enhance)\s+(\w+(?:\s+\w+){0,3})\s+(?:without|while not|but not)\s+(?:increasing|worsening|degrading)\s+(\w+(?:\s+\w+){0,3})",
    ]

    for pattern in contradiction_patterns:
        match = re.search(pattern, text_lower)
        if match:
            improving_text = match.group(1)
            worsening_text = match.group(2)

            improving_id = _match_parameter(improving_text)
            worsening_id = _match_parameter(worsening_text)

            if improving_id and worsening_id:
                return improving_id, worsening_id

    # Fallback: score all parameters by keyword frequency
    return _score_parameters_by_keywords(text_lower)


def _match_parameter(text: str) -> int | None:
    """Match text to a parameter ID using keywords."""
    text_lower = text.lower().strip()

    # Direct match
    for pid, keywords in PARAMETER_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return pid

    return None


def _score_parameters_by_keywords(text: str) -> tuple[int | None, int | None]:
    """Score parameters by keyword frequency and return top two."""
    scores: dict[int, int] = {}

    for pid, keywords in PARAMETER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # Count occurrences, with bonus for whole word matches
            count = len(re.findall(r'\b' + re.escape(kw) + r'\b', text))
            if count > 0:
                score += count * 2
            else:
                # Partial match (substring)
                if kw in text:
                    score += 1
        scores[pid] = score

    # Sort by score descending
    sorted_params = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if len(sorted_params) >= 2 and sorted_params[0][1] > 0 and sorted_params[1][1] > 0:
        return sorted_params[0][0], sorted_params[1][0]
    elif len(sorted_params) >= 1 and sorted_params[0][1] > 0:
        return sorted_params[0][0], None

    return None, None


# =============================================================================
# SOLVER ENGINE
# =============================================================================

def solve_contradiction(
    improving: int,
    worsening: int,
    problem_context: str | None = None,
) -> SolverResult:
    """
    Solve a TRIZ contradiction by finding recommended principles.

    Args:
        improving: ID of parameter to improve (1-39)
        worsening: ID of parameter that worsens (1-39)
        problem_context: Optional description of the problem for better explanations

    Returns:
        SolverResult with ranked principles and explanations
    """
    recommended = get_recommended_principles(improving, worsening)

    improving_name = get_parameter_name(improving)
    worsening_name = get_parameter_name(worsening)

    principles = []
    for i, principle_num in enumerate(recommended):
        principle = get_principle(principle_num)
        if principle:
            # Calculate relevance score (higher = more relevant)
            # First principles in the list are typically more relevant
            relevance = 1.0 - (i * 0.15)
            relevance = max(0.3, relevance)

            explanation = _generate_explanation(
                principle, improving_name, worsening_name, problem_context
            )

            principles.append(SuggestedPrinciple(
                number=principle.number,
                name=principle.name,
                description=principle.description,
                explanation=explanation,
                relevance_score=round(relevance, 2),
                examples=principle.examples[:3],  # Top 3 examples
            ))

    return SolverResult(
        improving_param_id=improving,
        improving_param_name=improving_name,
        worsening_param_id=worsening,
        worsening_param_name=worsening_name,
        principles=principles,
    )


def solve_from_text(problem_description: str) -> SolverResult | None:
    """
    Solve a TRIZ contradiction from natural language text.

    Args:
        problem_description: Natural language description of the problem

    Returns:
        SolverResult or None if parameters could not be extracted
    """
    improving, worsening = extract_parameters_from_text(problem_description)

    if improving is None or worsening is None:
        return None

    return solve_contradiction(improving, worsening, problem_description)


def _generate_explanation(
    principle: Principle,
    improving_name: str,
    worsening_name: str,
    problem_context: str | None = None,
) -> str:
    """Generate a contextual explanation for why this principle applies."""

    explanations = {
        1: f"Segment the system so that {improving_name} can be improved in parts without affecting {worsening_name} globally.",
        2: f"Extract the component causing {worsening_name} or isolate the part that needs {improving_name}.",
        3: f"Make different parts of the system handle {improving_name} and {worsening_name} separately.",
        4: f"Use asymmetry to improve {improving_name} without the symmetric constraints that cause {worsening_name}.",
        5: f"Merge functions so that improving {improving_name} simultaneously addresses {worsening_name}.",
        6: f"Make a single component serve multiple functions, improving {improving_name} while reducing {worsening_name}.",
        7: f"Nest components so that {improving_name} is achieved through compact arrangement without increasing {worsening_name}.",
        8: f"Use buoyancy, aerodynamics, or magnetic forces to improve {improving_name} without adding weight that causes {worsening_name}.",
        9: f"Pre-stress or pre-condition the system so that {worsening_name} is counteracted before it occurs while improving {improving_name}.",
        10: f"Prepare the system in advance so that {improving_name} is achieved without the time delay that causes {worsening_name}.",
        11: f"Add backup or cushioning systems to protect against {worsening_name} while pursuing {improving_name}.",
        12: f"Design the system so that changes in {improving_name} don't require positional changes that cause {worsening_name}.",
        13: f"Invert the approach: instead of directly improving {improving_name}, do the opposite to avoid {worsening_name}.",
        14: f"Use curved or spherical forms to improve {improving_name} through better force distribution, reducing {worsening_name}.",
        15: f"Make the system adaptive so that {improving_name} can vary dynamically without fixed states that cause {worsening_name}.",
        16: f"Apply slightly more or less than needed for {improving_name}, then adjust to avoid {worsening_name}.",
        17: f"Use additional dimensions or layers to improve {improving_name} without expanding in the dimension that causes {worsening_name}.",
        18: f"Introduce vibration or oscillation to improve {improving_name} through resonance or periodic effects, managing {worsening_name}.",
        19: f"Use periodic or pulsating action for {improving_name} so that intervals can recover from {worsening_name}.",
        20: f"Ensure continuous operation for {improving_name} without idle periods that accumulate {worsening_name}.",
        21: f"Perform the operation causing {worsening_name} at high speed to minimize its impact while achieving {improving_name}.",
        22: f"Turn the factor causing {worsening_name} into a resource that helps achieve {improving_name}.",
        23: f"Add feedback control so that {improving_name} is optimized automatically while monitoring {worsening_name}.",
        24: f"Use an intermediary material or process between the elements affecting {improving_name} and {worsening_name}.",
        25: f"Make the system self-serving: use waste from {worsening_name} to improve {improving_name}.",
        26: f"Use a copy or simulation to test {improving_name} without the real-world {worsening_name}.",
        27: f"Replace expensive components with multiple inexpensive ones to improve {improving_name} without cost-driven {worsening_name}.",
        28: f"Replace mechanical interaction with fields or sensors to improve {improving_name} while reducing {worsening_name}.",
        29: f"Use pneumatic or hydraulic systems to improve {improving_name} with fluid power that minimizes {worsening_name}.",
        30: f"Use thin films or membranes to improve {improving_name} through lightweight barriers that reduce {worsening_name}.",
        31: f"Make materials porous to improve {improving_name} through structural properties that absorb {worsening_name}.",
        32: f"Change colors or transparency to monitor {improving_name} visually without complex measurement causing {worsening_name}.",
        33: f"Use the same material throughout to improve {improving_name} through material compatibility, reducing {worsening_name}.",
        34: f"Make parts disposable or self-restoring so that {worsening_name} is eliminated while maintaining {improving_name}.",
        35: f"Change the physical state (temperature, concentration, flexibility) to improve {improving_name} while controlling {worsening_name}.",
        36: f"Use phase transitions to exploit volume or heat changes for {improving_name} while managing {worsening_name}.",
        37: f"Use thermal expansion properties to improve {improving_name} through temperature-controlled dimensional changes.",
        38: f"Use enriched oxygen or oxidizing environments to intensify processes for {improving_name} while controlling {worsening_name}.",
        39: f"Use inert atmosphere or vacuum to protect against {worsening_name} while optimizing for {improving_name}.",
        40: f"Use composite materials to combine properties that improve {improving_name} while resisting {worsening_name}.",
    }

    return explanations.get(principle.number,
        f"Apply principle '{principle.name}' to resolve the contradiction between {improving_name} and {worsening_name}.")


def list_all_parameters() -> list[tuple[int, str]]:
    """List all 39 engineering parameters."""
    return [(pid, name) for pid, name in PARAMETERS.items()]


def get_matrix_stats() -> dict[str, int]:
    """Get statistics about the contradiction matrix."""
    total_cells = 39 * 38  # 39x39 minus diagonal
    populated = count_cells()

    return {
        "total_possible_cells": total_cells,
        "populated_cells": populated,
        "parameters": 39,
        "principles": 40,
    }
