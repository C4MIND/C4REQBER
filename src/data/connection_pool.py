"""C4REQBER: Connection Pool Management.

SQLAlchemy connection pool configuration with health checks
and monitoring for PostgreSQL databases.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool


logger = logging.getLogger(__name__)

@dataclass
class PoolHealth:
    """Connection pool health metrics."""

    size: int
    checked_in: int
    checked_out: int
    overflow: int
    is_healthy: bool
    response_time_ms: float

class ConnectionPool:
    """SQLAlchemy connection pool manager with health checks."""

    def __init__(
        self,
        url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
        echo: bool = False,
    ) -> None:
        self.url = url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self._engine: Engine | None = None
        self._pool_stats: dict[str, Any] = {}

        # Convert URL for asyncpg if needed
        if url.startswith("postgresql://"):
            self._async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            self._async_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        else:
            self._async_url = url

        # Create the engine
        self._create_engine(echo)

    def _create_engine(self, echo: bool = False) -> Engine:
        """Create SQLAlchemy engine with connection pooling."""
        engine_kwargs: dict[str, Any] = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": echo,
        }

        # Disable pooling for testing
        if self.pool_size == 0:
            engine_kwargs["poolclass"] = NullPool
            del engine_kwargs["pool_size"]
            del engine_kwargs["max_overflow"]

        self._engine = create_engine(self.url, **engine_kwargs)
        logger.info(
            f"Connection pool created: pool_size={self.pool_size}, "
            f"max_overflow={self.max_overflow}"
        )
        return self._engine

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine."""
        if self._engine is None:
            raise RuntimeError("Connection pool not initialized")
        return self._engine

    def get_pool_status(self) -> dict[str, Any]:
        """Get current pool status."""
        if self._engine is None:
            return {"status": "not_initialized"}

        pool = self._engine.pool
        return {
            "size": pool.size(),  # type: ignore[attr-defined]
            "checked_in": pool.checkedin(),  # type: ignore[attr-defined]
            "checked_out": pool.checkedout(),  # type: ignore[attr-defined]
            "overflow": pool.overflow(),  # type: ignore[attr-defined]
            "max_overflow": self.max_overflow,
        }

    def health_check(self) -> PoolHealth:
        """Perform health check on the connection pool.

        Returns:
            PoolHealth: Health metrics including response time
        """
        start_time = time.time()
        is_healthy = False

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                is_healthy = result.scalar() == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            is_healthy = False

        response_time_ms = (time.time() - start_time) * 1000
        status = self.get_pool_status()

        health = PoolHealth(
            size=status.get("size", 0),
            checked_in=status.get("checked_in", 0),
            checked_out=status.get("checked_out", 0),
            overflow=status.get("overflow", 0),
            is_healthy=is_healthy,
            response_time_ms=round(response_time_ms, 2),
        )

        if not is_healthy:
            logger.warning(f"Pool health check failed: {health}")

        return health

    @contextmanager  # type: ignore[arg-type]
    def get_connection(self) -> None:  # type: ignore[misc]
        """Get a database connection from the pool.

        Usage:
            with pool.get_connection() as conn:
                result = conn.execute(...)
        """
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def close(self) -> None:
        """Close the connection pool and all connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            logger.info("Connection pool closed")

    def __enter__(self) -> ConnectionPool:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

class AsyncConnectionPool:
    """Async connection pool manager using asyncpg."""

    def __init__(
        self,
        url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
    ) -> None:
        self.url = url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self._engine: Any | None = None

        # Convert URL for asyncpg
        if url.startswith("postgresql://"):
            self._async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            self._async_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        else:
            self._async_url = url

    async def create_engine(self) -> Any:
        """Create async SQLAlchemy engine."""
        from sqlalchemy.ext.asyncio import create_async_engine

        if self._engine is not None:
            return self._engine

        engine_kwargs: dict[str, Any] = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
        }

        if self.pool_size == 0:
            from sqlalchemy.pool import NullPool
            engine_kwargs["poolclass"] = NullPool
            del engine_kwargs["pool_size"]
            del engine_kwargs["max_overflow"]

        self._engine = create_async_engine(self._async_url, **engine_kwargs)
        logger.info("Async connection pool created")
        return self._engine

    async def health_check(self) -> PoolHealth:
        """Perform async health check."""
        from sqlalchemy import text

        start_time = time.time()
        is_healthy = False

        try:
            engine = await self.create_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                is_healthy = result.scalar() == 1
        except Exception as e:
            logger.error(f"Async health check failed: {e}")
            is_healthy = False

        response_time_ms = (time.time() - start_time) * 1000

        # Get pool stats if available
        size = checked_in = checked_out = overflow = 0
        if self._engine and hasattr(self._engine.pool, "size"):
            pool = self._engine.pool
            size = pool.size()
            checked_in = pool.checkedin()
            checked_out = pool.checkedout()
            overflow = pool.overflow()

        return PoolHealth(
            size=size,
            checked_in=checked_in,
            checked_out=checked_out,
            overflow=overflow,
            is_healthy=is_healthy,
            response_time_ms=round(response_time_ms, 2),
        )

    async def close(self) -> None:
        """Close async connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            logger.info("Async connection pool closed")

# Convenience factory functions

def create_pool_from_config(config: Any) -> ConnectionPool:
    """Create connection pool from database config."""
    url = config.get_effective_url() if hasattr(config, "get_effective_url") else str(config)
    return ConnectionPool(
        url=url,
        pool_size=getattr(config, "pool_size", 5),
        max_overflow=getattr(config, "max_overflow", 10),
        pool_timeout=getattr(config, "pool_timeout", 30),
        pool_recycle=getattr(config, "pool_recycle", 1800),
        pool_pre_ping=getattr(config, "pool_pre_ping", True),
    )

def create_async_pool_from_config(config: Any) -> AsyncConnectionPool:
    """Create async connection pool from database config."""
    url = config.get_effective_url() if hasattr(config, "get_effective_url") else str(config)
    return AsyncConnectionPool(
        url=url,
        pool_size=getattr(config, "pool_size", 5),
        max_overflow=getattr(config, "max_overflow", 10),
        pool_timeout=getattr(config, "pool_timeout", 30),
        pool_recycle=getattr(config, "pool_recycle", 1800),
        pool_pre_ping=getattr(config, "pool_pre_ping", True),
    )
