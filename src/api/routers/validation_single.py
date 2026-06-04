"""
C4REQBER API: Validation Router (single /validate endpoint)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from src.api.db_manager import get_db
from src.api.dependencies import get_current_user
from src.api.models import User, ValidationRequest


router = APIRouter(prefix="/api/v1/validation", tags=["validation"])


@router.post("/validate/{discovery_id}")
async def validate_hypothesis(
    discovery_id: str,
    request: ValidationRequest,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Validate hypothesis."""
    db = await get_db()
    await db.update_discovery_status(  # type: ignore[union-attr]
        discovery_id=discovery_id,
        status=request.outcome,
        notes=request.notes,
        user_id=user.id,
    )
    return {"status": "success", "discovery_id": discovery_id}
