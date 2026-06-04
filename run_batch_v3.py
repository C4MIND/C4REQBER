#!/usr/bin/env python3
"""Batch v3 test runner — runs UniversalSolvePipeline on all 7 v3 topics."""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

# Load secrets
load_dotenv(".env")
load_dotenv(".env.dontredact", override=False)

from src.agents.pipeline import UniversalSolvePipeline


TOPICS: list[dict[str, str]] = [
    {
        "id": "01_cosmology",
        "problem": "Why does the universe exhibit fine-tuning for life?",
        "domain": "physics",
        "title": "Fine-tuning for life",
    },
    {
        "id": "02_superconductivity",
        "problem": "How can we achieve room-temperature superconductivity?",
        "domain": "physics",
        "title": "Room-temp superconductivity",
    },
    {
        "id": "03_consciousness",
        "problem": "What is the neural basis of consciousness?",
        "domain": "neuroscience",
        "title": "Neural basis of consciousness",
    },
    {
        "id": "04_abiogenesis",
        "problem": "How does abiogenesis occur from non-living chemistry?",
        "domain": "biology",
        "title": "Abiogenesis from chemistry",
    },
    {
        "id": "05_qualia",
        "problem": "What causes the hard problem of qualia?",
        "domain": "cognitive_science",
        "title": "Hard problem of qualia",
    },
    {
        "id": "06_quantum_gravity",
        "problem": "How can we unify quantum mechanics and general relativity?",
        "domain": "physics",
        "title": "Quantum gravity unification",
    },
    {
        "id": "07_agi",
        "problem": "What is the optimal architecture for artificial general intelligence?",
        "domain": "computer_science",
        "title": "Optimal AGI architecture",
    },
]

OUTPUT_DIR = Path("discovery/batch_v3_deepwork")


async def run_topic(topic: dict[str, str]) -> dict[str, Any]:
    """Run pipeline for a single topic."""
    print(f"\n{'='*60}")
    print(f"Topic {topic['id']}: {topic['title']}")
    print(f"{'='*60}")

    pipeline = UniversalSolvePipeline()
    t0 = time.time()

    try:
        result = await pipeline.solve(
            problem=topic["problem"],
            mode="deep-work",
            domain_hint=topic["domain"],
            max_depth=3,
        )
        duration = time.time() - t0
        await pipeline.close()

        # Extract citation count
        import re
        citations = re.findall(r"\[\d+\]", result.final_solution or "")

        record = {
            "id": topic["id"],
            "problem": topic["problem"],
            "domain": topic["domain"],
            "confidence": result.confidence,
            "cost_usd": result.cost_usd,
            "duration_sec": round(duration, 1),
            "solution_length": len(result.final_solution or ""),
            "unique_citations": len(set(citations)),
            "total_citation_markers": len(citations),
            "c4_path_length": len(result.c4_path),
            "steps": [
                {
                    "stage": s.stage.value,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in result.steps
            ],
            "solution": result.final_solution,
            "prior_art_summary": result.prior_art_summary,
        }

        # Save individual result
        out_file = OUTPUT_DIR / f"{topic['id']}_result.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # Save markdown
        md_file = OUTPUT_DIR / f"{topic['id']}_dissertation.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# {topic['title']}\n\n")
            f.write(f"**Problem:** {topic['problem']}\n\n")
            f.write(f"**Confidence:** {result.confidence:.2f}\n")
            f.write(f"**Cost:** ${result.cost_usd:.4f}\n")
            f.write(f"**Duration:** {duration:.1f}s\n")
            f.write(f"**Citations:** {len(set(citations))} unique / {len(citations)} total\n\n")
            f.write("---\n\n")
            f.write(result.final_solution or "")

        print(f"✅  Confidence: {result.confidence:.2f} | Cost: ${result.cost_usd:.4f} | Time: {duration:.1f}s")
        print(f"    Citations: {len(set(citations))} unique | Solution: {len(result.final_solution or '')} chars")

        return record

    except Exception as e:
        await pipeline.close()
        print(f"❌  ERROR: {e}")
        return {
            "id": topic["id"],
            "problem": topic["problem"],
            "error": str(e),
            "confidence": 0.0,
            "cost_usd": 0.0,
        }


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start = time.time()
    results: list[dict[str, Any]] = []

    for topic in TOPICS:
        record = await run_topic(topic)
        results.append(record)

    total_time = time.time() - start
    total_cost = sum(r.get("cost_usd", 0) for r in results)
    avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results)

    # Generate SUMMARY.md
    summary_path = OUTPUT_DIR / "SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# C4REQBER v5.6 — Batch v3 Enhanced Test Results\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Pipeline:** UniversalSolvePipeline (MultiSourceSearcher + CitationVerifier + NoveltyScorer)\n")
        f.write(f"**Total topics:** {len(TOPICS)}\n")
        f.write(f"**Total time:** {total_time/60:.1f} min\n")
        f.write(f"**Total cost:** ${total_cost:.4f}\n")
        f.write(f"**Avg confidence:** {avg_confidence:.2f}\n\n")
        f.write("| # | Topic | Confidence | Cost | Time | Citations | Status |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in results:
            tid = r["id"]
            title = next(t["title"] for t in TOPICS if t["id"] == tid)
            conf = r.get("confidence", 0)
            cost = r.get("cost_usd", 0)
            dur = r.get("duration_sec", 0)
            cit = r.get("unique_citations", 0)
            status = "✅" if not r.get("error") else "❌"
            f.write(f"| {tid} | {title} | {conf:.2f} | ${cost:.4f} | {dur:.0f}s | {cit} | {status} |\n")
        f.write("\n")
        f.write("## Key Improvements vs v3 Original\n\n")
        f.write("- **Sources:** 15 active APIs (was 2-5)\n")
        f.write("- **Citations:** Real DOI-verified citations via CitationVerifier\n")
        f.write("- **Novelty:** Embedding-based novelty score in confidence v3\n")
        f.write("- **Circuit breaker:** Auto-skip failing sources\n")
        f.write("- **Cross-validation:** DOI/title deduplication across sources\n")

    print(f"\n{'='*60}")
    print("BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"Total time: {total_time/60:.1f} min")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Avg confidence: {avg_confidence:.2f}")
    print(f"Results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
