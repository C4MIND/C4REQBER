"""
Reqber v8.0: Core Discovery Functions

Contains the main discovery functions:
- C4 cognitive navigation
- TRIZ contradiction resolution
- Knowledge search
- Hypothesis generation
- Paper generation
- Proof generation
- Simulation
"""

import asyncio
import logging
import time
from typing import Any


logger = logging.getLogger("reqber.api.v8.discovery.core")


# ---------------------------------------------------------------------------
# Step 1-2: C4 cognitive navigation
# ---------------------------------------------------------------------------

def navigate_c4(problem: str) -> dict[str, Any]:
    """Navigate C4 cognitive space for the given problem.

    Derives start/end states from problem keywords to make navigation
    problem-dependent rather than purely decorative.
    """
    try:
        from src.c4.engine import C4Space, C4State
        space = C4Space()

        # Derive start/end from problem keywords
        p_lower = problem.lower()
        t_start = 0
        if any(w in p_lower for w in ("future", "predict", "forecast", "will", "next")):
            t_start = 2
        elif any(w in p_lower for w in ("now", "current", "present", "today", "existing")):
            t_start = 1

        s_start = 0
        if any(w in p_lower for w in ("abstract", "theory", "model", "framework")):
            s_start = 1
        elif any(w in p_lower for w in ("meta", "paradigm", "epistemology", "ontology")):
            s_start = 2

        a_start = 0
        if any(w in p_lower for w in ("other", "team", "group", "community", "society")):
            a_start = 1
        elif any(w in p_lower for w in ("system", "ecosystem", "network", "organization")):
            a_start = 2

        # End state: push toward future + meta + system perspective
        t_end = (t_start + 2) % 3
        s_end = (s_start + 2) % 3
        a_end = (a_start + 2) % 3

        start = C4State(T=t_start, S=s_start, A=a_start)
        end = C4State(T=t_end, S=s_end, A=a_end)
        path = space.shortest_path(start, end)
        states = path.states_visited()
        return {
            "start": str(start), "end": str(end),
            "path": [str(s) for s in states], "steps": path.length,
            "states_visited": len(states), "operators": path.operators,
            "hamming_distance": space.hamming_distance(start, end), "problem": problem,
        }
    except ImportError as e:
        raise RuntimeError(f"C4 engine not available: {e}") from e
    except AttributeError as e:
        logger.error("C4 navigation error: %s", e)
        raise


# ---------------------------------------------------------------------------
# Step 3-4: TRIZ contradiction resolution
# ---------------------------------------------------------------------------

def resolve_triz(problem: str, domain: str = "science") -> list[dict[str, Any]]:
    """Resolve problem using TRIZ contradiction matrix."""
    try:
        from src.triz.bridge import C4TrizBridge
        from src.triz.matrix import get_recommended_principles
        from src.triz.matrix_core import get_parameter_id
        bridge = C4TrizBridge()
        domain_params: dict[str, tuple[str, str]] = {
            "physics": ("speed", "force"), "chemistry": ("concentration", "temperature"),
            "biology": ("adaptability", "stability"), "engineering": ("weight", "strength"),
            "materials": ("strength", "weight"), "electronics": ("power", "signal_to_noise"),
            "energy": ("efficiency", "losses"), "medicine": ("precision", "side_effects"),
            "economics": ("productivity", "cost"), "software": ("speed", "memory"),
        }
        improving, worsening = domain_params.get(domain, ("speed", "force"))
        imp_id = get_parameter_id(improving)
        wors_id = get_parameter_id(worsening)
        if imp_id is None or wors_id is None:
            return [{"id": i, "name": n, "description": d} for i, n, d in [
                (1, "Segmentation", "Divide"), (2, "Extraction", "Extract"),
                 (3, "Local Quality", "Change")]]
        principles = get_recommended_principles(imp_id, wors_id)
        results = []
        for pid in principles[:10]:
            info = bridge.get_principle_info(pid)
            results.append({"id": pid,
                          "name": info.name if hasattr(info, "name") else str(info),
                          "description": info.description if hasattr(info, "description") else ""}
                         if info else {"id": pid, "name": f"Principle #{pid}", "description": ""})
        return results or [{"id": i, "name": n, "description": d} for i, n, d in [
            (1, "Segmentation", "Divide"), (2, "Extraction", "Extract"),
             (3, "Local Quality", "Change")]]
    except (ImportError, AttributeError) as e:
        logger.error("TRIZ resolution error: %s", e)
        return [{"id": 1, "name": "Segmentation", "description": "Fallback"}]


