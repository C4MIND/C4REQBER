"""
FastAPI application for TURBO-CDI v8.4
Production-ready REST API with OpenAPI documentation.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Optional

from turbo_cdi.infrastructure.config import Settings
from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.presentation.api.routes import (
    corpus_router,
    discovery_router,
    health_router,
    system_router,
    auth_router,
)
from turbo_cdi.presentation.api.dependencies import get_container
from turbo_cdi.presentation.api.exceptions import (
    http_exception_handler,
    validation_exception_handler,
)
from turbo_cdi.presentation.api.middleware import (
    RequestTimingMiddleware,
    ExceptionHandlingMiddleware,
    LoggingMiddleware,
)


# Create FastAPI application
app = FastAPI(
    title="TURBO-CDI v8.4",
    description="Cognitive Discovery Intelligence - Enterprise Knowledge Processing Platform",
    version="8.4.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Add custom middleware
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(ExceptionHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler_v2)
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
app.include_router(
    corpus_router,
    prefix="/api/v1/corpora",
    tags=["Corpus Management"],
)
app.include_router(
    discovery_router,
    prefix="/api/v1/discovery",
    tags=["Knowledge Discovery"],
)
app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["Health & Monitoring"],
)
app.include_router(
    system_router,
    prefix="/api/v1/system",
    tags=["System Operations"],
)

# WebSocket support
from turbo_cdi.presentation.websocket import router as websocket_router

app.include_router(
    websocket_router,
    tags=["WebSocket"],
)
app.include_router(
    discovery_router,
    prefix="/api/v1/discovery",
    tags=["Knowledge Discovery"],
)
app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["Health & Monitoring"],
)
app.include_router(
    system_router,
    prefix="/api/v1/system",
    tags=["System Operations"],
)

# WebSocket support
from turbo_cdi.presentation.websocket import router as websocket_router

app.include_router(
    websocket_router,
    tags=["WebSocket"],
)


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="TURBO-CDI v8.4 API",
        version="8.4.0",
        description="Enterprise Cognitive Discovery Intelligence Platform API",
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 TURBO-CDI v8.4 API starting up...")

    # Initialize container with settings
    container = Container()
    app.state.container = container

    logger.info("✅ Application initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger = logging.getLogger(__name__)
    logger.info("🛑 TURBO-CDI v8.4 API shutting down...")

    # Clean up resources if needed
    logger.info("✅ Application shutdown complete")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": "TURBO-CDI v8.4",
        "description": "Cognitive Discovery Intelligence Platform",
        "version": "8.4.0",
        "documentation": {
            "swagger_ui": "/api/v1/docs",
            "redoc": "/api/v1/redoc",
            "openapi_json": "/api/v1/openapi.json",
        },
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    settings = Settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode,
        log_level="info" if settings.debug_mode else "warning",
    )
