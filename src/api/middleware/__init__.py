"""
c4-cdi-turbo API: Middleware Package
"""
from __future__ import annotations

from src.api.middleware.cors import setup_cors
from src.api.middleware.security import (
    SecurityHeadersMiddleware,
    setup_security_middleware,
)


try:
    from src.api.middleware.security import (  # type: ignore[attr-defined]
        HTTPSRedirectMiddleware,
        RequestLoggingMiddleware,
    )
except ImportError:
    HTTPSRedirectMiddleware = None
    RequestLoggingMiddleware = None


__all__ = [
    "setup_cors",
    "setup_security_middleware",
    "SecurityHeadersMiddleware",
    "RequestLoggingMiddleware",
    "HTTPSRedirectMiddleware",
]
