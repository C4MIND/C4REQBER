"""c4-cdi-turbo v8.0 API Sub-Routers
Exports all v8 sub-routers for aggregation in v8_router.py
"""
from fastapi import APIRouter

from src.api.v8_routers.agenda import router as agenda_router
from src.api.v8_routers.arxiv_v8 import router as arxiv_router
from src.api.v8_routers.discovery_v8 import router as discovery_router
from src.api.v8_routers.exploration import router as exploration_router
from src.api.v8_routers.knowledge_v8 import router as knowledge_router
from src.api.v8_routers.newton_v8 import router as newton_router
from src.api.v8_routers.novelty_v8 import router as novelty_router
from src.api.v8_routers.scimatic_v8 import router as scimatic_router
from src.api.v8_routers.social_v8 import router as social_router
from src.api.v8_routers.turbo_v8 import router as turbo_router
from src.api.v8_routers.verification_v8 import router as verification_router


try:
    from src.api.v8_routers.news_v8 import router as news_router
except Exception:
    news_router = APIRouter(prefix="/news", tags=["v8-news"])

__all__ = [
    "agenda_router",
    "arxiv_router",
    "discovery_router",
    "exploration_router",
    "knowledge_router",
    "newton_router",
    "news_router",
    "novelty_router",
    "scimatic_router",
    "social_router",
    "turbo_router",
    "verification_router",
]
