from __future__ import annotations


"""Simple rate limiter for c44tcdi API."""
import threading
from typing import Any
import time


class RateLimiter:
    """RateLimiter."""
    def __init__(self, max_requests: int = 60, window: int = 60) -> None:
        self.max = max_requests
        self.window = window
        self._clients: dict[str, Any] = {}
        self._lock = threading.Lock()

    def check(self, client_ip: str) -> bool:
        """Check."""
        now = time.time()
        with self._lock:
            if client_ip not in self._clients:
                self._clients[client_ip] = []
            self._clients[client_ip] = [t for t in self._clients[client_ip] if now - t < self.window]
            if len(self._clients[client_ip]) >= self.max:
                return False
            self._clients[client_ip].append(now)
            return True

discovery_limiter = RateLimiter(max_requests=10, window=60)
api_limiter = RateLimiter(max_requests=60, window=60)
