"""
C4REQBER API: Validation Router
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_current_user
from src.api.models import (
    ObservationData,
    User,
    ValidationExperimentCreate,
    ValidationExperimentResponse,
    ValidationRequest,
)
from src.compat import UTC
from src.memory.bank import StructuralMemoryBank


router = APIRouter(prefix="/api/v1/validations", tags=["validations"])

_validation_bank = StructuralMemoryBank()
_validation_lock = asyncio.Lock()


@router.post("", response_model=ValidationExperimentResponse)
async def create_validation(
    request: ValidationExperimentCreate,
    user: User = Depends(get_current_user),
) -> ValidationExperimentResponse:
    """Create validation."""
    exp_id = f"val_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC).isoformat()
    exp: Any = {
        "id": exp_id,
        "user_id": user.id,
        "hypothesis_id": request.hypothesis_id,
        "name": request.name or f"Experiment {exp_id}",
        "method": request.method or "simulation",
        "status": "draft",
        "observations": [],
        "conclusion": None,
        "started_at": now,
        "completed_at": None,
    }
    async with _validation_lock:
        await _validation_bank.create_validation_async(exp)  # type: ignore[attr-defined]
    return ValidationExperimentResponse(**exp)  # type: ignore[arg-type, unused-ignore]


@router.get("", response_model=list[ValidationExperimentResponse])
async def list_validations(
    user: User = Depends(get_current_user),
) -> list[ValidationExperimentResponse]:
    """List validations."""
    exps = await _validation_bank.list_validations_async(user_id=user.id)  # type: ignore[attr-defined]
    return [ValidationExperimentResponse(**exp) for exp in exps]


@router.get("/{validation_id}", response_model=ValidationExperimentResponse)
async def get_validation(
    validation_id: str, user: User = Depends(get_current_user)
) -> ValidationExperimentResponse:
    """Get validation."""
    exp = await _validation_bank.get_validation_async(  # type: ignore[attr-defined]
        validation_id, user_id=user.id
    )
    if not exp:
        raise HTTPException(
            status_code=404, detail="Validation experiment not found"
        )
    return ValidationExperimentResponse(**exp)


@router.post("/{validation_id}/observations")
async def add_observation(
    validation_id: str,
    request: ObservationData,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add observation."""
    async with _validation_lock:
        exp = await _validation_bank.get_validation_async(  # type: ignore[attr-defined]
            validation_id, user_id=user.id
        )
        if not exp:
            raise HTTPException(
                status_code=404, detail="Validation experiment not found"
            )
        obs = {
            "id": f"obs_{len(exp['observations']) + 1}",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": request.data,
            "notes": request.notes,
        }
        observations = exp["observations"]
        observations.append(obs)
        status = exp["status"]
        if status == "draft":
            status = "running"
        await _validation_bank.update_validation_async(  # type: ignore[attr-defined]
            validation_id,
            {"observations": observations, "status": status},
            user_id=user.id,
        )
    return {"status": "success", "observation": obs}


@router.post("/{validation_id}/conclude")
async def conclude_validation(
    validation_id: str,
    request: ValidationRequest,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Conclude validation."""
    async with _validation_lock:
        exp = await _validation_bank.get_validation_async(  # type: ignore[attr-defined]
            validation_id, user_id=user.id
        )
        if not exp:
            raise HTTPException(
                status_code=404, detail="Validation experiment not found"
            )
        updated = await _validation_bank.update_validation_async(  # type: ignore[attr-defined]
            validation_id,
            {
                "status": "completed",
                "conclusion": request.outcome,
                "completed_at": datetime.now(UTC).isoformat(),
            },
            user_id=user.id,
        )
        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Validation experiment not found or access denied",
            )
        exp = await _validation_bank.get_validation_async(  # type: ignore[attr-defined]
            validation_id, user_id=user.id
        )
    return {"status": "success", "experiment": ValidationExperimentResponse(**exp)}
