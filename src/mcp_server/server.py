from __future__ import annotations


"""
c44tcdi MCP Server
Model Context Protocol server for AI agents.
Run: pip install mcp && python3 -m c44tcdi.mcp_server
"""
import asyncio
import logging
import sys
from typing import Any


logger = logging.getLogger(__name__)

from src.config.paths import load_kilo_env, load_verifiers_env

load_kilo_env()
load_verifiers_env()

# Optional MCP SDK — falls back to stdio JSON-RPC if not installed
try:
    from mcp.server import Server as MCPSDKServer
    from mcp.server.stdio import stdio_server
    HAS_MCP = True
    Server = MCPSDKServer
except ImportError:
    HAS_MCP = False
    Server = None
    stdio_server = None
    print("⚠️  MCP SDK not installed. Run: pip install mcp", file=sys.stderr)  # logger unavailable pre-init

# Real MCP SDK doesn't have @server.tool() decorator — use fallback mode
if HAS_MCP and not hasattr(Server, "tool"):
    HAS_MCP = False

# Real imports for MCP tools
try:
    from src.bayesian.router import run_bma, run_mcmc
    from src.c4.engine import C4Space, C4State
    from src.causal.do_calculus import DoCalculus
    from src.export.manager import ExportManager
    from src.knowledge.orchestrator import MultiSourceSearcher
    from src.simulations.newton_bridge import NewtonBridge
    from src.triz.principles import search_principles as triz_search
    from src.verification.agda_bridge import AgdaBridge
    from src.verification.calibrator import VerificationCalibrator, VerificationContext
    from src.verification.coq_client import CoqClient
    from src.verification.dafny_client import DafnyClient
    from src.verification.lean4_client import Lean4Client
    HAS_TOOLS = True
except ImportError as e:
    HAS_TOOLS = False
    logger.warning("Some tool dependencies not found: %s", e)


from src.mcp_server.fallback_protocol import _FallbackServer


# Create server instance with or without MCP SDK
_server: Any = Server("c44tcdi") if HAS_MCP and Server else _FallbackServer("c44tcdi")
server: Any = _server

# Import c4_codegen tool (registered via @server.tool decorator in codegen.mcp_tool)
try:
    from src.codegen.mcp_tool import c4_codegen
except ImportError as e:
    logger.warning("c4_codegen not available: %s", e)


@server.tool("c4_solve")
async def c4_solve(problem: str, domain: str = "science") -> dict[str, Any]:
    """Run 12-stage discovery pipeline with observer, final verifier, redundant gates.

    Features: iterative paradigm detection, competing hypotheses, self-healing imports.
    Uses C4 cognitive engine + TRIZ + simulations.
    """
    try:
        if not HAS_TOOLS:
            return {"error": "Tool dependencies not available", "status": "error"}

        from src.core.profile_manager import UserProfileManager
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()

        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
        record = await pipeline.discover(problem)

        result = {
            "status": "success",
            "topic": record.topic,
            "sources": len(record.sources),
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": record.simulation.status if record.simulation else "N/A",
            "verification": record.verification.status if record.verification else "N/A",
            "quality_grade": record.quality_report.grade if record.quality_report else "N/A",
            "quality_score": record.quality_report.overall_score if record.quality_report else 0,
            "dissertation_path": f"dissertations/live/HIL_v2_{problem.replace(' ', '_')[:30]}.md",
        }

        if record.quality_report and not record.quality_report.passed_all:
            result["warnings"] = record.quality_report.recommendations

        return result
    except Exception as e:
        logger.exception("MCP tool failed")
        return {"error": str(e), "status": "error"}


@server.tool("c4_search")

async def c4_search(query: str, sources: list[str] | None = None) -> dict[str, Any]:
    """Search across 33 knowledge sources via orchestrator.py (arXiv, PubMed, ORCID, etc.)."""
    try:
        if not HAS_TOOLS:
            return {
                "status": "error",
                "data": [],
                "errors": ["MultiSourceSearcher not available"],
                "metadata": {"query": query, "sources": sources},
            }
        searcher = MultiSourceSearcher()
        results = await searcher.search_all(query, sources=sources)
        truncated = results[:10]
        return {
            "status": "success",
            "data": truncated,
            "metadata": {
                "query": query,
                "sources": sources,
                "total_found": len(results),
                "returned": len(truncated),
            },
        }
    except (AttributeError, ImportError) as e:
        return {
            "status": "error",
            "data": [],
            "errors": [str(e)],
            "metadata": {"query": query, "sources": sources},
        }


@server.tool("c4_triz")

