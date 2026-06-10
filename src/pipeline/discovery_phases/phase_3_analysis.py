"""Phase 3: Deep Analysis — Contradiction mining, temporal KG, isomorphism,
gap miner, hypothesis generation, competing hypotheses, cognitive plugins,
auto-scanner, strong inference, abduction.

v9.12.5: chunked contradiction mining — splits 387 papers into 6 parallel
chunks of ~65 papers, each processed on a separate CPU core. Cross-block
contradictions are found in a second pass using centroid papers (top-5
most-contradictory papers from each chunk). Compared to v9.12.4 (2 workers
sequential): wall time reduced from ~300s to ~60s on M3 Max (16 cores).

Architecture:
  1. Split papers into 6 chunks + submit to ProcessPoolExecutor (6 workers)
  2. mine_contradictions(chunk) runs on each core independently (intra-chunk)
  3. build_temporal_kg runs on full set (only 10 papers, ~0.1s)
  4. After all chunks complete: pick top-5 papers from each chunk (30 total)
  5. Final mine_contradictions(centroid_papers) finds cross-block contradictions
  6. Merge all contradictions, sort by score, return top-5
"""
from __future__ import annotations

import logging


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase3")


def _pick_centroids(
    chunks: list[list[dict]],
    chunk_results: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Pick top-K most-contradictory papers from each chunk for cross-block
    centroid comparison. Papers are identified by their position in the
    chunk; we reconstruct them from the chunk lists."""
    centroids: list[dict] = []
    for i, cr in enumerate(chunk_results):
        if i >= len(chunks):
            continue
        # Pick first top_k papers from this chunk (or all if smaller)
        n = min(top_k, len(chunks[i]))
        centroids.extend(chunks[i][:n])
    return centroids


async def run_deep_analysis(problem, domain, papers, results, thresholds, errors) -> tuple:
    """Run deep analysis — chunked parallel CPU-bound blocks + cross-block merge."""
    import asyncio
    import time
    from concurrent.futures import ProcessPoolExecutor, as_completed

    from src.discovery.pipeline_logic import (
        build_temporal_kg,
        generate_competing_hypotheses,
        generate_hypothesis,
        mine_contradictions,
        run_abduction,
        run_autoscanner,
        run_cognitive_plugins,
        run_strong_inference,
        search_isomorphisms,
    )

    loop = asyncio.get_running_loop()
    t0 = time.perf_counter()

    # Split papers into ~6 chunks for parallel contradiction mining.
    # On M3 Max (10 perf cores, 6 efficiency) 6 workers saturates all cores.
    # Each chunk ~65 papers → O(65²) = ~4K comparisons vs O(387²) = 150K.
    n_papers = len(papers) if isinstance(papers, list) else 0
    n_workers = min(6, max(2, n_papers // 50))
    chunk_size = max(1, n_papers // n_workers) if n_workers > 0 else n_papers
    chunks = [papers[i:i+chunk_size] for i in range(0, n_papers, chunk_size)]
    logger.info("Phase C: %d papers split into %d chunks (size %d)", n_papers, len(chunks), chunk_size)

    with ProcessPoolExecutor(max_workers=n_workers + 1) as pool:
        # Launch all chunked contradiction mining jobs in parallel
        futs = {}
        for i, chunk in enumerate(chunks):
            futs[pool.submit(mine_contradictions, chunk)] = f"contra_chunk_{i}"
        # Also launch temporal KG (fast — only 10 papers)
        futs[pool.submit(build_temporal_kg, papers, problem)] = "temporal_kg"

        # Collect intra-chunk results
        chunk_results: list[dict] = []
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                result = fut.result(timeout=240)
                if name.startswith("contra_chunk_"):
                    chunk_results.append(result)
                elif name == "temporal_kg":
                    results["temporal_kg"] = result
                    logger.info("Temporal KG: %.3fs", time.perf_counter() - t0)
            except TimeoutError:
                logger.warning("Phase C worker %s timed out", name)
            except Exception as e:
                logger.warning("Phase C worker %s failed: %s", name, e)
                if name == "temporal_kg":
                    results["temporal_kg"] = {"error": str(e)}
        logger.info("Intra-chunk contradiction mining: %d chunks in %.3fs", len(chunk_results), time.perf_counter() - t0)

    # Cross-block centroid pass: combine top-5 papers from each chunk
    # and run one more contradiction detection to find inter-chunk conflicts
    centroids = _pick_centroids(chunks, chunk_results, top_k=5)
    if len(centroids) > 1:
        try:
            cross_result = mine_contradictions(centroids)
            chunk_results.append(cross_result)
            logger.info("Cross-block centroid pass: %d papers in %.3fs",
                        len(centroids), time.perf_counter() - t0)
        except Exception as e:
            logger.warning("Cross-block centroid pass failed: %s", e)

    # Merge all contradictions from all chunks, sort by score, keep top 5
    all_contradictions: list[dict] = []
    total_claims = 0
    for cr in chunk_results:
        total_claims += cr.get("claims_extracted", 0)
        for c in cr.get("top_contradictions", []):
            all_contradictions.append(c)
    all_contradictions.sort(key=lambda c: c.get("score", 0), reverse=True)
    results["contradiction_mining"] = {
        "claims_extracted": total_claims,
        "contradictions_found": len(all_contradictions),
        "top_contradictions": all_contradictions[:5],
    }
    logger.info("Contradiction mining: %d claims, %d contradictions merged in %.3fs",
                total_claims, len(all_contradictions), time.perf_counter() - t0)

    # Isomorphisms (mixed async/sync, networkx — CPU-bound)
    try:
        triz_list = results.get("triz", {}).get("principles", [])
        iso_results = await search_isomorphisms(problem=problem, papers=papers if isinstance(papers, list) else [], triz_principles=triz_list if isinstance(triz_list, list) else [])
        results["isomorphisms"] = iso_results
    except Exception as e:
        results["isomorphisms"] = {"found": 0, "error": str(e)}
        errors.append(f"isomorphism: {str(e)}")

    # Gap miner (async)
    try:
        from src.discovery.gap_miner import GapMiner
        gm = GapMiner()
        gap_result = await gm.mine_for_discovery(problem=problem, papers=papers if isinstance(papers, list) else [])
        results["gap_miner"] = gap_result
    except Exception as e:
        results["gap_miner"] = {"discovery_potential": 0, "error": str(e)}
        errors.append(f"gap_miner: {str(e)}")

    gap_potential: float = results.get("gap_miner", {}).get("discovery_potential", 0)
    if gap_potential < thresholds["min_gap_miner_potential"]:
        abort_reasons = results.setdefault("_abort_reasons", [])
        abort_reasons.append(f"LOW_DISCOVERY_POTENTIAL: GapMiner score = {gap_potential:.2f} (minimum {thresholds['min_gap_miner_potential']}). Research opportunity not supported by literature.")

    # Hypothesis generation (async, LLM-bound — timeout 20s)
    try:
        hypothesis = await asyncio.wait_for(generate_hypothesis(problem=problem, c4_path=results.get("c4_path", {}), triz_principles=results.get("triz", {}).get("principles", []), papers=papers if isinstance(papers, list) else []), timeout=20.0)
        results["hypothesis"] = hypothesis
        try:
            competing = await generate_competing_hypotheses(
                problem=problem,
                primary_hypothesis=hypothesis.get("text", "")[:300],
                triz_principles=results.get("triz", {}).get("principles", []),
                papers=papers[:20] if isinstance(papers, list) else [],
                count=2,
            )
            results["competing_hypotheses"] = competing
            logger.info("Generated %d competing hypotheses", len(competing))
        except Exception:
            logger.exception("one_click_discovery generate_competing_hypotheses failed")
    except Exception as e:
        results["hypothesis"] = {"source": "none", "text": str(e), "error": str(e)}
        errors.append(f"hypothesis: {str(e)}")

    # Cognitive plugins (blocking, CPU-bound — runs after hypothesis is ready)
    try:
        hypothesis_text = results.get("hypothesis", {}).get("text", "") if isinstance(results.get("hypothesis"), dict) else str(hypothesis)
        results["cognitive_plugins"] = run_cognitive_plugins(problem=problem, hypothesis_text=hypothesis_text[:300], domain=domain)
    except Exception as e:
        results["cognitive_plugins"] = {"plugins_run": 0, "error": str(e)}
        errors.append(f"cognitive_plugins: {str(e)}")

    # Auto scanner (async, LLM-bound)
    try:
        results["autoscanner"] = await run_autoscanner(papers)
    except Exception as e:
        results["autoscanner"] = {"error": str(e)}
        errors.append(f"autoscanner: {str(e)}")

    # Strong inference (sync, CPU-light)
    try:
        results["strong_inference"] = run_strong_inference(problem, domain, results.get("hypothesis", {}))
    except Exception as e:
        results["strong_inference"] = {"error": str(e)}
        errors.append(f"strong_inference: {str(e)}")

    # Abduction (sync, CPU-bound but fast)
    try:
        results["abduction_ibe"] = run_abduction(problem, domain, papers)
    except Exception as e:
        results["abduction_ibe"] = {"error": str(e)}
        errors.append(f"abduction_ibe: {str(e)}")

    logger.info("Phase C total: %.3fs", time.perf_counter() - t0)
    return gap_potential, hypothesis
