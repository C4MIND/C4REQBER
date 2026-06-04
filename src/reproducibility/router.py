"""Reproducibility API Router — /v7/reproducibility"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.reproducibility.validator import (
    compare_runs,
    compute_experiment_hash,
    validate_experiment,
    verify_result_match,
)


router = APIRouter(prefix="/api/v7/reproducibility", tags=["v7-reproducibility"])

class ValidateRequest(BaseModel):
    """ValidateRequest."""
    experiment_config: dict[str, Any]
    results: list[dict[str, Any]] = []
    expected: list[dict[str, Any]] = []
    tolerance: float = 1e-6

class CompareRequest(BaseModel):
    """CompareRequest."""
    run_a: list[dict[str, Any]]
    run_b: list[dict[str, Any]]
    tolerance: float = 1e-6

class HashRequest(BaseModel):
    """HashRequest."""
    data: Any

@router.post("/validate")
async def api_validate(request: ValidateRequest) -> dict[str, Any]:
    """Api validate."""
    report = validate_experiment(
        experiment_config=request.experiment_config,
        results=request.results,
        expected=request.expected,
        tolerance=request.tolerance,
    )
    return report.to_dict()

@router.post("/compare")
async def api_compare_runs(request: CompareRequest) -> dict[str, Any]:
    """Api compare runs."""
    if not request.run_a or not request.run_b:
        raise HTTPException(status_code=400, detail="Both run_a and run_b are required")
    return compare_runs(
        request.run_a,
        request.run_b,
        tolerance=request.tolerance,
    )

@router.post("/hash")
async def api_compute_hash(request: HashRequest) -> dict[str, Any]:
    return {
        "hash": compute_experiment_hash(request.data),
        "algorithm": "sha256",
    }

class VerifyRequest(BaseModel):
    """VerifyRequest."""
    results: list[dict[str, Any]]
    expected: list[dict[str, Any]]
    tolerance: float = 1e-6

@router.post("/verify")
async def api_verify_match(request: VerifyRequest) -> dict[str, Any]:
    """Api verify match."""
    match, detail = verify_result_match(request.results, request.expected, request.tolerance)
    return {
        "match": match,
        "detail": detail,
        "n_results": len(request.results),
        "n_expected": len(request.expected),
    }