async def c4_triz(
    improving: int = 1,
    worsening: int = 2,
    mode: str = "matrix",
    problem: str = "",
) -> dict[str, Any]:
    """Resolve contradiction using TRIZ tools.

    Modes:
      matrix   — classic contradiction matrix (40 principles)
      ariz     — ARIZ-85C state machine analysis
      standard — 76 Standard Solutions lookup
      sufield  — Su-Field model analysis
    """
    try:
        if mode == "matrix":
            if not HAS_TOOLS:
                return {"error": "TRIZ module not available"}
            principles = triz_search(improving, worsening)
            return {
                "mode": mode,
                "improving": improving,
                "worsening": worsening,
                "principles": [p.number for p in principles[:5]],
            }

        if mode == "ariz":
            from src.triz.ariz import ARIZ85C, list_all_steps
            ariz = ARIZ85C()
            state = ariz.start(problem or "Unspecified problem")
            step = ariz.get_current_step(state)
            return {
                "mode": mode,
                "problem": problem,
                "current_step": step.step_id,
                "step_name": step.name,
                "prompt": step.prompt,
                "observer_level": step.c4_observer,
                "all_steps": list_all_steps(),
                "progress": ariz.get_progress(state),
            }

        if mode == "standard":
            from src.triz.standard_solutions import (
                count_solutions,
                get_all_solutions,
                search_solutions,
            )
            query = problem or ""
            results = search_solutions(query) if query else get_all_solutions()
            return {
                "mode": mode,
                "query": query,
                "counts": count_solutions(),
                "results": [s.to_dict() for s in results[:10]],
            }

        if mode == "sufield":
            from src.triz.sufield import SuFieldAnalyzer
            analyzer = SuFieldAnalyzer()
            analysis = analyzer.analyze(problem or "No problem text provided")
            return {
                "mode": mode,
                "problem": problem,
                "model": analysis.get("model"),
                "completeness": analysis.get("completeness"),
                "transformations": analysis.get("transformations"),
                "c4_mapping": analysis.get("c4_mapping"),
            }

        return {"error": f"Unknown mode: {mode}. Use matrix|ariz|standard|sufield"}

    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_fingerprint")

async def c4_fingerprint(problem: str) -> dict[str, Any]:
    """Classify problem to C4 state (Z₃³ cube coordinates) with C4 → GapAnalyzer ABC resolution scoring.

    Uses neural classifier (ONNX → PyTorch → LLM → heuristic) for best accuracy.
    """
    try:
        # Try neural classifier first (96.5% accuracy when available)
        try:
            from src.c4.neural_classifier.neural_fingerprint import NeuralFingerprint
            fp = NeuralFingerprint()
            if fp.is_available:
                result = fp.classify(problem)
                return {
                    "problem": problem,
                    "state": list(result.state.coordinates),
                    "fingerprint": result.state.label,
                    "confidence": result.confidence,
                    "backend": fp.backend,
                    "model": result.model,
                    "probabilities": result.probabilities,
                }
        except (ImportError, OSError, RuntimeError, ValueError):
            pass

        # Fallback: heuristic C4 engine
        if not HAS_TOOLS:
            return {"error": "C4 engine not available"}
        space = C4Space()
        try:
            from src.c4.routing import FRARouter
            router = FRARouter()
            state = router.classify_c4_state(problem)
        except (ImportError, AttributeError):
            state = space._heuristic_classify(problem)
        return {"problem": problem, "state": list(state.to_tuple()), "fingerprint": str(state)}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_verify")

