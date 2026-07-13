#!/usr/bin/env python3
"""Test single dissertation with new Quality Gates + PipelineConfig + UserProfile."""

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Load keys
if os.path.exists(".env.development"):
    with open(".env.development") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

TOPIC = "Self-healing concrete with bacterial additives"


async def main():
    from src.core.user_profile import UserProfile
    from src.pipeline.config import PipelineConfig
    from src.pipeline.hil_pipeline import HILDiscoveryPipeline

    # Create user profile
    user = UserProfile(
        name="Dr. Alexei Volkov",
        affiliation="Moscow Institute of Physics and Technology",
        orcid="0000-0001-2345-6789",
        degree="Ph.D. in Materials Science",
        department="Department of Civil Engineering",
    )

    # Create pipeline config with A+ standards
    config = PipelineConfig(
        min_sources=15,
        min_source_databases=4,
        min_sources_with_url=8,
        min_gaps=3,
        min_hypotheses=4,
        require_numerical_constraints=True,
        hypothesis_ambition="paradigm_shifting",
        include_risk_analysis=True,
        include_budget_estimate=True,
        min_dissertation_words=2500,
        max_references=15,
        enable_quality_score=True,
        min_quality_score=75,
        auto_retry_failed_steps=True,
        max_retry_attempts=2,
    )

    pipeline = HILDiscoveryPipeline(config=config, user_profile=user)
    logger.info("=" * 70)
    logger.info(f"SINGLE TEST: {TOPIC}")
    logger.info("=" * 70)

    record = await pipeline.discover(TOPIC)

    logger.info("\n" + "=" * 70)
    logger.info("FINAL RESULTS")
    logger.info("=" * 70)
    logger.info(f"Query type:      {pipeline._classify_query(TOPIC)}")
    logger.info(f"Sources:         {len(record.sources)}")
    logger.info(f"Gaps:            {len(record.gaps)}")
    logger.info(f"Hypotheses:      {len(record.hypotheses)}")
    logger.info(f"Simulation:      {record.simulation.status if record.simulation else 'N/A'}")
    logger.info(f"Verification:    {record.verification.status if record.verification else 'N/A'}")
    logger.info(f"Bibliography:    {len(record.bibliography)}")

    if record.quality_report:
        logger.info("\nQuality Report:")
        logger.info(f"  Grade:         {record.quality_report.grade}")
        logger.info(f"  Score:         {record.quality_report.overall_score}/100")
        logger.info(f"  All passed:    {record.quality_report.passed_all}")
        for g in record.quality_report.gates:
            status = "✅" if g.passed else "⚠️"
            logger.info(f"  {status} {g.step}: {g.message[:50]} (score: {g.score:.2f})")
        if record.quality_report.recommendations:
            logger.info("  Recommendations:")
            for r in record.quality_report.recommendations:
                logger.info(f"    - {r}")

    if record.gaps:
        logger.info("\nTop gaps:")
        for i, g in enumerate(record.gaps[:3], 1):
            logger.info(f"  {i}. {g.get('area', 'Unknown')[:60]}")


if __name__ == "__main__":
    asyncio.run(main())
