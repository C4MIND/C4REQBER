"""
C4REQBER API: Discovery Listings Router
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.db_manager import get_db
from src.api.dependencies import get_current_user_optional
from src.api.models import User


router = APIRouter(prefix="/api/v1/discoveries", tags=["discoveries"])


@router.get("")
async def list_discoveries(
    skip: int = 0,
    limit: int = 20,
    user: User | None = Depends(get_current_user_optional),
) -> list[dict[str, Any]]:
    """List discoveries."""
    db = await get_db()
    if user:
        discoveries = await db.get_user_discoveries(user.id, skip, limit)  # type: ignore[union-attr]
    else:
        discoveries = await db.get_all_discoveries(skip, limit)  # type: ignore[union-attr]
    return discoveries


@router.get("/{discovery_id}")
async def get_discovery(
    discovery_id: str, user: User | None = Depends(get_current_user_optional)
) -> dict[str, Any]:
    """Get discovery."""
    db = await get_db()
    discovery = await db.get_discovery(  # type: ignore[union-attr]
        discovery_id, user_id=(user.id if user else None)
    )
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    return discovery