async def c4_verify(code: str, language: str | None = None) -> dict[str, Any]:
    """Verify formal proof in lean4, coq, dafny, agda, z3, hoare, cvc5, tla, or alloy."""
    try:
        if not HAS_TOOLS:
            return {"error": "Verification module not available"}

        # Auto-detect backend when language is not specified
        if not language:
            calibrator = VerificationCalibrator()
            language = calibrator.select_backend(code, VerificationContext())

        if language == "lean4":
            client = Lean4Client()
            if not client.available:
                return {"valid": False, "error": "Lean4 not installed"}
            result = client.check_proof(code)
            return {"valid": result.get("success", False), "proof": code, "language": language, "details": result}
        elif language == "coq":
            client = CoqClient()
            if not client.is_available():
                return {"valid": False, "error": "Coq not installed"}
            result = client.check_proof(code)
            return {"valid": result.get("valid", False), "proof": code, "language": language, "details": result}
        elif language == "dafny":
            client = DafnyClient()
            if not client.is_available():
                return {"valid": False, "error": "Dafny not installed"}
            result = client.verify(code)
            return {"valid": result.get("valid", False), "proof": code, "language": language, "details": result}
        elif language == "agda":
            client = AgdaBridge()
            if not client.available:
                return {"valid": False, "error": "Agda not installed"}
            result = client.type_check(code)
            return {"valid": result.get("success", False), "proof": code, "language": language, "details": result}
        elif language == "z3":
            try:
                import ast

                import z3
                s = z3.Solver()
                s.set("timeout", 5000)  # prevent DoS from exponential SMT-LIB2 blowup
                try:
                    s.from_string(code)
                except z3.Z3Exception as e:
                    logger.warning("Z3 parse error: language=%s error=%s", language, e)
                    return {"error": f"Z3 parse error: {e}", "status": "error", "language": language}
                except (ValueError, RuntimeError):
                    # Fallback: use AST validation for safe evaluation
                    # Whitelist allowed nodes
                    tree = ast.parse(code, mode="exec")
                    for node in ast.walk(tree):
                        if not isinstance(node, (ast.Module, ast.Expr, ast.Call, ast.Name, ast.Constant,
                                                  ast.BinOp, ast.UnaryOp, ast.Compare, ast.BoolOp,
                                                  ast.Attribute, ast.Subscript)):
                            return {"valid": False, "error": f"Invalid AST node: {type(node).__name__}", "language": language}
                        # Check for dangerous names
                        if isinstance(node, ast.Name) and node.id in ("__import__", "eval", "exec", "compile", "open", "os", "sys"):
                            return {"valid": False, "error": f"Dangerous name: {node.id}", "language": language}
                    # Safe AST-based Z3 assertion extraction (no exec)
                    z3_names = {"Int", "Real", "Bool", "And", "Or", "Not", "Implies",
                                "ForAll", "Exists", "If", "Distinct", "Sum", "Product",
                                "BitVec", "BitVecVal", "IntVal", "RealVal", "BoolVal",
                                "true", "false", "solve", "prove"}
                    z3_attrs = {"add", "check", "model", "assert_and_track", "push", "pop",
                                "reset", "to_smt2", "sexpr", "set", "from_string",
                                "Solver", "SimpleSolver", "Tactic", "Then", "Repeat",
                                "OrElse", "With", "ParOr", "ParThen"}
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == "s":
                                    return {"valid": False, "error": "Cannot reassign 's' — use s.add()", "language": language}
                        if isinstance(node, ast.Name) and node.id not in z3_names and node.id not in z3_attrs and not node.id.startswith("_"):
                            pass  # Allow unknown names (could be Z3 variables)
                        if isinstance(node, ast.Call):
                            func = node.func
                            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "s" and func.attr in z3_attrs:
                                return {"valid": False, "error": f"Cannot call s.{func.attr}() without exec — use SMT-LIB2 format instead", "language": language}
                    return {"valid": False, "error": "Z3 Python code requires exec() which is disabled. Use SMT-LIB2 format (e.g. (declare-const x Int) (assert (> x 0)) (check-sat))", "language": language}
                result = s.check()
                is_sat = result == z3.sat
                return {
                    "valid": is_sat,
                    "proof": code,
                    "language": language,
                    "details": {"status": str(result), "model": str(s.model()) if is_sat else None},
                }
            except (z3.Z3Exception, ValueError, RuntimeError) as e:
                logger.warning("Z3 verification error: language=%s error=%s", language, e)
                return {"valid": False, "error": f"Z3 error: {e}", "language": language}
        elif language == "hoare":
            from src.verification.hoare_verifier import HoareVerifier
            hv = HoareVerifier()
            result = hv.verify(code)
            return {
                "valid": result.valid,
                "proof": code,
                "language": language,
                "details": result.to_dict(),
                "error": result.error or None,
            }
        elif language == "cvc5":
            from src.verification.cvc5_client import CVC5Client
            client = CVC5Client()
            if not client.is_available():
                return {"valid": False, "error": "CVC5 not installed"}
            result = client.verify(code)
            return {"valid": result.get("valid", False), "proof": code, "language": language, "details": result}
        elif language in ("tla", "tla+"):
            from src.verification.tla_client import TLAClient
            client = TLAClient()
            if not client.is_available():
                return {"valid": False, "error": "TLA+ TLC not installed"}
            result = client.verify(code)
            return {"valid": result.get("valid", False), "proof": code, "language": "tla", "details": result}
        elif language == "alloy":
            from src.verification.alloy_client import AlloyClient
            client = AlloyClient()
            if not client.is_available():
                return {"valid": False, "error": "Alloy not installed"}
            result = client.verify(code)
            return {"valid": result.get("valid", False), "proof": code, "language": language, "details": result}
        elif language in ("haskell", "haskell-typecheck"):
            from src.verification.haskell_bridge import verify_haskell_typecheck
            result = verify_haskell_typecheck(code)
            valid = result.get("status") == "passed"
            return {
                "valid": valid,
                "proof": code,
                "language": "haskell-typecheck",
                "details": result,
                "error": None if valid else str(result.get("error", result.get("message", ""))),
            }
        elif language == "haskell-quickcheck":
            from src.verification.haskell_bridge import verify_haskell_quickcheck
            result = verify_haskell_quickcheck(code)
            valid = result.get("status") == "passed"
            return {
                "valid": valid,
                "proof": code,
                "language": "haskell-quickcheck",
                "details": result,
                "error": None if valid else str(result.get("error", result.get("message", ""))),
            }
        else:
            return {"valid": False, "error": f"Unsupported language: {language}"}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_prove")
async def c4_prove(hypothesis: str, language: str = "lean4") -> dict[str, Any]:
    """Prove a hypothesis using LLM-based formal proof generation + iterative error correction.

    Uses an LLM (Claude/GPT/DeepSeek) to generate a formal proof in the
    target language, then compiles it with the native prover.
    On error, the LLM receives the error and fixes the proof.
    Repeats up to 3 iterations.

    Args:
        hypothesis: Natural-language hypothesis to prove
        language: Target language (lean4, coq, dafny, agda, z3, hoare, cvc5, tla, alloy)

    Returns:
        Dict with valid, proof, iterations, error
    """
    try:
        from src.verification.llm_prover import LLMProver

        prover = LLMProver()
        result = await prover.prove(hypothesis, language, max_iterations=3)
        return result.to_dict()
    except Exception as e:
        logger.exception("MCP tool failed")
        return {"valid": False, "error": str(e)}


@server.tool("c4_transfer")

async def c4_transfer(problem: str, source_domain: str, target_domain: str) -> dict[str, Any]:
    """Execute cross-domain structural isomorphism transfer."""
    try:
        from src.c4_analysis.transfer_pipeline import TransferPipeline
        pipeline = TransferPipeline()
        result = pipeline.transfer(problem, source_domain, target_domain)
        return result.to_dict()
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e), "status": "error"}


