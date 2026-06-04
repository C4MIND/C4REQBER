#!/usr/bin/env python3
"""Parallel dissertation generation — all 10 topics at once."""
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Load keys
if os.path.exists(".env.development"):
    with open(".env.development") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

TOPICS = [
    "Quantum effects in photosynthesis",
    "Self-healing concrete with bacterial additives",
    "Universal basic income through blockchain",
    "Asteroid mining physics and capture mechanics",
    "Neuroplasticity enhancement through sleep sound stimulation",
    "Geoengineering via marine cloud brightening",
    "Epigenetic reversal of aging through methylation editing",
    "Soft robotics for minimally invasive surgery",
    "Compact fusion reactors for distributed energy",
    "DNA data storage encoding and error correction",
]


async def generate_one(pipeline, topic: str, idx: int) -> dict:
    """Generate single dissertation."""
    start = asyncio.get_event_loop().time()
    try:
        record = await pipeline.discover(topic)
        elapsed = asyncio.get_event_loop().time() - start
        logger.info(f"[{idx}/10] ✅ {topic[:50]}... ({elapsed:.0f}s)")
        return {
            "topic": topic,
            "success": True,
            "sources": len(record.sources),
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": record.simulation.status if record.simulation else "N/A",
            "verification": record.verification.status if record.verification else "N/A",
            "bibliography": len(record.bibliography),
            "time": elapsed,
        }
    except Exception as e:
        elapsed = asyncio.get_event_loop().time() - start
        logger.error(f"[{idx}/10] ❌ {topic[:50]}... ({elapsed:.0f}s) — {e}")
        return {"topic": topic, "success": False, "error": str(e), "time": elapsed}


async def main():
    from src.pipeline.hil_pipeline import HILDiscoveryPipeline
    
    pipeline = HILDiscoveryPipeline()
    logger.info("=" * 70)
    logger.info("PARALLEL GENERATION: 10 dissertations")
    logger.info("=" * 70)
    
    # Launch ALL 10 concurrently
    tasks = [generate_one(pipeline, topic, i+1) for i, topic in enumerate(TOPICS)]
    results = await asyncio.gather(*tasks)
    
    # Summary
    success = sum(1 for r in results if r["success"])
    total_time = sum(r["time"] for r in results)
    
    logger.info("\n" + "=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Success: {success}/10")
    logger.info(f"Failed: {10-success}/10")
    logger.info(f"Total wall time: {total_time:.0f}s ({total_time/60:.1f} min)")
    logger.info(f"Parallel speedup: ~{total_time/600:.1f}x vs sequential")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        logger.info(f"  {status} {r['topic'][:50]}... ({r['time']:.0f}s)")


if __name__ == "__main__":
    asyncio.run(main())
