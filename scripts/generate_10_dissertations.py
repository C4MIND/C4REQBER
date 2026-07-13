#!/usr/bin/env python3
"""Generate 10 paradigm-shifting research proposals via c4reqber HIL pipeline."""

from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Run in background:
#     nohup python3 scripts/generate_10_dissertations.py > logs/dissertations_$(date +%Y%m%d_%H%M%S).log 2>&1 &
#
# Then check progress:
#     tail -f logs/dissertations_*.log

import asyncio
import logging
import os
import sys
import time
from datetime import datetime


# Setup logging
os.makedirs("logs", exist_ok=True)
log_file = f"logs/dissertations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Load keys from .env.development
env_file = ".env.development"
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                if key not in os.environ:
                    os.environ[key] = val

# Topics
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


async def generate_one(pipeline, topic: str, idx: int) -> str | None:
    """Generate single dissertation with retries."""
    start = time.time()
    logger.info(f"\n{'=' * 70}")
    logger.info(f"[{idx}/10] STARTING: {topic}")
    logger.info(f"{'=' * 70}")

    try:
        record = await pipeline.discover(topic)
        elapsed = time.time() - start

        logger.info(f"[{idx}/10] COMPLETE: {topic} ({elapsed:.1f}s)")
        logger.info(f"  Sources: {len(record.sources)}")
        logger.info(f"  Gaps: {len(record.gaps)}")
        logger.info(f"  Hypotheses: {len(record.hypotheses)}")
        logger.info(f"  Simulation: {record.simulation.status if record.simulation else 'N/A'}")
        logger.info(
            f"  Verification: {record.verification.status if record.verification else 'N/A'}"
        )
        logger.info(f"  Bibliography: {len(record.bibliography)}")

        return f"dissertations/live/HIL_v2_{topic.replace(' ', '_')[:30]}.md"
    except Exception as e:
        logger.error(f"[{idx}/10] FAILED: {topic} — {e}")
        return None


async def main():
    from src.pipeline.hil_pipeline import HILDiscoveryPipeline

    pipeline = HILDiscoveryPipeline()
    results = []

    total_start = time.time()

    for i, topic in enumerate(TOPICS, 1):
        path = await generate_one(pipeline, topic, i)
        results.append((topic, path))

        # Small delay between topics to avoid rate limits
        if i < len(TOPICS):
            await asyncio.sleep(2)

    total_elapsed = time.time() - total_start

    # Summary
    logger.info(f"\n{'=' * 70}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total time: {total_elapsed / 60:.1f} minutes")

    success = sum(1 for _, p in results if p)
    failed = len(results) - success

    logger.info(f"Success: {success}/{len(results)}")
    logger.info(f"Failed: {failed}/{len(results)}")

    for topic, path in results:
        status = "✅" if path else "❌"
        logger.info(f"  {status} {topic[:50]}...")
        if path:
            logger.info(f"      → {path}")

    logger.info(f"\nLog saved: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