@server.tool("c4_simulate")

async def c4_simulate(pattern_id: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Run physics simulation via PatternRunnerV2 (pattern_id selects engine)."""
    try:
        if not HAS_TOOLS:
            return {"error": "Simulation modules not available"}
        from src.simulations.runner_v2 import get_runner_v2
        runner = get_runner_v2()
        result = runner.run(pattern_id, hypothesis or {})
        return {"pattern": pattern_id, "result": result}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_bayesian")

async def c4_bayesian(models: dict[str, float], samples: int = 1000) -> dict[str, Any]:
    """Run Bayesian inference (MCMC/BMA) on competing models."""
    try:
        if not HAS_TOOLS:
            return {"error": "Bayesian module not available"}
        # Use BMA for model comparison
        result = await run_bma({"models": models, "samples": samples})
        return {"models": models, "samples": samples, "best_model": result.get("best_model", "")}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_causal")

async def c4_causal(nodes: list[dict[str, Any]], treatment: str, outcome: str) -> dict[str, Any]:
    """Perform causal discovery using do-calculus on SCM."""
    try:
        if not HAS_TOOLS:
            return {"error": "Causal module not available"}
        dc = DoCalculus()
        # Build SCM from nodes
        scm_nodes = {n["name"]: n for n in nodes}
        effect = dc.compute_effect(scm_nodes, treatment, outcome)
        return {"treatment": treatment, "outcome": outcome, "causal_effect": effect}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_export")

async def c4_export(discovery: dict[str, Any], format: str = "markdown") -> dict[str, Any]:
    """Export discovery to LaTeX/Markdown/JSON/HTML/PDF/BibTeX."""
    try:
        if not HAS_TOOLS:
            return {"error": "Export module not available"}
        manager = ExportManager()
        if format == "markdown":
            content = manager.export_discovery_markdown(discovery)
        elif format == "json":
            import json
            content = json.dumps(discovery, indent=2)
        else:
            content = str(discovery)
        return {"status": "exported", "format": format, "content": content[:1000]}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


@server.tool("c4_autoresearch")

async def c4_autoresearch(
    file: str,
    metric: str = "val_bpb",
    max_iter: int = 100,
) -> dict[str, Any]:
    """Run Karpathy-style iterative autoresearch loop on a Python training file.

    Implements: propose → execute → evaluate → keep/revert loop with C4-guided mutations.
    Multi-agent parallel execution is enabled via the orchestrator.

    Args:
        file: Path to the Python training script to optimize.
        metric: Metric name to extract from stdout/logs (e.g. val_bpb, val_loss).
        max_iter: Maximum number of mutations to try.

    Returns:
        Report with best_metric, best_iteration, total_iterations, and trace.
    """
    try:
        from operators.autoresearch import run_autoresearch
        report = run_autoresearch(
            file=file,
            metric=metric,
            max_iter=max_iter,
        )
        return {
            "status": "completed",
            "best_metric": report.best_metric,
            "best_iteration": report.best_iteration,
            "total_iterations": report.total_iterations,
            "total_duration_seconds": report.total_duration_seconds,
            "improvement_trace": report.improvement_trace,
        }
    except Exception as e:
        logger.exception("MCP tool failed")
        return {"error": str(e), "status": "error"}


@server.tool("c4_chain")

async def c4_chain(
    problem: str,
    from_state: list[int] | None = None,
    to_state: list[int] | None = None,
) -> dict[str, Any]:
    """Compute C4 discovery chain (Theorem 11: ≤6 steps between any two states).

    If both states are provided, returns the canonical path between them.
    If only `problem` is provided, loads discovery history and returns
    the nearest past discovery with chaining path.
    """
    try:
        from src.discovery.chainer import DiscoveryChainer
    except ImportError:
        try:
            from src.discovery.chainer import DiscoveryChainer
        except ImportError as e:
            return {"error": f"DiscoveryChainer not available: {e}"}

    chainer = DiscoveryChainer()

    if from_state is not None and to_state is not None:
        s1 = C4State(T=from_state[0], S=from_state[1], A=from_state[2])
        s2 = C4State(T=to_state[0], S=to_state[1], A=to_state[2])
        path = chainer.compute_path(s1, s2)
        return {
            "from_state": from_state,
            "to_state": to_state,
            "path": path,
            "step_count": len(path),
            "theorem": "Theorem 11: diameter of C4Space = 6",
        }

    suggestion = chainer.chain_from_history(problem, [])
    if suggestion is None:
        return {
            "problem": problem,
            "path": [],
            "step_count": 0,
            "note": "No prior discoveries found for this problem.",
        }
    return suggestion.to_dict()


@server.tool("c4_meta")

async def c4_meta(reasoning_trace: str, depth: int = 2) -> dict[str, Any]:
    """Meta-cognitive reflection on reasoning quality and path optimization.

    Analyzes a reasoning trace through C4 state space, identifies
    meta-cognitive gaps, and suggests alternative operator sequences.
    """
    try:
        from src.c4.engine import C4Space, C4State
        from src.c4.routing import FRARouter, QualityPreset
    except ImportError as e:
        return {"error": f"C4 engine not available: {e}"}

    router = FRARouter()
    space = C4Space()

    # Fingerprint current reasoning state
    state = router.classify_c4_state(reasoning_trace)

    # Find optimal meta-cognitive states (high A dimension)
    meta_states = [s for s in space.all_states() if s.A >= 1]
    if not meta_states:
        meta_states = space.all_states()

    # Route to nearest meta-cognitive state
    target = min(meta_states, key=lambda s: space.hamming_distance(state, s))
    route = router.find_route(state, target, preset=QualityPreset.SYNTHESIS)

    # Generate reflection
    reflections = [
        f"Current reasoning maps to C4 state {state} (T={state.T}, S={state.S}, A={state.A})",
        f"Recommended meta-cognitive shift: {' → '.join(route.operators[:depth])}",
        f"Hamming distance to optimal meta-state: {route.hamming_distance}",
    ]

    if route.hamming_distance >= 3:
        reflections.append("⚠️ Reasoning is far from meta-cognitive zone. Consider explicit reflection.")
    elif route.hamming_distance <= 1:
        reflections.append("✓ Reasoning is already in meta-cognitive zone.")

    return {
        "state": str(state),
        "target_meta_state": str(target),
        "hamming_distance": route.hamming_distance,
        "operators": route.operators[:depth],
        "reflections": reflections,
        "depth": depth,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BLAST Mode Tools (v5.3.0)
# ═══════════════════════════════════════════════════════════════════════════════

@server.tool("blast_solve")

async def blast_solve(problem: str, output_format: str = "auto", domain: str | None = None) -> dict[str, Any]:
    """Run BLAST solve mode — produces strategic artifacts (PRD, plan, blueprint, code).

    Uses UniversalSolvePipeline v2 with HIL enhancements:
    - MultiSourceSearcher (33 sources)
    - Gap Analysis
    - Quality Gates + Reality Check
    - Plugin Auto-Selection
    - 36 simulation engines (including 32 P1 adapters)
    """
    try:
        from src.agents.pipeline import UniversalSolvePipeline
        from src.core.profile_manager import UserProfileManager

        manager = UserProfileManager()
        manager.load()
        config = manager.get_config()

        pipeline = UniversalSolvePipeline(config=config)
        result = await pipeline.solve(problem, mode="autopilot", domain_hint=domain)

        return {
            "status": "success",
            "mode": "solve",
            "problem": result.problem,
            "final_solution": result.final_solution[:2000],
            "confidence": result.confidence,
            "sources": len(result.sources),
            "gaps": len(result.gaps),
            "quality_report": result.quality_report,
            "c4_path": result.c4_path,
            "plugin_selection": result.plugin_selection,
            "cost_usd": result.cost_usd,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "solve"}


@server.tool("blast_turbo")

async def blast_turbo(topic: str, verify_backend: str = "hybrid", functors: bool = True) -> dict[str, Any]:
    """Run BLAST turbo mode — generates paradigm-shifting research proposal (A+ quality).

    Uses HILDiscoveryPipeline v4 with USP components:
    - IMPACT, C4 Fingerprint, MP Rotation, QZRF, Isomorphism, CDI, TOTE, MatrixDream
    - 33 knowledge sources, 9 functor agents, hybrid verification (6 backends)
    - 36 simulation engines (including 32 P1 adapters + 4 Virtual Bio bridges)
    """
    try:
        from src.core.profile_manager import UserProfileManager
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()
        config.verification_backend = verify_backend
        config.enable_functors = functors

        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
        record = await pipeline.discover(topic)

        return {
            "status": "success",
            "mode": "turbo",
            "topic": record.topic,
            "sources": len(record.sources),
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": record.simulation.status if record.simulation else "N/A",
            "verification": record.verification.status if record.verification else "N/A",
            "quality_grade": record.quality_report.grade if record.quality_report else "N/A",
            "quality_score": record.quality_report.overall_score if record.quality_report else 0,
            "quality_gates": [
                {"step": g.step, "passed": g.passed, "score": round(g.score, 2), "message": g.message}
                for g in (record.quality_report.gates if record.quality_report else [])
            ],
            "dissertation_path": f"dissertations/live/HIL_v2_{topic.replace(' ', '_')[:30]}.md",
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "turbo"}


@server.tool("blast_flash")

async def blast_flash(question: str, with_sources: bool = False, deep: bool = False) -> dict[str, Any]:
    """Run BLAST flash mode — quick LLM answer with optional USP cognitive analysis.

    Args:
        question: Question to answer
        with_sources: Include source citations
        deep: Run USP cognitive components (IMPACT, C4, MP, QZRF, CDI, TOTE)
    """
    try:
        from src.knowledge.orchestrator import MultiSourceSearcher
        from src.llm.gateway import get_gateway
        from src.plugins.unified_registry import WebSearchPlugin

        llm = get_gateway()
        context = ""
        sources = []
        usp_context = {}

        if deep:
            # Run USP cognitive components
            from src.c4.engine import C4Space
            from src.core.cdi_engine import CDIEngine
            from src.metamodels.impact import ImpactEngine
            from src.metamodels.mp.library import MPLibrary
            from src.metamodels.mp.profiles import MPRotationEngine
            from src.metamodels.qzrf.operators import QzrfLibrary

            try:
                impact = ImpactEngine()
                impact_result = impact.identify(question)
                impact_mapped = impact.map(impact_result)
                usp_context["impact"] = f"{len(impact_mapped.get('entities', []))} entities"
            except (ImportError, AttributeError, RuntimeError):
                pass

            try:
                c4_space = C4Space()
                c4_state = c4_space.fingerprint(question)
                usp_context["c4_state"] = str(c4_state)
            except (ImportError, AttributeError, RuntimeError):
                c4_state = "unknown"

            try:
                mp_lib = MPLibrary()
                mp_rotation = MPRotationEngine(mp_lib)
                perspectives = mp_rotation.rotate(question, state=str(c4_state))
                usp_context["perspectives"] = [p.get("name", "") for p in perspectives[:3]]
            except (ImportError, AttributeError, RuntimeError):
                pass

            try:
                qzrf = QzrfLibrary()
                operators = qzrf.select(str(c4_state))
                usp_context["qzrf"] = operators[:5]
            except (ImportError, AttributeError, RuntimeError):
                pass

            try:
                cdi = CDIEngine()
                cdi_result = cdi.analyze(question, context={"c4_state": str(c4_state)})
                usp_context["contradictions"] = len(cdi_result.get("contradictions", []))
            except (ImportError, AttributeError, RuntimeError):
                pass

        if with_sources or deep:
            searcher = MultiSourceSearcher()
            try:
                result = await searcher.search_all(question)
                papers = result.get("papers", [])[:5]
                sources = papers
                context = "\n".join([
                    f"- {p.get('title', '')}: {p.get('snippet', p.get('abstract', ''))[:250]}"
                    for p in papers
                ])
            except (ImportError, AttributeError, RuntimeError, ValueError):
                searcher = WebSearchPlugin()
                results = searcher.execute(question, max_results=3)
                sources = results

        prompt = f"""Answer concisely and accurately.

Context:
{context}

Cognitive Analysis:
{usp_context}

Question: {question}

Answer:"""

        response = await llm.generate(prompt, max_tokens=800, temperature=0.3)

        return {
            "status": "success",
            "mode": "flash",
            "answer": response.content,
            "sources": [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources[:5]],
            "usp_context": usp_context,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "flash"}


@server.tool("blast_turbofactory")

async def blast_turbofactory(domain: str, scale: str = "standard", max_concurrent: int = 5, pipeline_mode: str = "mixed") -> dict[str, Any]:
    """Run BLAST turbofactory mode — parallel paradigm factory (5-100 pipelines).

    Args:
        domain: Domain or problem to research
        scale: mini(5)|standard(10)|mega(25)|giga(100)
        max_concurrent: Max concurrent pipelines
        pipeline_mode: solve|turbo|mixed — which pipeline(s) to run per agent
    """
    try:
        SCALE_MAP = {"mini": 5, "standard": 10, "mega": 25, "giga": 100}
        n_pipelines = SCALE_MAP.get(scale, 10)

        from src.agents.pipeline import UniversalSolvePipeline
        from src.core.profile_manager import UserProfileManager
        from src.llm.gateway import get_gateway
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()

        # Generate sub-problems
        llm = get_gateway()
        prompt = f"Given the domain '{domain}', generate {n_pipelines} distinct research sub-problems. Format as numbered list."
        response = await llm.generate(prompt, max_tokens=1200, temperature=0.8)
        import re
        subproblems = []
        for line in response.content.split("\n"):
            m = re.match(r'^\s*\d+[\.\)]\s*(.+)', line.strip())
            if m and len(m.group(1)) > 10:
                subproblems.append(m.group(1).strip())
        while len(subproblems) < n_pipelines:
            subproblems.append(f"{domain} — aspect {len(subproblems)+1}")
        subproblems = subproblems[:n_pipelines]

        # Run pipelines
        import asyncio
        sem = asyncio.Semaphore(max_concurrent)
        use_solve = pipeline_mode in ("solve", "mixed")
        use_turbo = pipeline_mode in ("turbo", "mixed")

        async def run_one(topic: str) -> dict[str, Any]:
            async with sem:
                result = {
                    "topic": topic,
                    "status": "success",
                    "pipeline_used": [],
                    "solve_result": None,
                    "turbo_result": None,
                }
                if use_solve:
                    try:
                        pipeline = UniversalSolvePipeline(config=config)
                        solve_record = await pipeline.solve(topic, mode="autopilot")
                        result["solve_result"] = {
                            "final_solution": solve_record.final_solution[:500],
                            "confidence": solve_record.confidence,
                            "sources": len(solve_record.sources),
                            "gaps": len(solve_record.gaps),
                        }
                        result["pipeline_used"].append("solve")
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["solve_result"] = {"error": str(e)}
                if use_turbo:
                    try:
                        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
                        turbo_record = await pipeline.discover(topic)
                        result["turbo_result"] = {
                            "hypotheses": len(turbo_record.hypotheses),
                            "sources": len(turbo_record.sources),
                            "quality_grade": turbo_record.quality_report.grade if turbo_record.quality_report else "N/A",
                            "quality_score": turbo_record.quality_report.overall_score if turbo_record.quality_report else 0,
                        }
                        result["pipeline_used"].append("turbo")
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["turbo_result"] = {"error": str(e)}
                if not result["pipeline_used"]:
                    result["status"] = "error"
                    result["error"] = "All pipelines failed"
                return result

        tasks = [run_one(sp) for sp in subproblems]
        results = await asyncio.gather(*tasks)

        successful = [r for r in results if r["status"] == "success"]
        total_hypotheses = sum(r.get("turbo_result", {}).get("hypotheses", 0) for r in successful)
        avg_quality = sum(r.get("turbo_result", {}).get("quality_score", 0) for r in successful) / max(len(successful), 1)

        return {
            "status": "success",
            "mode": "turbofactory",
            "domain": domain,
            "scale": scale,
            "pipeline_mode": pipeline_mode,
            "pipelines": n_pipelines,
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "total_hypotheses": total_hypotheses,
            "avg_quality_score": round(avg_quality, 1),
            "results": results,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "turbofactory"}


@server.tool("blast_auto")

async def blast_auto(query: str) -> dict[str, Any]:
    """Auto-route query to best BLAST mode and execute it.

    Uses keyword-based routing:
    - Scientific → turbo
    - Paradigm/survey → turbofactory
    - Short question → flash
    - Default → solve
    """
    try:
        from src.cli.mode_router import auto_route, get_mode_description

        mode = auto_route(query)
        description = get_mode_description(mode)

        # Execute the routed mode
        if mode == "solve":
            result = await blast_solve(problem=query)
        elif mode == "turbo":
            result = await blast_turbo(topic=query)
        elif mode == "flash":
            result = await blast_flash(question=query, with_sources=True)
        elif mode == "turbofactory":
            result = await blast_turbofactory(domain=query)
        else:
            result = await blast_solve(problem=query)

        result["auto_routed"] = True
        result["selected_mode"] = mode
        result["mode_description"] = description
        return result
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "auto"}


async def main():
    if HAS_MCP and stdio_server:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    elif hasattr(server, "run_stdio_fallback"):
        await server.run_stdio_fallback()
    else:
        logger.error("Cannot start MCP server — neither MCP SDK run() nor run_stdio_fallback() available. Install: pip install mcp")
        sys.exit(1)





# === MCP Tool JSON Schemas (for AI agent structured function calling) ===
c4_solve.schema = {"type":"object","properties":{"problem":{"type":"string","description":"Problem statement to solve via 12-stage discovery pipeline"},"domain":{"type":"string","description":"Scientific domain (default: science)","default":"science"}},"required":["problem"]}
c4_search.schema = {"type":"object","properties":{"query":{"type":"string","description":"Search query across 33 knowledge sources"},"sources":{"type":"array","items":{"type":"string"},"description":"Optional list of source names"}},"required":["query"]}
c4_triz.schema = {"type":"object","properties":{"improving":{"type":"integer","description":"TRIZ parameter to improve (1-39)","default":1},"worsening":{"type":"integer","description":"TRIZ parameter that worsens (1-39)","default":2},"mode":{"type":"string","description":"TRIZ mode: matrix, ariz, standard, sufield","enum":["matrix","ariz","standard","sufield"],"default":"matrix"},"problem":{"type":"string","description":"Problem description for ARIZ/sufield modes","default":""}}}
c4_fingerprint.schema = {"type":"object","properties":{"problem":{"type":"string","description":"Problem text to classify into C4 Z33 cognitive state"}},"required":["problem"]}
c4_verify.schema = {"type":"object","properties":{"code":{"type":"string","description":"Proof code to verify"},"language":{"type":"string","description":"Proof language: lean4, coq, dafny, agda, z3, hoare, cvc5, tla, alloy, haskell-typecheck, haskell-quickcheck"}},"required":["code"]}
c4_prove.schema = {"type":"object","properties":{"hypothesis":{"type":"string","description":"Natural-language hypothesis to prove"},"language":{"type":"string","description":"Target proof language: lean4, coq, dafny, agda, z3, hoare, cvc5, tla, alloy, haskell-typecheck, haskell-quickcheck","default":"lean4"}},"required":["hypothesis"]}
c4_transfer.schema = {"type":"object","properties":{"problem":{"type":"string","description":"Problem to transfer across domains"},"source_domain":{"type":"string","description":"Source domain name"},"target_domain":{"type":"string","description":"Target domain name"}},"required":["problem","source_domain","target_domain"]}
c4_simulate.schema = {"type":"object","properties":{"pattern_id":{"type":"string","description":"Simulation pattern ID"},"hypothesis":{"type":"object","description":"Hypothesis dict with parameters"}},"required":["pattern_id","hypothesis"]}
c4_bayesian.schema = {"type":"object","properties":{"models":{"type":"object","description":"Dict of model_name: prior_probability"},"samples":{"type":"integer","description":"Number of MCMC samples","default":1000}},"required":["models"]}
c4_causal.schema = {"type":"object","properties":{"nodes":{"type":"array","items":{"type":"object"},"description":"SCM node dicts with name and relationships"},"treatment":{"type":"string","description":"Treatment variable name"},"outcome":{"type":"string","description":"Outcome variable name"}},"required":["nodes","treatment","outcome"]}
c4_export.schema = {"type":"object","properties":{"discovery":{"type":"object","description":"Discovery result dict to export"},"format":{"type":"string","description":"Export format: markdown, json, latex, html","enum":["markdown","json","latex","html"],"default":"markdown"}},"required":["discovery"]}
c4_autoresearch.schema = {"type":"object","properties":{"file":{"type":"string","description":"Path to Python training script"},"metric":{"type":"string","description":"Metric name (e.g. val_bpb)","default":"val_bpb"},"max_iter":{"type":"integer","description":"Max mutations","default":100}},"required":["file"]}
c4_chain.schema = {"type":"object","properties":{"problem":{"type":"string","description":"Problem text for discovery chain"},"from_state":{"type":"array","items":{"type":"integer"},"description":"Source C4 state [T,S,A]"},"to_state":{"type":"array","items":{"type":"integer"},"description":"Target C4 state [T,S,A]"}},"required":["problem"]}
c4_meta.schema = {"type":"object","properties":{"reasoning_trace":{"type":"string","description":"Reasoning trace to analyze"},"depth":{"type":"integer","description":"Reflection depth","default":2}},"required":["reasoning_trace"]}
blast_solve.schema = {"type":"object","properties":{"problem":{"type":"string","description":"Problem via UniversalSolvePipeline"},"output_format":{"type":"string","description":"Output: auto, prd, code, plan, blueprint, protocol","default":"auto"},"domain":{"type":"string","description":"Domain hint"}},"required":["problem"]}
blast_turbo.schema = {"type":"object","properties":{"topic":{"type":"string","description":"Research topic for paradigm-shifting proposal"},"verify_backend":{"type":"string","description":"Verification backend","default":"hybrid"},"functors":{"type":"boolean","description":"Enable functor agents","default":True}},"required":["topic"]}
blast_flash.schema = {"type":"object","properties":{"question":{"type":"string","description":"Question for quick answer"},"with_sources":{"type":"boolean","description":"Include source citations","default":False},"deep":{"type":"boolean","description":"Run USP cognitive components","default":False}},"required":["question"]}
blast_turbofactory.schema = {"type":"object","properties":{"domain":{"type":"string","description":"Domain for paradigm factory"},"scale":{"type":"string","description":"Scale: mini, standard, mega, giga","default":"standard"},"max_concurrent":{"type":"integer","description":"Max concurrent pipelines","default":5},"pipeline_mode":{"type":"string","description":"Pipeline: solve, turbo, mixed","default":"mixed"}},"required":["domain"]}
blast_auto.schema = {"type":"object","properties":{"query":{"type":"string","description":"Query to auto-route to best BLAST mode"}},"required":["query"]}


@server.tool("c4_social")
async def c4_social(action: str, draft_id: str = "", platform: str = "") -> dict[str, Any]:
    """Social publishing — preprint upload, post to platforms, health check.

    Actions: status, publish, preview, drafts, health, post.

    Args:
        action: status | publish | preview | drafts | health | post
        draft_id: Draft ID for publish/preview/post actions
        platform: Target platform for post action (twitter, mastodon, reddit, discord, slack)
    """
    from pathlib import Path

    if action == "status":
        from src.social.profile_manager import UserProfile
        p = UserProfile.load()
        drafts_dir = Path.home() / ".c4reqber" / "drafts"
        draft_count = len([d for d in drafts_dir.iterdir() if d.is_dir()]) if drafts_dir.exists() else 0
        return {"author": p.primary_author.name, "orcid": p.orcid_ids, "drafts": draft_count}

    if action == "health":
        from src.social.health_checker import check_all
        return await check_all()

    if action == "drafts":
        drafts_dir = Path.home() / ".c4reqber" / "drafts"
        if not drafts_dir.exists():
            return {"drafts": []}
        import json
        result = []
        for d in sorted(drafts_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            if d.is_dir():
                state = json.loads((d / "draft_state.json").read_text()) if (d / "draft_state.json").exists() else {}
                result.append({"id": d.name, "status": state.get("status", "?")})
        return {"drafts": result}

    if action == "preview" and draft_id:
        draft_dir = Path.home() / ".c4reqber" / "drafts" / draft_id
        md = draft_dir / "dissertation.md"
        if md.exists():
            return {"draft_id": draft_id, "content": md.read_text(encoding="utf-8")[:5000]}
        return {"error": f"Draft {draft_id} not found"}

    if action == "publish" and draft_id:
        from src.social.publisher import Publisher
        pub = Publisher()
        result = await pub.publish(draft_id)
        return result.get("steps", result)

    if action == "post" and draft_id and platform:
        from src.social.i18n_templates import detect_language, format_post
        from src.social.social_history import SocialHistory
        lang = detect_language()
        post = format_post(lang, "preprint_post", title=draft_id, url=f"https://doi.org/c4reqber/{draft_id}")
        SocialHistory().record("mcp_post", platform, draft_id, "pending", text=post)
        return {"draft_id": draft_id, "platform": platform, "post": post[:280], "status": "queued"}

    return {"error": f"Unknown action: {action}. Use: status, publish, preview, drafts, health, post"}


c4_social.schema = {"type":"object","properties":{"action":{"type":"string","description":"Action: status, publish, preview, drafts, health, post"},"draft_id":{"type":"string","description":"Draft ID for publish/preview/post"},"platform":{"type":"string","description":"Platform for post: twitter, mastodon, reddit, discord, slack"}},"required":["action"]}

__all__ = [
    "server",
    "HAS_TOOLS",
    "HAS_MCP",
    "main",
]

if __name__ == "__main__":
    asyncio.run(main())

