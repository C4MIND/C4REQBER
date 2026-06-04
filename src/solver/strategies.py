"""
C4REQBER: Solving Strategies
Phase-specific solving methods: literature, consensus, hypotheses,
pattern simulations, validation, recommendations, and next steps.
"""
from __future__ import annotations

from typing import Any

from rich.console import Console

from .core import OneShotResult


console = Console()


async def search_literature(problem: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Semantic Scholar for relevant papers."""
    try:
        from src.search.semantic_scholar import get_semantic_scholar_client

        client = get_semantic_scholar_client()
        papers = await client.search_papers(problem, limit=limit)

        return [
            {
                "title": p.title,
                "authors": p.authors[:3] if len(p.authors) > 3 else p.authors,
                "year": p.year,
                "citation_count": p.citation_count,
                "abstract": p.abstract[:200] + "..."
                if len(p.abstract) > 200
                else p.abstract,
                "fields": p.fields_of_study,
                "open_access": p.open_access_pdf is not None,
                "tldr": p.tldr[:150] + "..." if len(p.tldr) > 150 else p.tldr,
            }
            for p in papers
        ]
    except Exception as e:
        console.print(f"[yellow]Warning: Literature search failed: {e}[/yellow]")
        return []


async def analyze_consensus(
    problem: str, papers: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Analyze scientific consensus from papers."""
    try:
        from src.validation.consensus_meter import (
            Evidence,
            EvidenceStrength,
            EvidenceType,
            get_consensus_meter,
        )

        meter = get_consensus_meter()

        evidence_list = []
        for paper in papers:
            ev_type = (
                EvidenceType.SUPPORTING
                if paper.get("citation_count", 0) > 50
                else EvidenceType.NEUTRAL
            )

            ev = Evidence(
                source=paper["title"],
                type=ev_type,
                strength=EvidenceStrength.MODERATE
                if paper.get("citation_count", 0) > 20
                else EvidenceStrength.WEAK,
                description=paper.get("abstract", ""),
                citation_count=paper.get("citation_count", 0),
                year=paper.get("year", 0),
                peer_reviewed=True,
            )
            evidence_list.append(ev)

        score = meter.calculate_consensus(
            hypothesis_id="temp",
            hypothesis_text=problem,
            evidence_list=evidence_list,
        )

        return {
            "level": score.consensus_level,
            "confidence": score.confidence_score,
            "supporting": score.supporting_count,
            "contradicting": score.contradicting_count,
            "neutral": score.neutral_count,
            "supporting_score": score.supporting_score,
            "contradicting_score": score.contradicting_score,
            "summary": meter.generate_summary_text(score),
        }
    except Exception as e:
        console.print(f"[yellow]Warning: Consensus analysis failed: {e}[/yellow]")
        return None


async def generate_hypotheses(
    problem: str, max_hypotheses: int
) -> list[dict[str, Any]]:
    """Generate hypotheses using agent."""
    try:
        from src.agents.discovery.core import get_agent

        agent = get_agent()
        report = await agent.discover(
            problem=problem, max_hypotheses=max_hypotheses
        )

        return [
            {
                "id": h.id,
                "hypothesis": h.hypothesis,
                "mechanism": h.mechanism,
                "confidence": h.confidence,
                "method": h.generation_method,
                "c4_path": h.c4_path,
                "triz_principles": h.triz_principles,
                "validation_cost": h.estimated_validation_cost,
                "validation_time": h.estimated_time_to_validate,
            }
            for h in report.hypotheses
        ]
    except Exception as e:
        console.print(
            f"[yellow]Warning: Hypothesis generation failed: {e}[/yellow]"
        )
        return []


async def create_validation_plan(
    hypothesis: dict[str, Any]
) -> dict[str, Any]:
    """Create validation plan for top hypothesis."""
    try:
        criteria = [
            {
                "statement": f"Measure key metric of {hypothesis['hypothesis'][:50]}...",
                "measurement": "Primary outcome variable",
                "threshold": "20% improvement",
                "difficulty": "medium",
            },
            {
                "statement": "Check for side effects or negative outcomes",
                "measurement": "Secondary metrics and safety indicators",
                "threshold": "Side effects < 10%",
                "difficulty": "hard",
            },
        ]

        return {
            "hypothesis_id": hypothesis["id"],
            "estimated_cost": hypothesis.get("validation_cost", 5000),
            "estimated_time": hypothesis.get("validation_time", "4 weeks"),
            "criteria": criteria,
        }
    except Exception as e:
        console.print(f"[yellow]Warning: Validation planning failed: {e}[/yellow]")
        return {}


async def run_pattern_simulations(
    hypotheses: list[dict[str, Any]], problem: str = ""
) -> None:
    """Run v6 pattern simulations for hypotheses to enrich confidence."""
    try:
        from src.patterns.runner import get_runner

        runner = get_runner()

        for h in hypotheses:
            pattern_id = match_pattern(h, problem=problem)
            if pattern_id and pattern_id in runner.list_patterns():
                try:
                    sim_result = await runner.run_pattern(
                        pattern_id,
                        hypothesis={
                            "title": h.get("hypothesis", ""),
                            "description": h.get("mechanism", ""),
                        },
                        params={},
                    )
                    h["simulation"] = {
                        "pattern_id": pattern_id,
                        "status": sim_result.get("status"),
                        "metrics": sim_result.get("result", {}).get("metrics", {}),
                        "execution_time_seconds": sim_result.get(
                            "execution_time_seconds", 0
                        ),
                    }
                    if sim_result.get("status") == "completed":
                        confidence_score = sim_result.get("result", {}).get(
                            "confidence_score", 0.5
                        )
                        h["confidence"] = min(
                            0.99, h["confidence"] * 0.6 + confidence_score * 0.4
                        )
                        h["simulation"]["confidence"] = h["confidence"]
                    else:
                        h["simulation"]["confidence"] = h["confidence"]
                except Exception as e:
                    console.print(
                        f"[yellow]Pattern {pattern_id} simulation failed: {e}[/yellow]"
                    )
                    h["simulation"] = {
                        "pattern_id": pattern_id,
                        "status": "failed",
                        "error": str(e),
                        "confidence": h["confidence"],
                    }
            else:
                h["simulation"] = {
                    "pattern_id": None,
                    "status": "no_match",
                    "confidence": h["confidence"],
                }
    except Exception as e:
        console.print(
            f"[yellow]Warning: Pattern simulation phase failed: {e}[/yellow]"
        )


def match_pattern(
    hypothesis: dict[str, Any], problem: str = ""
) -> str | None:
    """Match hypothesis to best v6 pattern based on keywords."""
    text = f"{problem} {hypothesis.get('hypothesis', '')} {hypothesis.get('mechanism', '')}".lower()

    keyword_map = {
        "agent_based": ["agent", "behavior", "individual", "crowd"],
        "cfd": ["fluid", "flow", "aerodynamic", "navier-stokes"],
        "monte_carlo": ["random", "stochastic", "probability", "statistical"],
        "system_dynamics": ["feedback", "stock", "flow", "system"],
        "circuit_simulation": ["circuit", "electronic", "voltage", "current"],
        "neural_network": ["neuron", "brain", "spiking", "synapse", "neural"],
        "fem": ["finite element", "stress", "structural", "mechanics"],
        "dsge": ["macroeconomic", "policy", "rbc", "keynesian", "economy"],
        "garch": ["volatility", "financial risk", "variance"],
        "game_theory": ["nash", "equilibrium", "strategy", "auction"],
        "social_network": ["network", "diffusion", "viral", "social"],
        "supply_chain": ["supply chain", "logistics", "inventory"],
        "epidemic_seir": ["epidemic", "infection", "disease", "virus"],
        "connectome": ["brain", "connectome", "network", "neural"],
        "quantum": ["quantum", "qubit", "superposition"],
        "n_body": ["gravity", "orbit", "planetary", "celestial"],
        "thermal": ["heat", "temperature", "thermal"],
        "elasticity_3d": ["elastic", "deformation", "solid"],
        "evolutionary": ["evolution", "genetic", "selection"],
        "optimization": ["optimize", "linear programming", "lp"],
    }

    scores = {}
    for pattern_id, keywords in keyword_map.items():
        scores[pattern_id] = sum(1 for kw in keywords if kw in text)

    if scores:
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[best] > 0:
            return best
    return None


def generate_recommendations(result: OneShotResult) -> list[str]:
    """Generate actionable recommendations."""
    recs = []

    if result.top_hypothesis:
        h = result.top_hypothesis
        recs.append(
            f"Start with hypothesis {h['id']} (confidence: {h['confidence']:.0%})"
        )

        sim = h.get("simulation")
        if sim and sim.get("pattern_id") and sim.get("status") == "completed":
            recs.append(
                f"Pattern simulation '{sim['pattern_id']}' completed successfully"
            )
        elif sim and sim.get("status") == "failed":
            recs.append("Simulation failed - review hypothesis assumptions")

        if h.get("validation_cost"):
            recs.append(f"Budget ${h['validation_cost']:,.0f} for validation")

        if result.consensus_analysis:
            level = result.consensus_analysis.get("level", "unknown")
            if level in ["strong", "moderate"]:
                recs.append("Strong scientific consensus supports this direction")
            elif level == "contested":
                recs.append("Contradictory evidence exists - validate carefully")

    if len(result.hypotheses) >= 3:
        recs.append(
            f"Consider parallel validation of top {min(3, len(result.hypotheses))} hypotheses"
        )

    return recs


def generate_next_steps(result: OneShotResult) -> list[str]:
    """Generate next steps."""
    steps = []

    if result.top_hypothesis:
        steps.append(
            f"1. Review hypothesis: {result.top_hypothesis['hypothesis'][:60]}..."
        )
        steps.append("2. Design experiment based on validation plan")

        if result.relevant_papers:
            steps.append(
                f"3. Review {len(result.relevant_papers)} relevant papers from literature search"
            )

        steps.append("4. Create validation experiment: turbo validate create")

    return steps
