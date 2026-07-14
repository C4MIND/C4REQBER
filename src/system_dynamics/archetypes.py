"""
System Archetypes — pre-defined Senge patterns and archetype detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

from .causal_loop import CausalLoopDiagram, Polarity
from .stock_flow import CompiledSystem, SystemSpec


# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------


@dataclass
class Archetype:
    """A named system archetype with a builder function and CLD signature."""

    name: str
    description: str
    build: Callable[..., SystemSpec]
    signature_nodes: list[str]
    signature_links: list[tuple[str, str, Polarity]]


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


def _sigmoid(x: float, k: float = 1.0, x0: float = 0.0) -> float:
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ---------------------------------------------------------------------------
# 1. Limits to Growth
# ---------------------------------------------------------------------------


def build_limits_to_growth(
    initial_growth: float = 1.0,
    limit: float = 100.0,
    growth_rate: float = 0.05,
    resistance_strength: float = 0.02,
) -> SystemSpec:
    """Growth is slowed by an approaching limit."""
    spec = SystemSpec("limits_to_growth")
    spec.add_stock("performance", initial_growth, unit="units")
    spec.add_stock("limiting_factor", 0.0, unit="units")
    spec.add_flow(
        "growth_effort",
        lambda performance, limiting_factor: growth_rate * performance * (1 - limiting_factor / limit) if limiting_factor < limit else 0.0,
        source=None,
        sink="performance",
    )
    spec.add_flow(
        "resistance",
        lambda performance, limiting_factor: resistance_strength * performance * limiting_factor / limit,
        source="performance",
        sink="limiting_factor",
    )
    spec.add_auxiliary(
        "remaining_capacity",
        lambda performance, limiting_factor: limit - limiting_factor,
    )
    return spec


LIMITS_TO_GROWTH = Archetype(
    name="Limits to Growth",
    description="Growth is slowed by an approaching limit.",
    build=build_limits_to_growth,
    signature_nodes=["performance", "limiting_factor", "growth_effort", "resistance"],
    signature_links=[
        ("growth_effort", "performance", Polarity.POSITIVE),
        ("performance", "resistance", Polarity.POSITIVE),
        ("resistance", "limiting_factor", Polarity.POSITIVE),
        ("limiting_factor", "growth_effort", Polarity.NEGATIVE),
    ],
)


# ---------------------------------------------------------------------------
# 2. Shifting the Burden
# ---------------------------------------------------------------------------


def build_shifting_the_burden(
    initial_problem: float = 50.0,
    fix_rate: float = 0.1,
    fundamental_rate: float = 0.02,
    side_effect_rate: float = 0.03,
) -> SystemSpec:
    """Symptomatic fixes erode fundamental solutions."""
    spec = SystemSpec("shifting_the_burden")
    spec.add_stock("problem_symptom", initial_problem)
    spec.add_stock("fundamental_solution", 20.0)
    spec.add_stock("side_effect", 0.0)
    spec.add_flow(
        "symptomatic_fix",
        lambda problem_symptom, fundamental_solution, side_effect: fix_rate * problem_symptom * (1 - _clip(side_effect / 100.0, 0.0, 1.0)),
        source="problem_symptom",
        sink=None,
    )
    spec.add_flow(
        "fundamental_fix",
        lambda problem_symptom, fundamental_solution, side_effect: fundamental_rate * fundamental_solution,
        source="problem_symptom",
        sink=None,
    )
    spec.add_flow(
        "side_effect_growth",
        lambda problem_symptom, fundamental_solution, side_effect: side_effect_rate * problem_symptom,
        source=None,
        sink="side_effect",
    )
    spec.add_flow(
        "solution_atrophy",
        lambda problem_symptom, fundamental_solution, side_effect: 0.01 * fundamental_solution,
        source="fundamental_solution",
        sink=None,
    )
    return spec


SHIFTING_THE_BURDEN = Archetype(
    name="Shifting the Burden",
    description="Symptomatic fixes erode fundamental solutions.",
    build=build_shifting_the_burden,
    signature_nodes=["problem_symptom", "fundamental_solution", "side_effect"],
    signature_links=[
        ("problem_symptom", "symptomatic_fix", Polarity.POSITIVE),
        ("symptomatic_fix", "problem_symptom", Polarity.NEGATIVE),
        ("symptomatic_fix", "side_effect", Polarity.POSITIVE),
        ("side_effect", "fundamental_solution", Polarity.NEGATIVE),
        ("fundamental_solution", "fundamental_fix", Polarity.POSITIVE),
        ("fundamental_fix", "problem_symptom", Polarity.NEGATIVE),
    ],
)


# ---------------------------------------------------------------------------
# 3. Tragedy of the Commons
# ---------------------------------------------------------------------------


def build_tragedy_of_the_commons(
    initial_resource: float = 1000.0,
    num_users: int = 10,
    individual_use_rate: float = 0.5,
    regeneration_rate: float = 0.1,
) -> SystemSpec:
    """Individual incentives deplete a shared resource."""
    spec = SystemSpec("tragedy_of_the_commons")
    spec.add_stock("shared_resource", initial_resource, min_value=0.0)
    spec.add_stock("total_benefit", 0.0)
    spec.add_flow(
        "individual_use",
        lambda shared_resource, total_benefit: individual_use_rate * num_users * (shared_resource / (shared_resource + 100.0)),
        source="shared_resource",
        sink=None,
    )
    spec.add_flow(
        "regeneration",
        lambda shared_resource, total_benefit: regeneration_rate * shared_resource * (1 - shared_resource / 2000.0) if shared_resource > 0 else 0.0,
        source=None,
        sink="shared_resource",
    )
    spec.add_flow(
        "benefit_accumulation",
        lambda shared_resource, total_benefit: individual_use_rate * num_users * (shared_resource / (shared_resource + 100.0)),
        source=None,
        sink="total_benefit",
    )
    return spec


TRAGEDY_OF_THE_COMMONS = Archetype(
    name="Tragedy of the Commons",
    description="Individual incentives deplete a shared resource.",
    build=build_tragedy_of_the_commons,
    signature_nodes=["shared_resource", "total_benefit", "individual_use"],
    signature_links=[
        ("shared_resource", "individual_use", Polarity.POSITIVE),
        ("individual_use", "total_benefit", Polarity.POSITIVE),
        ("individual_use", "shared_resource", Polarity.NEGATIVE),
        ("shared_resource", "regeneration", Polarity.POSITIVE),
    ],
)


# ---------------------------------------------------------------------------
# 4. Escalation
# ---------------------------------------------------------------------------


def build_escalation(
    a_initial: float = 50.0,
    b_initial: float = 50.0,
    threat_perception: float = 0.1,
    decay: float = 0.05,
) -> SystemSpec:
    """Two parties escalate in response to each other."""
    spec = SystemSpec("escalation")
    spec.add_stock("party_a", a_initial)
    spec.add_stock("party_b", b_initial)
    spec.add_flow(
        "a_escalation",
        lambda party_a, party_b: threat_perception * party_b - decay * party_a,
        source=None,
        sink="party_a",
    )
    spec.add_flow(
        "b_escalation",
        lambda party_a, party_b: threat_perception * party_a - decay * party_b,
        source=None,
        sink="party_b",
    )
    return spec


ESCALATION = Archetype(
    name="Escalation",
    description="Two parties escalate in response to each other.",
    build=build_escalation,
    signature_nodes=["party_a", "party_b"],
    signature_links=[
        ("party_a", "b_escalation", Polarity.POSITIVE),
        ("b_escalation", "party_b", Polarity.POSITIVE),
        ("party_b", "a_escalation", Polarity.POSITIVE),
        ("a_escalation", "party_a", Polarity.POSITIVE),
    ],
)


# ---------------------------------------------------------------------------
# 5. Fixes that Fail
# ---------------------------------------------------------------------------


def build_fixes_that_fail(
    initial_problem: float = 100.0,
    fix_strength: float = 0.2,
    unintended_strength: float = 0.05,
    delay: float = 5.0,
) -> SystemSpec:
    """Quick fixes create delayed unintended consequences."""
    spec = SystemSpec("fixes_that_fail")
    spec.add_stock("problem", initial_problem)
    spec.add_stock("unintended_consequence", 0.0)
    spec.add_flow(
        "quick_fix",
        lambda problem, unintended_consequence: fix_strength * problem,
        source="problem",
        sink=None,
    )
    spec.add_flow(
        "delayed_side_effect",
        lambda problem, unintended_consequence: unintended_strength * problem,
        source=None,
        sink="unintended_consequence",
    )
    spec.add_flow(
        "consequence_backlash",
        lambda problem, unintended_consequence: 0.03 * unintended_consequence,
        source=None,
        sink="problem",
    )
    return spec


FIXES_THAT_FAIL = Archetype(
    name="Fixes that Fail",
    description="Quick fixes create delayed unintended consequences.",
    build=build_fixes_that_fail,
    signature_nodes=["problem", "unintended_consequence", "quick_fix"],
    signature_links=[
        ("problem", "quick_fix", Polarity.POSITIVE),
        ("quick_fix", "problem", Polarity.NEGATIVE),
        ("quick_fix", "unintended_consequence", Polarity.POSITIVE),
        ("unintended_consequence", "problem", Polarity.POSITIVE),
    ],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ARCHETYPES: list[Archetype] = [
    LIMITS_TO_GROWTH,
    SHIFTING_THE_BURDEN,
    TRAGEDY_OF_THE_COMMONS,
    ESCALATION,
    FIXES_THAT_FAIL,
]

ARCHETYPE_BY_NAME: dict[str, Archetype] = {a.name: a for a in ARCHETYPES}


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


def model_to_cld(spec: SystemSpec) -> CausalLoopDiagram:
    """Heuristic conversion of a SystemSpec to a CLD for pattern matching."""
    cld = CausalLoopDiagram(spec.name)
    for s in spec.stocks.values():
        cld.add_node(s.name, category="stock")
    for a in spec.auxiliaries.values():
        cld.add_node(a.name, category="auxiliary")
    for fl in spec.flows.values():
        # add flow as a node so it can be a link source/target
        if fl.name not in cld.nodes:
            cld.add_node(fl.name, category="flow")
        if fl.source and fl.sink:
            cld.add_link(fl.source, fl.name, Polarity.POSITIVE)
            cld.add_link(fl.name, fl.sink, Polarity.POSITIVE)
        elif fl.source:
            # outflow reduces source
            cld.add_link(fl.source, fl.name, Polarity.POSITIVE)
            cld.add_link(fl.name, fl.source, Polarity.NEGATIVE)
        elif fl.sink:
            # inflow increases sink
            cld.add_link(fl.name, fl.sink, Polarity.POSITIVE)
    return cld


def _subgraph_match(
    cld: CausalLoopDiagram,
    signature_nodes: list[str],
    signature_links: list[tuple[str, str, Polarity]],
) -> float:
    """Return a match score in [0, 1] based on node and link overlap."""
    node_set = set(cld.nodes.keys())
    sig_node_set = set(signature_nodes)
    node_overlap = len(node_set & sig_node_set) / max(len(sig_node_set), 1)

    cld_links = {(l.source, l.target, l.polarity) for l in cld.links}
    sig_links = set(signature_links)
    link_overlap = len(cld_links & sig_links) / max(len(sig_links), 1)

    return 0.5 * node_overlap + 0.5 * link_overlap


def detect_archetype(spec: SystemSpec) -> list[tuple[str, float]]:
    """Score every known archetype against *spec* and return sorted results."""
    cld = model_to_cld(spec)
    scores = [
        (arch.name, _subgraph_match(cld, arch.signature_nodes, arch.signature_links))
        for arch in ARCHETYPES
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def best_archetype_match(spec: SystemSpec, threshold: float = 0.5) -> tuple[str, float] | None:
    """Return the highest-scoring archetype if it exceeds *threshold*."""
    scores = detect_archetype(spec)
    if scores and scores[0][1] >= threshold:
        return scores[0]
    return None


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------


def simulate_archetype(
    archetype_name: str,
    t_span: tuple[float, float] = (0.0, 100.0),
    n_steps: int = 2000,
    **kwargs: Any,
) -> tuple[NDArray[np.float64], NDArray[np.float64], SystemSpec]:
    """Build, compile and run a named archetype.

    Returns (t, y, spec).
    """
    from .stock_flow import rk4_integrate

    arch = ARCHETYPE_BY_NAME[archetype_name]
    spec = arch.build(**kwargs)
    compiled = CompiledSystem(spec)
    t, y = rk4_integrate(compiled, t_span, n_steps=n_steps)
    return t, y, spec


# ---------------------------------------------------------------------------
# __init__ exports
# ---------------------------------------------------------------------------

__all__ = [
    "Archetype",
    "ARCHETYPES",
    "ARCHETYPE_BY_NAME",
    "LIMITS_TO_GROWTH",
    "SHIFTING_THE_BURDEN",
    "TRAGEDY_OF_THE_COMMONS",
    "ESCALATION",
    "FIXES_THAT_FAIL",
    "build_limits_to_growth",
    "build_shifting_the_burden",
    "build_tragedy_of_the_commons",
    "build_escalation",
    "build_fixes_that_fail",
    "model_to_cld",
    "detect_archetype",
    "best_archetype_match",
    "simulate_archetype",
]
