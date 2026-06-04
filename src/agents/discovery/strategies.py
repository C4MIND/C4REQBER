"""Hypothesis generation strategies for the Scientific Discovery Agent."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.validation import FalsifiabilityCriterion


if TYPE_CHECKING:
    from .core import AgentHypothesis, ScientificDiscoveryAgent


async def _generate_c4_triz(
    agent: ScientificDiscoveryAgent, problem: str, domains: list[str]
) -> list[AgentHypothesis]:
    """Generate hypotheses using C4+TRIZ methodology."""
    from .core import AgentHypothesis

    hypotheses = []

    # Try different contradiction formulations
    contradictions = [
        ("performance", "cost"),
        ("speed", "reliability"),
        ("features", "simplicity"),
    ]

    for improve, worsen in contradictions[:2]:
        solution = agent.triz.generate_c4_triz_path(problem, (improve, worsen))

        agent._hypothesis_counter += 1
        h = AgentHypothesis(
            id=f"h_c4_{agent._hypothesis_counter}",
            problem=problem,
            hypothesis=f"Solution via {improve} vs {worsen} optimization",
            mechanism=f"Apply C4 path: {' → '.join(solution['c4_path'])}",
            c4_path=solution["c4_path"],
            triz_principles=solution["triz_principles"],
            analogies=[],
            confidence=0.6
            + len(solution["c4_path"]) * 0.05,  # More steps = higher confidence
            falsifiability_criteria=[],
            estimated_validation_cost=0.0,
            estimated_time_to_validate="",
            domain=domains[0] if domains else "general",
            generation_method="c4_triz",
        )
        hypotheses.append(h)

    return hypotheses


async def _generate_analogies(
    agent: ScientificDiscoveryAgent, problem: str, domains: list[str]
) -> list[AgentHypothesis]:
    """Generate hypotheses via cross-domain analogies."""
    from .core import AgentHypothesis

    hypotheses = []

    # Try cross-domain mappings
    source_domains = domains
    target_domains = ["biology", "physics", "computer_science", "economics"]

    for source in source_domains:
        for target in target_domains:
            if source != target:
                # Find analogies between domains
                analogies = agent.analogy.discover_cross_domain_analogies(
                    source, target, max_analogies=3
                )

                for analogy in analogies[:1]:  # Top 1 per domain pair
                    agent._hypothesis_counter += 1
                    h = AgentHypothesis(
                        id=f"h_ana_{agent._hypothesis_counter}",
                        problem=problem,
                        hypothesis=f"Apply {analogy.source_concept} ({source}) → {analogy.target_concept} ({target})",
                        mechanism=f"Cross-domain analogy with confidence {analogy.confidence:.2f}",
                        c4_path=["sigma", "iota"],  # Abstraction + Integration
                        triz_principles=[
                            6,
                            24,
                            28,
                        ],  # Universality, Mediator, Mechanics Substitution
                        analogies=[analogy],
                        confidence=analogy.confidence,
                        falsifiability_criteria=[],
                        estimated_validation_cost=0.0,
                        estimated_time_to_validate="",
                        domain=source,
                        generation_method="analogy",
                    )
                    hypotheses.append(h)

    return hypotheses


async def _generate_hybrid(
    agent: ScientificDiscoveryAgent, existing: list[AgentHypothesis]
) -> list[AgentHypothesis]:
    """Generate hybrid hypotheses by combining existing ones."""
    from .core import AgentHypothesis

    if len(existing) < 2:
        return []

    hypotheses = []

    # Combine top C4 with top Analogy
    c4_h = next((h for h in existing if h.generation_method == "c4_triz"), None)
    ana_h = next((h for h in existing if h.generation_method == "analogy"), None)

    if c4_h and ana_h:
        agent._hypothesis_counter += 1
        h = AgentHypothesis(
            id=f"h_hyb_{agent._hypothesis_counter}",
            problem=c4_h.problem,
            hypothesis=f"Hybrid: {c4_h.hypothesis} + {ana_h.hypothesis}",
            mechanism=f"Combine C4 path with analogy from {ana_h.analogies[0].source_domain if ana_h.analogies else 'unknown'}",
            c4_path=c4_h.c4_path + ["iota"],  # Add integration step
            triz_principles=list(set(c4_h.triz_principles + ana_h.triz_principles)),
            analogies=ana_h.analogies,
            confidence=(c4_h.confidence + ana_h.confidence)
            / 2
            * 1.1,  # Boost for hybrid
            falsifiability_criteria=[],
            estimated_validation_cost=0.0,
            estimated_time_to_validate="",
            domain=c4_h.domain,
            generation_method="hybrid",
        )
        # Cap confidence at 0.95
        h.confidence = min(h.confidence, 0.95)
        hypotheses.append(h)

    return hypotheses


async def _generate_falsifiability(
    agent: ScientificDiscoveryAgent, hypothesis: AgentHypothesis
) -> list[FalsifiabilityCriterion]:
    """Generate falsifiability criteria for a hypothesis."""
    # Simplified - in real implementation would use LLM
    criteria = [
        FalsifiabilityCriterion(
            statement=f"If {hypothesis.domain} metric does not improve by 20%, hypothesis is false",
            measurement=f"Measure {hypothesis.domain} performance",
            threshold="20% improvement",
            difficulty="medium",
        ),
        FalsifiabilityCriterion(
            statement="If side effects exceed benefits, hypothesis is false",
            measurement="Measure side effects vs benefits",
            threshold="Side effects < 10% of benefits",
            difficulty="hard",
        ),
    ]
    return criteria


def _rank_hypotheses(
    hypotheses: list[AgentHypothesis],
) -> list[AgentHypothesis]:
    """Rank hypotheses by composite score."""

    def score(h: AgentHypothesis) -> float:
        # Composite: confidence * (1/cost) * speed_factor
        """Score."""
        cost_factor = 1.0 / (1 + h.estimated_validation_cost / 10000)
        return h.confidence * cost_factor

    return sorted(hypotheses, key=score, reverse=True)


def _estimate_cost(hypothesis: AgentHypothesis) -> float:
    """Estimate validation cost in USD."""
    # Simplified cost model
    base_cost = 5000  # Base experiment cost

    # Adjust by method
    multipliers = {
        "c4_triz": 1.0,
        "analogy": 1.2,  # Cross-domain may need more setup
        "hybrid": 1.5,  # More complex to validate
    }

    return base_cost * multipliers.get(hypothesis.generation_method, 1.0)


def _estimate_time(hypothesis: AgentHypothesis) -> str:
    """Estimate time to validate."""
    times = {
        "c4_triz": "2-4 weeks",
        "analogy": "4-6 weeks",
        "hybrid": "6-8 weeks",
    }
    return times.get(hypothesis.generation_method, "4 weeks")


def _parse_time(time_str: str) -> int:
    """Parse time string to weeks for sorting."""
    import re

    numbers = re.findall(r"\d+", time_str)
    if numbers:
        return int(numbers[0])
    return 4


def _generate_summary(hypotheses: list[AgentHypothesis]) -> str:
    """Generate executive summary."""
    methods: Any = {}
    for h in hypotheses:
        methods[h.generation_method] = methods.get(h.generation_method, 0) + 1

    avg_confidence = (
        sum(h.confidence for h in hypotheses) / len(hypotheses) if hypotheses else 0
    )
    total_cost = sum(h.estimated_validation_cost for h in hypotheses)

    return f"""Generated {len(hypotheses)} hypotheses across {len(methods)} methods.
Average confidence: {avg_confidence:.1%}
Total validation budget: ${total_cost:,.0f}
Top method: {max(methods, key=methods.get) if methods else "N/A"}  # type: ignore[arg-type]
"""


def _generate_recommendations(hypotheses: list[AgentHypothesis]) -> list[str]:
    """Generate actionable recommendations."""
    if not hypotheses:
        return ["No hypotheses generated. Try rephrasing the problem."]

    top = hypotheses[0]
    return [
        f"Start with hypothesis {top.id} (confidence: {top.confidence:.1%})",
        f"Budget ${top.estimated_validation_cost:,.0f} for validation",
        f"Estimated time to validate: {top.estimated_time_to_validate}",
        "Consider parallel validation of top 3 hypotheses",
    ]

estimate_cost = _estimate_cost
estimate_time = _estimate_time
generate_analogies = _generate_analogies
generate_c4_triz = _generate_c4_triz
generate_falsifiability = _generate_falsifiability
generate_hybrid = _generate_hybrid
generate_recommendations = _generate_recommendations
generate_summary = _generate_summary
parse_time = _parse_time
rank_hypotheses = _rank_hypotheses
