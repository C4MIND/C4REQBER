"""Contradiction Miner API Router — /v7/contradiction-miner"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.contradiction_miner.detector import ContradictionResult, detect_contradictions
from src.contradiction_miner.extractor import Claim, ExtractionResult, extract_claims


router = APIRouter(prefix="/api/v7/contradiction-miner", tags=["contradiction-miner"])

@router.post("/extract", response_model=ExtractionResult)
async def extract(request: dict[str, Any]) -> ExtractionResult:
    """
    Extract scientific claims from text.

    Body:
    {
        "text": "Coffee increases alertness. Tea reduces stress."
    }
    """
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    return extract_claims(text)

@router.post("/detect", response_model=ContradictionResult)
async def detect(request: dict[str, Any]) -> ContradictionResult:
    """
    Detect contradictions between claims.

    Body:
    {
        "claims": [
            {"id": "C0", "subject": "...", "predicate": "...", "polarity": "positive"},
            {"id": "C1", "subject": "...", "predicate": "...", "polarity": "negative"},
        ]
    }
    """
    raw_claims = request.get("claims", [])
    if not raw_claims:
        raise HTTPException(status_code=400, detail="claims is required")

    claims = [
        Claim(
            id=c["id"],
            text=c.get("text", ""),
            subject=c.get("subject", ""),
            predicate=c.get("predicate", ""),
            polarity=c.get("polarity", "neutral"),
            confidence=c.get("confidence", 0.5),
            source=c.get("source", ""),
            section=c.get("section", ""),
        )
        for c in raw_claims
    ]

    return detect_contradictions(claims)

@router.post("/pipeline")
async def pipeline(request: dict[str, Any]) -> dict[str, Any]:
    """
    Run full extraction + detection pipeline on text.

    Body:
    {
        "text": "Coffee increases alertness. Tea reduces stress."
    }
    """
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    extraction = extract_claims(text)
    contradiction_result = detect_contradictions(extraction.claims)

    return {
        "extraction": {
            "total_sentences": extraction.total_sentences,
            "claims_per_sentence": extraction.claims_per_sentence,
            "claims_count": len(extraction.claims),
        },
        "contradictions": contradiction_result,
    }

@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available contradiction mining methods and their descriptions."""
    return {
        "methods": [
            {
                "name": "Claim Extraction",
                "endpoint": "POST /v7/contradiction-miner/extract",
                "description": (
                    "Extract scientific claims from text using pattern matching "
                    "on copula, causal, and comparative constructions."
                ),
            },
            {
                "name": "Contradiction Detection",
                "endpoint": "POST /v7/contradiction-miner/detect",
                "description": (
                    "Detect contradictions between claims: direct negation, "
                    "opposite semantic pairs, and polarity mismatches."
                ),
            },
            {
                "name": "Full Pipeline",
                "endpoint": "POST /v7/contradiction-miner/pipeline",
                "description": "Run extraction + detection in one call.",
            },
        ],
        "domain": "Literature Intelligence — Contradiction Mining",
    }
