"""c4reqber v5.4.0 — v8 API router aggregator."""
from __future__ import annotations

from fastapi import APIRouter

from src.api.v8_routers import (
    agenda_router,
    arxiv_router,
    discovery_router,
    exploration_router,
    knowledge_router,
    news_router,
    newton_router,
    novelty_router,
    scimatic_router,
    social_router,
    turbo_router,
    verification_router,
)


router = APIRouter(prefix="/v8", tags=["v8"])

router.include_router(knowledge_router)
router.include_router(discovery_router)
router.include_router(newton_router)
router.include_router(social_router)
router.include_router(verification_router)
router.include_router(novelty_router)
router.include_router(agenda_router)
router.include_router(exploration_router)
router.include_router(arxiv_router)
router.include_router(scimatic_router)
router.include_router(news_router)
router.include_router(turbo_router)

__all__ = ["router"]
