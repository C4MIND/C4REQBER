"""
C4REQBER API: CORS Middleware Setup
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware with allowlist."""
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8000",
    ).split(",")
    allowed_origins = [o.strip() for o in allowed_origins if o.strip()]

    if os.getenv("ENV") == "production":
        allowed_origins = [o for o in allowed_origins if o != "*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Trace-ID", "X-API-Key"],
        expose_headers=["X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=600,
    )
