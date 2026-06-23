"""
C4REQBER API: FastAPI Server
Production-ready REST API with structured logging, security, and health endpoints.
"""
from __future__ import annotations

import os
from pathlib import Path


# Load .env file before anything else
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent.parent
    _env_path = _root / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
    # Explicit opt-in: load .env.dontredact for additional API keys
    _dontredact_path = _root / ".env.dontredact"
    if _dontredact_path.exists():
        load_dotenv(_dontredact_path, override=False)
except ImportError:
    pass

import uvicorn
from fastapi import FastAPI

from src import __version__
from src.api.lifespan import lifespan
from src.api.middleware.security import setup_security_middleware
from src.api.routers import (
    auth,
    bridge,
    discoveries,
    discovery_list,
    graph,
    health,
    metrics,
    patterns,
    search,
    theorems,
    validation_single,
    validations,
    websocket,
)

# Import structured logging
from src.core.logging import configure_logging, get_logger, get_request_id_middleware


# Configure logging on startup
configure_logging()
logger = get_logger(__name__)


_env = os.getenv("ENV", "development")
_docs_url = "/docs" if _env != "production" else None
_redoc_url = "/redoc" if _env != "production" else None

app = FastAPI(
    title="c4reqber API",
    description="Cognitive Exoskeleton for AI Agents — Scientific Hypothesis Generation Platform",
    version=__version__,
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# Register centralized error handlers
from src.api.errors import register_error_handlers


register_error_handlers(app)

# Add request ID middleware for structured logging
app.middleware("http")(get_request_id_middleware())

# CORS is mounted once, inside setup_security_middleware (it previously also ran
# via a second, byte-identical setup_cors(app) call — the duplicate is removed).
setup_security_middleware(app)

logger.info("api_server_initializing", env=_env, version=__version__)

# Include routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(auth.router)
app.include_router(discoveries.router)
app.include_router(discovery_list.router)
app.include_router(search.router)
app.include_router(patterns.router)
app.include_router(bridge.router)
app.include_router(theorems.router)
app.include_router(graph.router)
app.include_router(validations.router)
app.include_router(validation_single.router)
app.include_router(websocket.router)

# Include v1 routers
from src.api.agents_router import router as agents_router
from src.api.v8_router import router as v8_router


app.include_router(agents_router)
app.include_router(v8_router)



if __name__ == "__main__":
    uvicorn.run(
        "src.api.server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1")),
    )
