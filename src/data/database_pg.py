"""C4REQBER: PostgreSQL Database with Connection Pooling.

Async PostgreSQL support using asyncpg with SQLAlchemy 2.0+.
Provides connection pooling for production workloads.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config.db_config import DatabaseConfig, get_database_config


logger = logging.getLogger(__name__)


class PostgreSQLDatabase:
    """Async PostgreSQL database with connection pooling."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def get_async_url(self) -> str:
        """Convert PostgreSQL URL to asyncpg format.

        postgresql:// -> postgresql+asyncpg://
        """
        url = self.config.get_effective_url()
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    def create_engine(self) -> AsyncEngine:
        """Create async SQLAlchemy engine with connection pooling."""
        if self._engine is not None:
            return self._engine

        url = self.get_async_url()

        # Connection pool configuration
        engine_kwargs: dict[str, Any] = {
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
            "pool_pre_ping": self.config.pool_pre_ping,
            "echo": False,  # Set to True for SQL debugging
        }

        # Disable pooling for testing environments
        if self.config.pool_size == 0:
            engine_kwargs["poolclass"] = NullPool
            del engine_kwargs["pool_size"]
            del engine_kwargs["max_overflow"]

        try:
            self._engine = create_async_engine(url, **engine_kwargs)
            logger.info(
                f"PostgreSQL async engine created with pool_size={self.config.pool_size}, "
                f"max_overflow={self.config.max_overflow}"
            )
            return self._engine
        except (OSError, ImportError, RuntimeError) as e:
            logger.error(f"Failed to create PostgreSQL engine: {e}")
            raise

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """Get or create async session factory."""
        if self._session_maker is not None:
            return self._session_maker

        engine = self.create_engine()
        self._session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        return self._session_maker

    async def get_session(self) -> AsyncSession:
        """Get a new async database session."""
        session_maker = self.get_session_maker()
        return session_maker()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager for database sessions.

        Usage:
            async with db.session() as session:
                result = await session.execute(...)
        """
        session = await self.get_session()
        try:
            yield session
            await session.commit()
        except (OSError, RuntimeError):
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if self._engine is None:
            return False

        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except (OSError, RuntimeError) as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the database engine and all connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None
            logger.info("PostgreSQL engine closed")

    async def __aenter__(self) -> PostgreSQLDatabase:
        """Async context manager entry."""
        self.create_engine()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class SyncPostgreSQLDatabase:
    """Sync PostgreSQL database with connection pooling (for migrations/tools)."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()
        self._engine: Any | None = None

    def create_engine(self) -> Any:
        """Create sync SQLAlchemy engine with psycopg2."""
        from sqlalchemy import create_engine

        if self._engine is not None:
            return self._engine

        url = self.config.get_effective_url()

        # Ensure we're using psycopg2 driver for sync operations
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        engine_kwargs: dict[str, Any] = {
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
            "pool_pre_ping": self.config.pool_pre_ping,
        }

        if self.config.pool_size == 0:
            engine_kwargs["poolclass"] = NullPool
            del engine_kwargs["pool_size"]
            del engine_kwargs["max_overflow"]

        self._engine = create_engine(url, **engine_kwargs)
        logger.info(
            f"PostgreSQL sync engine created with pool_size={self.config.pool_size}"
        )
        return self._engine

    def close(self) -> None:
        """Close the database engine."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            logger.info("PostgreSQL sync engine closed")


def get_postgres_db(config: DatabaseConfig | None = None) -> PostgreSQLDatabase:
    """Get the global PostgreSQL async database instance (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if not container.has("pg_db"):
        container.register("pg_db", PostgreSQLDatabase(config))
    return container.resolve("pg_db")


def get_sync_postgres_db(config: DatabaseConfig | None = None) -> SyncPostgreSQLDatabase:
    """Get the global PostgreSQL sync database instance (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if not container.has("sync_pg_db"):
        container.register("sync_pg_db", SyncPostgreSQLDatabase(config))
    return container.resolve("sync_pg_db")


def reset_postgres_db() -> None:
    """Reset global PostgreSQL instances."""
    from src.di.container import get_container
    container = get_container()
    if container.has("pg_db"):
        container.register("pg_db", None)
    if container.has("sync_pg_db"):
        container.register("sync_pg_db", None)
    if container.has("pg_engine"):
        container.register("pg_engine", None)


def init_engine(config: DatabaseConfig | None = None) -> AsyncEngine:
    """Initialize the global async engine (backed by DI container)."""
    db = get_postgres_db(config)
    _engine = db.create_engine()
    from src.di.container import get_container
    get_container().register("pg_engine", _engine)
    return _engine
