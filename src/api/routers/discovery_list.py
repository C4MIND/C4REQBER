"""
C4REQBER API: Discovery Listings Router
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.db_manager import get_db
from src.api.dependencies import get_current_user
from src.api.models import User


router = APIRouter(prefix="/api/v1/discoveries", tags=["discoveries"])


@router.get("")
async def list_discoveries(
    skip: int = 0,
    limit: int = 20,
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List discoveries for the authenticated user."""
    db = await get_db()
    discoveries = await db.get_user_discoveries(user.id, skip, limit)  # type: ignore[union-attr]
    return discoveries


@router.get("/{discovery_id}")
async def get_discovery(
    discovery_id: str, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get discovery owned by the authenticated user."""
    db = await get_db()
    discovery = await db.get_discovery(  # type: ignore[union-attr]
        discovery_id, user_id=user.id
    )
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    return discovery
