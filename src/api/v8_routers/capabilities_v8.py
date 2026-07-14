"""v8 simulations capabilities — engine + verifier probe for TUI overlay."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.simulations.capabilities_probe import probe_capabilities


router = APIRouter(prefix="/simulations", tags=["v8-simulations"])


@router.get("/capabilities")
async def get_capabilities() -> dict[str, Any]:
    """Return simulation engines + formal verifiers available on this host.

    Consumed by TUI v9 capsim overlay (Ctrl+Shift+C).
    """
    return probe_capabilities().to_dict()
