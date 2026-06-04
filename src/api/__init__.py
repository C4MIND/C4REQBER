"""
c4-cdi-turbo API: Module Initialization
"""

from __future__ import annotations

from .auth import AuthManager
from .cache import CacheManager
from .db_manager import get_db
from .models import (
    DiscoveryRequest,
    DiscoveryResponse,
    HealthResponse,
    HypothesisResponse,
    MetricsResponse,
    SearchRequest,
    SearchResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    ValidationRequest,
    WebSocketMessage,
)
from .rate_limiter import RateLimiter, WebSocketRateLimiter
from .websocket import ConnectionManager


__all__ = [
    "HealthResponse",
    "MetricsResponse",
    "UserCreate",
    "UserResponse",
    "TokenResponse",
    "DiscoveryRequest",
    "DiscoveryResponse",
    "HypothesisResponse",
    "SearchRequest",
    "SearchResponse",
    "ValidationRequest",
    "WebSocketMessage",
    "get_db",
    "AuthManager",
    "CacheManager",
    "RateLimiter",
    "WebSocketRateLimiter",
    "ConnectionManager",
]