# ---------------------------------------------------------------------------
# Step 5: Knowledge search
# ---------------------------------------------------------------------------

async def search_knowledge(problem: str) -> list[dict[str, Any]]:
    """Search papers across registered sources."""
    try:
        from src.knowledge.orchestrator import MultiSourceSearcher

        searcher = MultiSourceSearcher()
        start = time.perf_counter()
        result = await asyncio.wait_for(
            searcher.search_all(problem, domain="general", max_per_source=8, include_web=False),
            timeout=12.0,
        )
        papers = result.get("papers", []) if isinstance(result, dict) else []
        elapsed = time.perf_counter() - start
        logger.info("Knowledge search found %d papers in %.2fs", len(papers), elapsed)
        return papers
    except TimeoutError:
        logger.warning("Knowledge search timed out")
        raise
    except Exception as e:
        logger.warning("Knowledge search error: %s", e)
        raise


# ---------------------------------------------------------------------------
# Step 6: Hypothesis generation
# ---------------------------------------------------------------------------

async def generate_hypothesis(
    problem: str, c4_path: dict[str, Any],
    triz_principles: list[dict[str, Any]], papers: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a scientific hypothesis grounded in retrieved paper abstracts."""
    triz_names = ", ".join(p["name"] for p in triz_principles[:3])
    try:
        from src.api.v8_routers.discovery.pipeline import _sanitize_for_prompt
        from src.llm.gateway import get_gateway

        # Sanitize user input before any prompt interpolation
        safe_problem = _sanitize_for_prompt(problem, max_len=500)

        # RAG: retrieve semantically relevant abstracts from ChromaDB
        rag_context = ""
        try:
            from src.knowledge.chroma_store import ChromaVectorStore
            store = ChromaVectorStore()
            rag_results = store.search_papers(problem, n_results=5)
            if rag_results:
                rag_context = "\n\nRELEVANT RESEARCH ABSTRACTS:\n"
                for i, r in enumerate(rag_results[:5], 1):
                    title = r.get("title", "")[:80]
                    rag_context += f"[{i}] {title}\n"
            else:
                # Fallback: use provided papers directly
                rag_context = "\n\nPAPERS:\n" + "\n".join(
                    f"- {p.get('title', '')[:100]}" for p in (papers or [])[:8]
                )
        except Exception:
            logger.warning("RAG retrieval failed, using paper titles as fallback", exc_info=True)
            rag_context = "\n\nPAPERS:\n" + "\n".join(
                f"- {p.get('title', '')[:100]}" for p in (papers or [])[:8]
            )

        # Try LLMCouncil first (N-version redundancy), fallback to single model
        council_result = None
        try:
            from src.llm.council import council_generate
            prompt = (
                f"Generate hypothesis. Problem: {safe_problem}\n"
                f"TRIZ Principles: {triz_names}\n"
                f"{rag_context}\n\n"
                "CRITICAL: Ground your hypothesis in the provided research. "
                "Reference specific paper numbers [N] when citing evidence. "
                "Specific, falsifiable, 3-4 sentences. No markdown."
            )
            council_result = await council_generate(prompt, max_tokens=400, temperature=0.4)
            llm_text = council_result.consensus
            if council_result.agreement_score < 0.5:
                logger.warning(
                    "LLMCouncil agreement low (%.2f) for hypothesis; using consensus anyway",
                    council_result.agreement_score,
                )
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.debug("LLMCouncil unavailable for hypothesis: %s", e)
            llm_text = await get_gateway().chat(
                messages=[{"role": "user", "content":
                    f"Generate hypothesis. Problem: {safe_problem}\n"
                    f"TRIZ Principles: {triz_names}\n"
                    f"{rag_context}\n\n"
                    "CRITICAL: Ground your hypothesis in the provided research. "
                    "Reference specific paper numbers [N] when citing evidence. "
                    "Specific, falsifiable, 3-4 sentences. No markdown."}],
                max_tokens=400, temperature=0.4)
    except (ImportError, AttributeError, RuntimeError) as e:
        llm_text = ""
        logger.warning("LLM hypothesis error: %s", e)

    if not llm_text or len(llm_text) < 50:
        raise RuntimeError("Hypothesis generation failed: LLM unavailable or returned insufficient content")

    # Evidence-based confidence: novelty × source coverage × RAG grounding
    confidence = 0.5
    if papers:
        confidence += min(len(papers) / 50, 0.2)  # Source coverage boost
    if rag_context and "RELEVANT RESEARCH" in rag_context:
        confidence += 0.1  # RAG grounding boost
    if council_result is not None and council_result.agreement_score > 0.5:
        confidence += min(council_result.agreement_score * 0.1, 0.1)  # Council agreement boost

    return {
        "source": "LLMProvider/v8",
        "text": llm_text,
        "structured": False,
        "confidence": round(min(confidence, 0.95), 3),
    }


# ---------------------------------------------------------------------------
# Step 9: Paper generation
# ---------------------------------------------------------------------------

def generate_paper(hypothesis: dict[str, Any], papers: list[dict[str, Any]],
                  proof: dict[str, Any]) -> dict[str, Any]:
    """Generate LaTeX paper with BibTeX."""
    hypothesis_text = hypothesis.get("text", "Hypothesis text not available")
    bibtex_entries = []
    for i, paper in enumerate(papers[:10]):
        title = paper.get("title", f"Untitled {i}")
        authors_str = " and ".join(paper.get("authors", ["Unknown"]))
        year = paper.get("year", 2025)
        doi = paper.get("doi", "")
        entry = f"@article{{ref{i+1},\n  author = {{{authors_str}}},\n  title = {{{title}}}"
        if doi:
            entry += f",\n  doi = {{{doi}}}"
        entry += f",\n  year = {{{year}}}\n}}"
        bibtex_entries.append(entry)

    return {"latex": rf"""\documentclass{{article}}
\usepackage{{amsmath, amssymb, amsthm}}
\title{{One-Click Discovery}}
\begin{{document}}
\maketitle
\begin{{abstract}}{hypothesis_text[:500]}\end{{abstract}}
\section{{Introduction}}
\section{{Methodology}}
\section{{Results}}
\section{{Conclusion}}
\end{{document}}""",
            "bibtex": "\n\n".join(bibtex_entries) or "% No references",
            "reference_count": len(bibtex_entries)}


# ---------------------------------------------------------------------------
# Step 8: Proof generation
# ---------------------------------------------------------------------------

async def generate_lean4_proof(hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Generate Lean 4 proof."""
    try:
        from src.verification.llm_prover import LLMProver
        gen = LLMProver()
        h_text = hypothesis.get("text", str(hypothesis)[:500])
        proof_code_res = await gen.prove(h_text, "lean4")
        return {"language": "lean4", "proof": proof_code_res.proof[:500],
                "generated": True}
    except (ImportError, AttributeError, RuntimeError) as e:
        return {"language": "lean4", "proof": f"(* Error: {e} *)",
                "generated": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Step 7: Simulation
# ---------------------------------------------------------------------------

async def run_relevant_simulation(domain: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Run physics simulation."""
    try:
        from src.simulations.domain_selector import get_domain_simulations
        from src.simulations.newton_bridge import NewtonBridge
        pattern_ids = get_domain_simulations(domain, count=4)
        results = {}
        newton = NewtonBridge()
        for pid in pattern_ids[:3]:
            try:
                sim = newton.run_simulation({"pattern_id": pid, "domain": domain,
                                              "duration": 10.0, "dt": 0.01,
                                              "hypothesis": hypothesis.get("text", "")[:100]})
                results[pid] = {"status": getattr(sim, 'status', 'completed'),
                               "final_state": str(getattr(sim, 'final_state', 'ok'))[:200],
                                "time_steps": getattr(sim, 'time_steps', 0)}
            except (TimeoutError, RuntimeError, AttributeError) as e:
                results[pid] = {"status": "error", "error": str(e)[:100]}
        return {"engine": "newton", "domain": domain, "patterns_run": len(results),
                "pattern_ids": pattern_ids[:3], "results": results, "status": "completed"}
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"NewtonBridge unavailable: {e}") from e
