"""
C4REQBER API: Theorem Router
"""
from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter, HTTPException

from src.theorem.prover import get_theorem_prover


router = APIRouter(prefix="/api/v1/theorems", tags=["theorems"])


@router.post("")
async def formalize_hypothesis(payload: dict[str, Any]) -> dict[str, Any]:
    """Formalize hypothesis."""
    backend = payload.get("backend", "simulation")
    if not isinstance(backend, str) or len(backend) > 50:
        raise HTTPException(status_code=400, detail="Invalid backend parameter")
    prover = get_theorem_prover(backend)
    hypothesis_id = payload.get(
        "hypothesis_id",
        f"h-{hashlib.md5(payload.get('hypothesis', '').encode()).hexdigest()[:16]}",
    )
    hypothesis = payload.get("hypothesis", "")
    domain = payload.get("domain", "general")

    if not hypothesis:
        raise HTTPException(status_code=400, detail="hypothesis required")

    theorem = await prover.formalize_hypothesis(hypothesis_id, hypothesis, domain)
    return {
        "id": theorem.id,
        "hypothesis_id": theorem.hypothesis_id,
        "statement": theorem.statement,
        "formal_statement": theorem.formal_statement,
        "backend": theorem.backend.value,
        "status": theorem.status.value,
        "confidence": theorem.confidence,
        "created_at": theorem.created_at,
    }


@router.get("")
async def list_theorems() -> list[dict[str, Any]]:
    """List theorems."""
    prover = get_theorem_prover()
    theorems = prover.list_theorems()
    return [
        {
            "id": t.id,
            "hypothesis_id": t.hypothesis_id,
            "statement": t.statement,
            "status": t.status.value,
            "backend": t.backend.value,
            "confidence": t.confidence,
            "created_at": t.created_at,
            "proved_at": t.proved_at,
        }
        for t in theorems
    ]


@router.get("/stats")
async def theorem_statistics() -> dict[str, Any]:
    """Theorem statistics."""
    prover = get_theorem_prover()
    return prover.get_statistics()


@router.get("/{theorem_id}")
async def get_theorem(theorem_id: str) -> dict[str, Any]:
    """Get theorem."""
    prover = get_theorem_prover()
    theorem = prover.get_theorem(theorem_id)
    if not theorem:
        raise HTTPException(status_code=404, detail="Theorem not found")
    return {
        "id": theorem.id,
        "hypothesis_id": theorem.hypothesis_id,
        "statement": theorem.statement,
        "formal_statement": theorem.formal_statement,
        "backend": theorem.backend.value,
        "status": theorem.status.value,
        "proof_steps": [
            {
                "id": s.id,
                "tactic": s.tactic,
                "goal_before": s.goal_before,
                "goal_after": s.goal_after,
                "justification": s.justification,
                "line_number": s.line_number,
            }
            for s in theorem.proof_steps
        ],
        "error_message": theorem.error_message,
        "confidence": theorem.confidence,
        "created_at": theorem.created_at,
        "proved_at": theorem.proved_at,
    }


@router.post("/{theorem_id}/prove")
async def prove_theorem(theorem_id: str) -> dict[str, Any]:
    """Prove theorem."""
    prover = get_theorem_prover()
    theorem = prover.get_theorem(theorem_id)
    if not theorem:
        raise HTTPException(status_code=404, detail="Theorem not found")

    result = await prover.attempt_proof(theorem_id)
    return {
        "id": result.id,
        "status": result.status.value,
        "proof_steps": [
            {
                "id": s.id,
                "tactic": s.tactic,
                "goal_before": s.goal_before,
                "goal_after": s.goal_after,
                "justification": s.justification,
            }
            for s in result.proof_steps
        ],
        "error_message": result.error_message,
        "proved_at": result.proved_at,
    }
