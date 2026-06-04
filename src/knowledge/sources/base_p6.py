"""
c4reqber: Base class for scientific-data REST API clients (P6 tier).

Eliminates boilerplate duplicated across NCBI, PubChem, ChEMBL,
Materials Project, NOAA, GTEx, UniProt, Kaggle, DrugBank clients.
"""
from __future__ import annotations

import logging
import time
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4reqber.knowledge.base_p6")


class ClientRegistry:
    """Global registry of active BaseP6Client instances for graceful shutdown."""

    def __init__(self) -> None:
        self._clients: set[BaseP6Client] = set()

    def add(self, client: BaseP6Client) -> None:
        self._clients.add(client)

    def remove(self, client: BaseP6Client) -> None:
        self._clients.discard(client)

    async def close_all(self) -> None:
        """Close every registered client and clear the registry."""
        clients = list(self._clients)
        self._clients.clear()
        for client in clients:
            try:
                await client.close()
            except Exception:
                logger.debug("Client close failed for %s", client, exc_info=True)


# Module-level singleton for lifespan shutdown
client_registry = ClientRegistry()



class _SimpleTTLCache:
    """In-memory cache with TTL for GET requests."""

    def __init__(self, default_ttl: float = 300.0) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any:
        if key not in self._store:
            return None
        value, expires = self._store[key]
        if time.monotonic() > expires:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        expires = time.monotonic() + (ttl or self._default_ttl)
        self._store[key] = (value, expires)

    def clear(self) -> None:
        self._store.clear()


class BaseP6Client:
    """Async REST API client with common boilerplate for scientific sources.

    Subclasses must define ``BASE_URL``.
    """

    BASE_URL: str = ""
    DEFAULT_TIMEOUT: float = 30.0
    DEFAULT_CACHE_TTL: float = 300.0  # 5 minutes

    def __init__(
        self,
        *,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: Any | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        self._client: Any = None
        self._cache = _SimpleTTLCache(default_ttl=cache_ttl or self.DEFAULT_CACHE_TTL)
        if HAS_HTTPX:
            kwargs: dict[str, Any] = {
                "timeout": timeout or self.DEFAULT_TIMEOUT,
                "headers": headers or {},
                "limits": httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                ),
            }
            if auth is not None:
                kwargs["auth"] = auth
            self._client = httpx.AsyncClient(**kwargs)
        client_registry.add(self)

    async def close(self) -> None:
        """Close the underlying HTTP client and clear cache."""
        client_registry.remove(self)
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._cache.clear()

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """GET request with error handling and optional caching."""
        if not HAS_HTTPX or self._client is None:
            raise RuntimeError("httpx not available")
        url = f"{self.BASE_URL}{path}"
        cache_key = f"GET:{url}:{sorted((params or {}).items())}" if use_cache else None
        if cache_key:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for %s", url)
                return cached
        try:
            response = await self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()
            if cache_key:
                self._cache.set(cache_key, data)
            return data
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP %d for %s: %s", e.response.status_code, url, e)
            raise
        except Exception as e:
            logger.warning("Request failed for %s: %s", url, e)
            raise

    async def _post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST request with error handling."""
        if not HAS_HTTPX or self._client is None:
            raise RuntimeError("httpx not available")
        url = f"{self.BASE_URL}{path}"
        try:
            response = await self._client.post(url, data=data, json=json)  # type: ignore[union-attr]
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP %d for %s: %s", e.response.status_code, url, e)
            raise
        except Exception as e:
            logger.warning("Request failed for %s: %s", url, e)
            raise

    @property
    def available(self) -> bool:
        """True when the HTTP client is ready."""
        return HAS_HTTPX and self._client is not None

    async def __aenter__(self) -> BaseP6Client:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
