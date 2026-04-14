"""
TURBO-CDI v8.4 Production API Main Entry Point
Complete enterprise-grade web server with all features.
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from pathlib import Path

from turbo_cdi.presentation.api.routes import (
    corpus_router,
    discovery_router,
    health_router,
    system_router,
    auth_router,
)
from turbo_cdi.presentation.api.exceptions import (
    http_exception_handler,
    api_error_handler,
    global_exception_handler,
)
from turbo_cdi.presentation.api.schemas import APIError, ErrorResponse
from turbo_cdi.presentation.websocket import router as websocket_router
from turbo_cdi.infrastructure.config.container import Container

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI application
app = FastAPI(
    title="TURBO-CDI v8.4 - Cognitive Discovery Intelligence",
    description="Enterprise Cognitive Operating System for Transformational Knowledge Discovery",
    version="8.4.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: configure specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(corpus_router, prefix="/api/v1/corpora", tags=["Corpus Management"])
app.include_router(discovery_router, prefix="/api/v1/discovery", tags=["Knowledge Discovery"])
app.include_router(health_router, prefix="/api/v1/health", tags=["Health & Monitoring"])
app.include_router(system_router, prefix="/api/v1/system", tags=["System Operations"])
app.include_router(websocket_router, tags=["WebSocket"])

# Templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 TURBO-CDI v8.4 Production API starting up...")

    # Create and store container
    container = Container()
    app.state.container = container

    logger.info("✅ Application initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger = logging.getLogger(__name__)
    logger.info("🛑 TURBO-CDI v8.4 API shutting down...")
    logger.info("✅ Application shutdown complete")


@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    """Production homepage with system status"""
    container = getattr(request.app.state, "container", None)

    # Get basic system info
    system_info = {
        "version": "8.4.0",
        "status": "production_ready",
        "architecture": "Clean Hexagonal",
        "features": [
            "Cognitive Discovery Intelligence",
            "Clean Architecture CQRS",
            "Real-time Processing",
            "Enterprise Security",
            "Production Monitoring",
        ],
    }

    # Try to get health status
    try:
        if container:
            from turbo_cdi.infrastructure.health import HealthChecker

            health_checker = HealthChecker(container)
            health_data = await health_checker.check_all()
            system_info["health"] = health_data.get("overall_health", "unknown")
        else:
            system_info["health"] = "initializing"
    except Exception:
        system_info["health"] = "unknown"

    return templates.TemplateResponse(
        "index.html", {"request": request, "system_info": system_info}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Interactive dashboard for real-time monitoring"""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "title": "TURBO-CDI Dashboard"}
    )


# API info endpoint
@app.get("/api/v1/info")
async def api_info():
    """Comprehensive API information"""
    return {
        "name": "TURBO-CDI v8.4",
        "version": "8.4.0",
        "description": "Cognitive Discovery Intelligence Platform",
        "architecture": "Clean Hexagonal CQRS",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "corpus_management": "/api/v1/corpora",
            "discovery": "/api/v1/discovery",
            "health": "/api/v1/health",
            "system": "/api/v1/system",
            "websocket": "/discovery/{client_id}",
        },
        "documentation": {
            "swagger_ui": "/api/v1/docs",
            "redoc": "/api/v1/redoc",
            "openapi_json": "/api/v1/openapi.json",
        },
        "features": [
            "JWT Authentication",
            "Role-Based Access Control",
            "Knowledge Corpus Management",
            "Anomaly Detection",
            "Cognitive Transformations",
            "Real-time Monitoring",
            "Health Checks",
        ],
    }
