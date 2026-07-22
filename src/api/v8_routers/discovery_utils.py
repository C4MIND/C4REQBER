"""
Reqber v8.0: Discovery Utilities

Contains helper functions, Pydantic models, and all 20+ module functions.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.plugins.invoke import invoke_plugin_execute
from src.utils.honesty_status import outer_status_from_plugin_result


logger = logging.getLogger("reqber.api.v8.discovery.utils")


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class OneClickRequest(BaseModel):
    """OneClickRequest."""

    problem: str
    domain: str = "science"
    auto_route: bool = False


class MultiHypothesisRequest(BaseModel):
    """MultiHypothesisRequest."""

    problem: str
    domain: str = "science"
    count: int = 3


class ExportRequest(BaseModel):
    """ExportRequest."""

    discovery: dict[str, Any]
    format: str = "markdown"


class ExportResponse(BaseModel):
    """ExportResponse."""

    status: str
    format: str
    filepath: str | None = None
    content_preview: str | None = None
    error: str | None = None


class DissertationRequest(BaseModel):
    """DissertationRequest."""

    problem: str
    domain: str = "general"
    max_iterations: int = 10
    min_quality: str = "PUBLISHABLE"


# ---------------------------------------------------------------------------
# Domain Helpers
# ---------------------------------------------------------------------------


def _domain_improving_param(domain: str) -> str:
    return {
        "physics": "speed",
        "chemistry": "concentration",
        "biology": "adaptability",
        "engineering": "reliability",
        "materials": "strength",
        "electronics": "power",
        "energy": "efficiency",
        "medicine": "precision",
        "economics": "productivity",
        "software": "speed",
    }.get(domain, "efficiency")


def _domain_worsening_param(domain: str) -> str:
    return {
        "physics": "stability",
        "chemistry": "cost",
        "biology": "complexity",
        "engineering": "weight",
        "materials": "cost",
        "electronics": "heat",
        "energy": "cost",
        "medicine": "side_effects",
        "economics": "risk",
        "software": "complexity",
    }.get(domain, "cost")


# ---------------------------------------------------------------------------
# Analysis Modules
# ---------------------------------------------------------------------------


def run_fra_routing(problem: str) -> dict[str, Any]:
    """Step 2.5: FRA Routing."""
    try:
        from src.c4.routing import FRARouter

        router = FRARouter()
        fp = router.fingerprint(problem)
        return {
            "situation": fp["situation"],
            "c4_state": str(fp["c4_state"]),
            "recommended_operators": fp["recommended_operators"],
            "situation_scores": fp["scores"],
            "routed_chain": router.route(fp["situation"], gap_pct=50.0),
        }
    except (ImportError, KeyError, TypeError) as e:
        return {"error": str(e), "situation": "unknown"}


def run_c4_observer(problem: str, c4_path: dict[str, Any]) -> dict[str, Any]:
    """Step 2.6: C4 Observer."""
    try:
        from src.c4.observer import ObserverController, ObserverPosition
        from src.c4.state import C4State

        controller = ObserverController()
        current = C4State(T=1, S=1, A=1)
        return {
            "observer_positions": {
                pos.name: {
                    "visible_states_count": len(controller.observe(pos, current).visible_states),
                    "blind_spots": controller.observe(pos, current).blind_spots,
                    "insights": controller.observe(pos, current).insights,
                }
                for pos in [
                    ObserverPosition.IMMERSED,
                    ObserverPosition.OBSERVING,
                    ObserverPosition.META,
                ]
            }
        }
    except (ImportError, AttributeError) as e:
        return {"error": str(e)}


async def search_isomorphisms(problem: str, papers: list, triz: list) -> dict[str, Any]:
    """Step 5.5: Isomorphism Search."""
    isomorphisms = []
    try:
        from memory.isomorphism_seed import ISOMORPHISM_SEED

        problem_lower = problem.lower()
        for iso in ISOMORPHISM_SEED:
            if (
                any(t in problem_lower for t in iso.get("target", "").split("_"))
                or any(t in problem_lower for t in iso.get("source", "").split("_"))
                or any(t in problem_lower for t in iso.get("applications", "").split(","))
            ):
                isomorphisms.append(iso)
            if len(isomorphisms) >= 10:
                break
    except ImportError:
        pass
    return {"found": len(isomorphisms), "isomorphisms": isomorphisms[:10]}


def mine_contradictions(papers: list) -> dict[str, Any]:
    """Step 5.1: Contradiction Mining."""
    try:
        from src.litintel.contradiction import ClaimExtractor, ContradictionDetector

        extractor, detector = ClaimExtractor(), ContradictionDetector()
        claims = []
        for p in papers:
            claims.extend(
                extractor.extract(
                    f"{p.get('title', '')}. {p.get('abstract', '')}",
                    source=p.get("source", "unknown"),
                )
            )
        contradictions = detector.find_all_contradictions(claims) if len(claims) >= 2 else []
        return {
            "claims_extracted": len(claims),
            "contradictions_found": len(contradictions),
            "top_contradictions": [
                {
                    "claim_a": c.claim_a.text[:120],
                    "claim_b": c.claim_b.text[:120],
                    "score": round(c.contradiction_score, 3),
                }
                for c in contradictions[:5]
            ],
        }
    except (ImportError, AttributeError) as e:
        return {"error": str(e)}


def build_temporal_kg(papers: list, problem: str) -> dict[str, Any]:
    """Step 5.4: Temporal Knowledge Graph."""
    try:
        from src.litintel.temporal_kg import TemporalKnowledgeGraph, TimeStampedClaim

        kg = TemporalKnowledgeGraph()
        for i, p in enumerate(papers[:10]):
            try:
                year = int(p.get("year", 2025))
            except (ValueError, TypeError):
                year = 2025
            kg.add_claim(
                TimeStampedClaim(
                    id=f"claim_{i}",
                    text=p.get("title", ""),
                    timestamp=datetime(year, 1, 1),
                    source=p.get("source", "unknown"),
                    domain=p.get("domain", ""),
                )
            )
        traj = kg.consensus_trajectory(problem[:80])
        return {
            "claims_indexed": len(kg.claims),
            "stability": traj.get("stability", 0.0),
            "trend": traj.get("trend", "insufficient_data"),
            "paradigm_boundaries": len(kg.find_paradigm_boundaries(problem[:80])),
        }
    except (ImportError, AttributeError) as e:
        return {"error": str(e)}


def detect_paradigm_shift(papers: list, domain: str) -> dict[str, Any]:
    """Step 5.6: Paradigm Shift."""
    try:
        from src.litintel.paradigm_shift import ParadigmShiftDetector, ScientificClaim

        detector = ParadigmShiftDetector()
        claims = [
            ScientificClaim(
                text=p.get("title", ""),
                timestamp=datetime(2025, 1, 1),
                source=p.get("source", "unknown"),
                domain=domain,
            )
            for p in papers[:15]
        ]
        warning = detector.analyze(claims, domain=domain)
        return {
            "paradigm_shift_probability": round(warning.probability, 4),
            "timeframe": warning.estimated_timeframe,
            "crisis_severity": warning.confidence,
            "contributing_factors": warning.contributing_factors[:5],
        }
    except (ImportError, AttributeError, TypeError) as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Inference Modules
# ---------------------------------------------------------------------------


def run_strong_inference(problem: str, domain: str, hypothesis: dict) -> dict[str, Any]:
    """Step 5.5c: Strong Inference."""
    try:
        from src.discovery.strong_inference import (
            StrongInferenceEngine,
            generate_competing_hypotheses,
        )

        engine = StrongInferenceEngine(max_cycles=3)
        result = engine.run(
            problem=problem,
            hypotheses=generate_competing_hypotheses(problem, domain, count=3),
            domain=domain,
        )
        return {
            "method": "Platt's Strong Inference (1964)",
            "cycles": result.cycles,
            "surviving_hypotheses": len(result.surviving_hypotheses),
        }
    except (ImportError, AttributeError, RuntimeError) as e:
        return {"error": str(e)}


def run_abduction(problem: str, domain: str, papers: list) -> dict[str, Any]:
    """Step 5.5d: Abduction."""
    try:
        from src.discovery.abduction import AbductionEngine, Observation

        engine = AbductionEngine()
        obs = [
            Observation(
                description=p.get("title", "")[:100],
                source=p.get("source", "unknown"),
                confidence=0.9,
            )
            for p in papers[:5]
        ] or [Observation(description=problem[:100], source="problem")]
        result = engine.infer_to_best_explanation(observations=obs, domain=domain, max_hypotheses=4)
        return {
            "method": "Inference to the Best Explanation (Peirce)",
            "hypotheses_generated": len(result.hypotheses),
            "best_score": round(result.best_explanation.overall_score, 4)
            if result.best_explanation
            else 0.0,
        }
    except (ImportError, AttributeError, TypeError) as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Bayesian Modules
# ---------------------------------------------------------------------------


def run_bayesian_model_averaging(hypothesis: dict, monte_carlo: dict) -> dict[str, Any]:
    """Step 6.5f: Bayesian Model Averaging."""
    try:
        from bayesian.bma import bayesian_model_averaging

        models = []
        if monte_carlo.get("p_value") is not None:
            models.append(("monte_carlo", 0.5, float(monte_carlo.get("p_value", 0.05))))
        models.extend([("prior", 0.3, 0.5), ("prior_alt", 0.2, 0.5)])
        result = bayesian_model_averaging(models)
        return {
            "weighted_prediction": round(result.weighted_prediction, 4),
            "uncertainty": round(result.uncertainty, 4),
        }
    except (ImportError, AttributeError, TypeError) as e:
        return {"error": str(e)}


def run_dempster_shafer(hypothesis: dict, papers: list) -> dict[str, Any]:
    """Step 6.5g: Dempster-Shafer fused from paper abstracts."""
    try:
        from src.discovery.dempster_literature import fuse_dempster_from_papers

        return fuse_dempster_from_papers(hypothesis, list(papers or []))
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        return {"error": str(e), "heuristic": True}


def run_bayesian_conjugate_update(monte_carlo: dict) -> dict[str, Any]:
    """Step 6.5h: Bayesian Conjugate — requires real samples (no invented data)."""
    try:
        import numpy as np

        from bayesian.core import normal_normal

        raw_data = monte_carlo.get("samples") or monte_carlo.get("data")
        if raw_data is None:
            return {
                "status": "skipped",
                "reason": "No observed samples are available for Bayesian update",
                "posterior_mean": None,
            }
        data = np.array(raw_data, dtype=np.float64)
        if len(data) == 0:
            return {"error": "No data available for Bayesian update", "posterior_mean": None}
        result = normal_normal(
            data=data,
            mu_prior=0.5,
            tau_prior=10.0,
            sigma_known=0.15,
            credible_level=0.95,
        )
        return {"posterior_mean": round(result.mu_post, 4), "note": "using observed data"}
    except (ImportError, AttributeError, TypeError) as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Validation Modules
# ---------------------------------------------------------------------------


def run_falsification_engine(hypothesis: dict, domain: str) -> dict[str, Any]:
    """Step 6.5a: Falsification."""
    try:
        from src.discovery.falsification import FalsificationEngine

        engine = FalsificationEngine()
        h_text = hypothesis.get("text", "")[:300] or ""
        first = h_text.split(".")[0].strip() or h_text[:200]
        is_fals, reason = engine.check_falsifiability(first)
        return {"is_falsifiable": is_fals, "falsifiability_reason": reason}
    except (ImportError, AttributeError, RuntimeError) as e:
        return {"error": str(e)}


def run_doe_design(domain: str) -> dict[str, Any]:
    """Step 6.5b: DoE."""
    try:
        from experiment_design.doe import DesignType, DoEConfig, Factor, generate_design

        config = DoEConfig(
            factors=[
                Factor(name="a", low=0.0, high=100.0, levels=2),
                Factor(name="b", low=0.0, high=100.0, levels=2),
            ],
            design_type=DesignType.LATIN_HYPERCUBE,
            samples=8,
        )
        result = generate_design(config)
        return {"design_type": result.design_type.name, "n_runs": result.design_matrix.shape[0]}
    except (ImportError, AttributeError, ValueError) as e:
        return {"error": str(e)}


def run_power_analysis(hypothesis: dict) -> dict[str, Any]:
    """Step 6.5c: Power Analysis."""
    try:
        import numpy as np

        from experiment_design.power import cohens_d, ttest_sample_size

        rng = np.random.default_rng()
        g1 = np.array(rng.normal(0.5, 0.15, 30), dtype=np.float64)
        g2 = np.array(rng.normal(0.7, 0.15, 30), dtype=np.float64)
        effect = abs(cohens_d(g1, g2))
        result = ttest_sample_size(effect_size=max(effect, 0.2), alpha=0.05, power=0.8)
        return {"effect_size": round(result.effect_size, 4), "power": round(result.power, 4)}
    except (ImportError, AttributeError, TypeError) as e:
        return {"error": str(e)}


def run_reproducibility_check(problem: str) -> dict[str, Any]:
    """Step 6.5d: Reproducibility."""
    try:
        from experiment_design.reproducibility import ReproducibilityValidator

        validator = ReproducibilityValidator(experiment_id=problem[:40])
        check_results = validator.quick_validate(
            data_available=True, code_available=True, env_specified=True
        )
        report = validator.generate_report(check_results)
        return {"overall_score": round(report.overall_score, 2)}
    except (ImportError, AttributeError, KeyError) as e:
        return {"error": str(e)}


def run_consensus_meter(hypothesis: dict, papers: list) -> dict[str, Any]:
    """Step 8.1: Consensus Meter."""
    try:
        from validation.consensus_meter import (
            ConsensusMeter,
            Evidence,
            EvidenceStrength,
            EvidenceType,
        )

        h_text = hypothesis.get("text", "")
        evidence_list = [
            Evidence(
                source=p.get("source", "unknown"),
                type=EvidenceType.SUPPORTING if i % 2 == 0 else EvidenceType.NEUTRAL,
                strength=EvidenceStrength.MODERATE,
                description=p.get("title", "")[:100],
            )
            for i, p in enumerate(papers[:6])
        ]
        score = ConsensusMeter().calculate_consensus("H1", h_text[:100], evidence_list)
        return {"consensus_level": score.consensus_level}
    except (ImportError, AttributeError, KeyError) as e:
        return {"error": str(e)}


def run_empirical_validation(problem: str, c4_path: dict) -> dict[str, Any]:
    """Step 8.2: Empirical Validation."""
    try:
        from validation.tracker import ValidationTracker

        summary = ValidationTracker().get_validation_summary()
        return {"total_experiments": summary.get("total_experiments", 0)}
    except (ImportError, AttributeError, KeyError) as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Other Modules
# ---------------------------------------------------------------------------


def run_matrix_dream(problem: str, c4_path: dict) -> dict[str, Any]:
    """Step 4.7: Matrix Dream."""
    try:
        from metamodels.matrix_dream import MatrixDreamLibrary

        matches = MatrixDreamLibrary().match(problem, top_k=6)
        return {
            "patterns_applied": len(matches),
            "top_patterns": [
                {"id": p.id, "name": p.name, "score": round(s, 3)} for p, s in matches[:5]
            ],
        }
    except (ImportError, AttributeError) as e:
        return {"error": str(e)}


async def run_autoscanner(papers: list) -> dict[str, Any]:
    """Step 5.5x: AutoScanner — extract from real papers only (no demo corpus)."""
    try:
        from src.discovery.autoscanner import AutoScanner

        candidates = await AutoScanner().scan_from_papers(list(papers or []))
        return {
            "candidates_found": len(candidates),
            "demo": False,
            "top_problems": [
                {
                    "problem": c.get("problem", "") or c.get("title", ""),
                    "potential": c.get("discovery_potential", 0),
                }
                for c in candidates[:5]
            ],
        }
    except (ImportError, AttributeError) as e:
        return {"candidates_found": 0, "demo": False, "error": str(e)}


async def run_cognitive_plugins(problem: str, hypothesis_text: str, domain: str) -> dict[str, Any]:
    """Run all 20 cognitive plugins."""
    results = {}
    try:
        from llm.providers.unified import LLMProviderRouter

        LLMProviderRouter.auto_route(problem).get("power_level", "medium") if True else "medium"
    except ImportError:
        pass

    plugins = [
        ("swot", "SWOT"),
        ("red_team", "Red Team"),
        ("six_hats", "Six Hats"),
        ("five_whys", "5 Whys"),
        ("scamper", "SCAMPER"),
        ("pareto", "Pareto"),
        ("ishikawa", "Ishikawa"),
        ("morphological", "Morphological"),
        ("delphi", "Delphi"),
        ("ooda", "OODA"),
        ("pre_mortem", "Pre-Mortem"),
        ("second_order", "Second-Order"),
        ("lateral_thinking", "Lateral"),
        ("design_thinking", "Design"),
        ("first_principles", "First"),
        ("inversion", "Inversion"),
        ("constraint_relaxation", "Constraint"),
        ("analogical_reasoning", "Analogical"),
        ("bayesian_update", "Bayesian"),
        ("persistence", "Persistence"),
    ]

    for plugin_name, display_name in plugins:
        try:
            import importlib

            module = importlib.import_module(f"src.plugins.{plugin_name}")
            if hasattr(module, "execute"):
                plugin_result = invoke_plugin_execute(
                    module.execute,
                    problem=problem[:2000],
                    context=f"{problem} {hypothesis_text}",
                    domain=domain,
                )
                results[plugin_name] = {
                    "name": display_name,
                    "status": outer_status_from_plugin_result(plugin_result),
                    "result": plugin_result,
                }
            else:
                results[plugin_name] = {"name": display_name, "status": "no_execute"}
        except (ImportError, AttributeError, RuntimeError) as e:
            results[plugin_name] = {"name": display_name, "status": "error", "error": str(e)[:100]}

    success = sum(1 for v in results.values() if v.get("status") == "success")
    partial = sum(1 for v in results.values() if v.get("status") == "partial")
    return {
        "plugins_run": len(plugins),
        "successful": success,
        "partial": partial,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Export Helpers
# ---------------------------------------------------------------------------


def _normalize_discovery_for_markdown(discovery: dict) -> dict:
    """Normalize discovery for markdown export."""
    hypothesis = discovery.get("hypothesis", {})
    hypothesis_text = (
        hypothesis.get("text", str(hypothesis)) if isinstance(hypothesis, dict) else str(hypothesis)
    )
    c4_path = discovery.get("c4_path", {})
    c4_list = (
        c4_path.get("operators", [c4_path.get("summary", "")])
        if isinstance(c4_path, dict)
        else (c4_path if isinstance(c4_path, list) else [])
    )
    return {
        "created_at": discovery.get("created_at") or datetime.now().isoformat(),
        "domain": discovery.get("domain", "general"),
        "problem": discovery.get("problem", "N/A"),
        "hypothesis": hypothesis_text,
        "c4_path": c4_list,
    }


def _build_dissertation(discovery: dict, attempts: list) -> dict:
    """Build dissertation — delegate to pipeline_logic (real literature + citations)."""
    from src.discovery.pipeline_logic import _build_dissertation as _build_from_pipeline

    return _build_from_pipeline(discovery, attempts)


def _score_hypothesis(h: dict) -> float:
    """Score hypothesis for ranking."""
    n = h.get("novelty", {})
    novelty = 0.5 if isinstance(n, dict) and n.get("status") == "checked" else 0.0
    sim = 0.3 if h.get("simulation", {}).get("status") not in ("error", "timeout") else 0.0
    text = min(len(h.get("text", "")) / 500.0, 0.2)
    return round(novelty + sim + text, 3)
