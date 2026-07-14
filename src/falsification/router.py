"""Falsification Engine API Router — /v7/falsification"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.falsification.lakatos import (
    ProgrammeEvaluation,
    ResearchProgramme,
    evaluate_programme,
)
from src.falsification.popper import (
    FalsificationResult,
    run_falsification,
)


router = APIRouter(prefix="/api/v7/falsification", tags=["falsification"])

@router.post("/test", response_model=FalsificationResult)
async def falsify(request: dict[str, Any]) -> FalsificationResult:
    """
    Run Popperian falsification tests on a hypothesis.

    Body:
    {
        "hypothesis": "All swans are white",
        "predictions": ["swan A is white", "swan B is white", ...],
        "results": [["confirmed", 0.95], ["falsified", 0.99], ...]
    }
    """
    hypothesis = request.get("hypothesis")
    predictions = request.get("predictions", [])
    raw_results = request.get("results", [])

    if not hypothesis:
        raise HTTPException(status_code=400, detail="hypothesis is required")
    if not predictions:
        raise HTTPException(status_code=400, detail="predictions is required")
    if not raw_results:
        raise HTTPException(status_code=400, detail="results is required")
    if len(predictions) != len(raw_results):
        raise HTTPException(
            status_code=400,
            detail=f"Mismatch: {len(predictions)} predictions vs {len(raw_results)} results",
        )

    results: list[tuple[str, float]] = [(r[0], float(r[1])) for r in raw_results]

    return run_falsification(hypothesis=hypothesis, predictions=predictions, results=results)

@router.post("/evaluate", response_model=ProgrammeEvaluation)
async def evaluate(programme: dict[str, Any]) -> ProgrammeEvaluation:
    """
    Evaluate a Lakatos research programme as progressive or degenerating.

    Body:
    {
        "name": "Newtonian Mechanics",
        "hard_core": ["F=ma", "action-reaction", ...],
        "protective_belt": ["friction model", ...],
        "novel_predictions": ["planet X", ...],
        "confirmed_predictions": ["planet X", ...],
        "anomalies": ["Mercury precession", ...]
    }
    """
    required = ["name", "hard_core", "protective_belt"]
    for field in required:
        if field not in programme:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    rp = ResearchProgramme(
        name=programme["name"],
        hard_core=programme["hard_core"],
        protective_belt=programme["protective_belt"],
        novel_predictions=programme.get("novel_predictions", []),
        confirmed_predictions=programme.get("confirmed_predictions", []),
        anomalies=programme.get("anomalies", []),
    )

    return evaluate_programme(rp)

@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available falsification methods and their descriptions."""
    return {
        "methods": [
            {
                "name": "Falsification Test (Popper)",
                "endpoint": "POST /v7/falsification/test",
                "description": (
                    "Test hypotheses through risky predictions; "
                    "a single falsification refutes the hypothesis."
                ),
                "fields": ["hypothesis", "predictions", "results"],
            },
            {
                "name": "Research Programme Evaluation (Lakatos)",
                "endpoint": "POST /v7/falsification/evaluate",
                "description": (
                    "Evaluate research programmes as progressive (growing) "
                    "or degenerating (stagnating) based on novel predictions vs anomalies."
                ),
                "fields": [
                    "name",
                    "hard_core",
                    "protective_belt",
                    "novel_predictions",
                    "confirmed_predictions",
                    "anomalies",
                ],
            },
        ],
        "philosophy": "Popperian falsification + Lakatosian research programmes",
    }
