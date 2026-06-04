"""C4REQBER: Database Configuration.

Configuration for database connections with support for SQLite and PostgreSQL.
PostgreSQL configuration includes connection pooling settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration with connection pooling support."""

    # Connection settings
    url: str = ""

    # PostgreSQL specific (when not using URL)
    host: str = "localhost"
    port: int = 5432
    database: str = "c4_cdi_turbo"
    user: str = "c4_cdi_turbo"
    password: str = ""

    # Connection pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800  # 30 minutes
    pool_pre_ping: bool = True  # Verify connections before use

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load configuration from environment variables.

        Environment variables:
            DATABASE_URL: Full database URL (sqlite:///... or postgresql://...)
            DB_HOST: PostgreSQL host (default: localhost)
            DB_PORT: PostgreSQL port (default: 5432)
            DB_NAME: PostgreSQL database name (default: c4_cdi_turbo)
            DB_USER: PostgreSQL username (default: c4_cdi_turbo)
            DB_PASSWORD: PostgreSQL password
            POOL_SIZE: Connection pool size (default: 5)
            MAX_OVERFLOW: Max overflow connections (default: 10)
            POOL_TIMEOUT: Pool timeout in seconds (default: 30)
            POOL_RECYCLE: Connection recycle time in seconds (default: 1800)
            POOL_PRE_PING: Enable pre-ping (default: true)
        """
        # Check for DATABASE_URL first
        url = os.getenv("DATABASE_URL", "").strip()

        # Parse individual settings
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        database = os.getenv("DB_NAME", "c4_cdi_turbo")
        user = os.getenv("DB_USER", "c4_cdi_turbo")
        password = os.getenv("DB_PASSWORD", "")

        # Pool settings
        pool_size = int(os.getenv("POOL_SIZE", "5"))
        max_overflow = int(os.getenv("MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("POOL_TIMEOUT", "30"))
        pool_recycle = int(os.getenv("POOL_RECYCLE", "1800"))
        pool_pre_ping = os.getenv("POOL_PRE_PING", "true").lower() in (
            "true",
            "1",
            "yes",
        )

        return cls(
            url=url,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
        )

    def get_effective_url(self) -> str:
        """Get effective database URL.

        If DATABASE_URL is set, returns it. Otherwise constructs
        a PostgreSQL URL from individual settings.
        """
        if self.url:
            return self.url

        # Construct PostgreSQL URL from parts
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"

    def is_postgresql(self) -> bool:
        """Check if configured for PostgreSQL."""
        url = self.get_effective_url()
        return url.startswith("postgresql://") or url.startswith("postgres://")

    def is_sqlite(self) -> bool:
        """Check if configured for SQLite."""
        url = self.get_effective_url()
        return url.startswith("sqlite://")


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration (backed by DI container).

    Loads from environment on first call, then caches.
    """
    from src.di.container import get_container
    container = get_container()
    if not container.has("db_config"):
        container.register("db_config", DatabaseConfig.from_env())
    return container.resolve("db_config")


def reset_database_config() -> None:
    """Reset the global database configuration.

    Useful for testing or when environment changes.
    """
    from src.di.container import get_container
    get_container().register("db_config", None)
