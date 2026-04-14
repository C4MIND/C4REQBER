"""
Main API routes aggregation module.
Imports and combines all route modules.
"""

from turbo_cdi.presentation.api.routes.corpus_routes import router as corpus_router
from turbo_cdi.presentation.api.routes.discovery_routes import router as discovery_router
from turbo_cdi.presentation.api.routes.health_routes import router as health_router
from turbo_cdi.presentation.api.routes.system_routes import router as system_router
from turbo_cdi.presentation.api.routes.auth_routes import router as auth_router

__all__ = [
    "corpus_router",
    "discovery_router",
    "health_router",
    "system_router",
    "auth_router",
]
