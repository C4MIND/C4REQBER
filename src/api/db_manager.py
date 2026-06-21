"""
C4REQBER API: Database Layer
SQLite primary (default), PostgreSQL optional
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.compat import UTC


def _hypothesis_text(h: Any) -> str:
    """Extract hypothesis text whether input is str or dict."""
    if isinstance(h, str):
        return h
    if isinstance(h, dict):
        return str(h.get("hypothesis", h.get("text", "")))
    return str(h)


def _hypothesis_field(h: Any, key: str, default: Any) -> Any:
    """Extract a field from a hypothesis that may be str or dict."""
    if isinstance(h, dict):
        return h.get(key, default)
    return default


# Optional PostgreSQL support
try:
    import asyncpg

    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    asyncpg = None


DB_PATH = Path(__file__).parent.parent.parent / "data" / "c4_cdi_turbo.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    problem TEXT NOT NULL,
    top_hypothesis TEXT,
    duration_seconds REAL DEFAULT 0,
    estimated_cost REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    validation_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discovery_id INTEGER NOT NULL,
    hypothesis_text TEXT NOT NULL,
    confidence REAL DEFAULT 0,
    method TEXT,
    c4_path TEXT,
    triz_principles TEXT,
    FOREIGN KEY (discovery_id) REFERENCES discoveries(id)
);

CREATE INDEX IF NOT EXISTS idx_discoveries_user ON discoveries(user_id);
CREATE INDEX IF NOT EXISTS idx_discoveries_status ON discoveries(status);
"""


class SQLiteDatabase:
    """SQLite async database manager."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite schema."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(SQLITE_SCHEMA)
            conn.commit()

    def _connection(self) -> Any:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    async def connect(self) -> None:
        """No-op for interface parity with PostgresDatabase. SQLite opens a
        fresh connection per call (see _connection); there is no pool to open."""
        return None

    async def disconnect(self) -> None:
        """No-op for interface parity with PostgresDatabase. Without this the
        lifespan shutdown (`await db.disconnect()`) raised AttributeError on
        every shutdown for the SQLite path."""
        return None

    async def ping(self) -> bool:
        try:
            with self._connection() as conn:
                conn.execute("SELECT 1")
            return True
        except (sqlite3.Error, OSError):
            return False

    async def save_discovery(self, result: Any, user_id: str | None) -> str:
        """Save discovery."""
        problem = (
            result.get("problem") if isinstance(result, dict) else getattr(result, "problem", "")
        )
        hypotheses = (
            result.get("hypotheses", [])
            if isinstance(result, dict)
            else getattr(result, "hypotheses", [])
        )
        duration = (
            result.get("duration_seconds", 0.0)
            if isinstance(result, dict)
            else getattr(result, "duration_seconds", 0.0)
        )
        cost = (
            result.get("estimated_cost_usd", 0.0)
            if isinstance(result, dict)
            else getattr(result, "estimated_cost_usd", 0.0)
        )

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO discoveries (user_id, problem, top_hypothesis, duration_seconds, estimated_cost, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    problem,
                    _hypothesis_text(hypotheses[0]) if hypotheses else None,
                    duration,
                    cost,
                    datetime.now(UTC),
                ),
            )
            discovery_id = cursor.lastrowid

            for h in hypotheses:
                conn.execute(
                    """
                    INSERT INTO hypotheses (discovery_id, hypothesis_text, confidence, method, c4_path, triz_principles)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        discovery_id,
                        _hypothesis_text(h),
                        _hypothesis_field(h, "confidence", 0.0),
                        _hypothesis_field(h, "method", ""),
                        ",".join(_hypothesis_field(h, "c4_path", [])),
                        ",".join(map(str, _hypothesis_field(h, "triz_principles", []))),
                    ),
                )
            conn.commit()
            return str(discovery_id)

    async def get_discovery(self, discovery_id: str, user_id: str | None = None) -> dict | None:  # type: ignore[type-arg]
        with self._connection() as conn:
            query = "SELECT * FROM discoveries WHERE id = ?"
            params = [discovery_id]
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    async def get_user_discoveries(self, user_id: str, skip: int, limit: int) -> list[dict]:  # type: ignore[type-arg]
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM discoveries WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, skip),
            ).fetchall()
            return [dict(r) for r in rows]

    async def get_all_discoveries(self, skip: int, limit: int) -> list[dict]:  # type: ignore[type-arg]
        """Get all discoveries."""
        limit = min(max(limit, 0), 100)
        skip = max(skip, 0)
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM discoveries ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, skip),
            ).fetchall()
            return [dict(r) for r in rows]

    async def update_discovery_status(
        self, discovery_id: str, status: str, notes: str | None, user_id: str
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE discoveries SET status = ?, validation_notes = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (status, notes, datetime.now(UTC), discovery_id, user_id),
            )
            conn.commit()

    async def count_discoveries(self) -> int:
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM discoveries").fetchone()
            return row[0] if row else 0

    async def count_hypotheses(self) -> int:
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()
            return row[0] if row else 0

    async def count_active_experiments(self) -> int:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM discoveries WHERE status = 'running'"
            ).fetchone()
            return row[0] if row else 0

    async def get_validation_rate(self) -> float:
        with self._connection() as conn:
            total_row = conn.execute("SELECT COUNT(*) FROM discoveries").fetchone()
            total = total_row[0] if total_row else 0
            if total == 0:
                return 0.0
            val_row = conn.execute(
                "SELECT COUNT(*) FROM discoveries WHERE status IN ('validated', 'falsified')"
            ).fetchone()
            validated = val_row[0] if val_row else 0
            return validated / total

    async def get_avg_confidence(self) -> float:
        with self._connection() as conn:
            row = conn.execute("SELECT COALESCE(AVG(confidence), 0) FROM hypotheses").fetchone()
            return row[0] if row else 0.0


class PostgresDatabase:
    """PostgreSQL async database manager (production path)."""

    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL", "postgresql://localhost/c4_cdi_turbo"),
            min_size=2,
            max_size=20,
            command_timeout=30,
        )

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def ping(self) -> bool:
        if self.pool is None:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except (OSError, RuntimeError):
            return False

    async def save_discovery(self, result: Any, user_id: str | None) -> str:
        problem = (
            result.get("problem") if isinstance(result, dict) else getattr(result, "problem", "")
        )
        hypotheses = (
            result.get("hypotheses", [])
            if isinstance(result, dict)
            else getattr(result, "hypotheses", [])
        )
        duration = (
            result.get("duration_seconds", 0.0)
            if isinstance(result, dict)
            else getattr(result, "duration_seconds", 0.0)
        )
        cost = (
            result.get("estimated_cost_usd", 0.0)
            if isinstance(result, dict)
            else getattr(result, "estimated_cost_usd", 0.0)
        )
        top_hyp = _hypothesis_text(hypotheses[0]) if hypotheses else None

        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            discovery_id = await conn.fetchval(
                """
                INSERT INTO discoveries (
                    user_id, problem, top_hypothesis, duration_seconds,
                    estimated_cost, created_at, updated_at
                )
                VALUES ($1::uuid, $2, $3, $4, $5, $6, $6)
                RETURNING id::text
                """,
                user_id,
                problem,
                top_hyp,
                duration,
                cost,
                datetime.now(UTC),
            )
            for h in hypotheses:
                c4_path = _hypothesis_field(h, "c4_path", [])
                triz = _hypothesis_field(h, "triz_principles", [])
                await conn.execute(
                    """
                    INSERT INTO hypotheses (
                        discovery_id, hypothesis_text, confidence, method,
                        c4_path, triz_principles
                    )
                    VALUES ($1::uuid, $2, $3, $4, $5, $6)
                    """,
                    discovery_id,
                    _hypothesis_text(h),
                    _hypothesis_field(h, "confidence", 0.0),
                    _hypothesis_field(h, "method", ""),
                    c4_path if isinstance(c4_path, list) else [],
                    triz if isinstance(triz, list) else [],
                )
            return str(discovery_id)

    async def get_discovery(self, discovery_id: str, user_id: str | None = None) -> dict | None:  # type: ignore[type-arg]
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            if user_id:
                row = await conn.fetchrow(
                    "SELECT * FROM discoveries WHERE id = $1::uuid AND user_id = $2::uuid",
                    discovery_id,
                    user_id,
                )
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM discoveries WHERE id = $1::uuid",
                    discovery_id,
                )
            return dict(row) if row else None

    async def get_user_discoveries(self, user_id: str, skip: int, limit: int) -> list[dict]:  # type: ignore[type-arg]
        limit = min(max(limit, 0), 100)
        skip = max(skip, 0)
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            rows = await conn.fetch(
                """
                SELECT * FROM discoveries
                WHERE user_id = $1::uuid
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                skip,
            )
            return [dict(r) for r in rows]

    async def get_all_discoveries(self, skip: int, limit: int) -> list[dict]:  # type: ignore[type-arg]
        limit = min(max(limit, 0), 100)
        skip = max(skip, 0)
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            rows = await conn.fetch(
                "SELECT * FROM discoveries ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit,
                skip,
            )
            return [dict(r) for r in rows]

    async def update_discovery_status(
        self, discovery_id: str, status: str, notes: str | None, user_id: str
    ) -> None:
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            await conn.execute(
                """
                UPDATE discoveries
                SET status = $1, validation_notes = $2, updated_at = $3
                WHERE id = $4::uuid AND user_id = $5::uuid
                """,
                status,
                notes,
                datetime.now(UTC),
                discovery_id,
                user_id,
            )

    async def count_discoveries(self) -> int:
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            val = await conn.fetchval("SELECT COUNT(*) FROM discoveries")
            return int(val or 0)

    async def count_hypotheses(self) -> int:
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            val = await conn.fetchval("SELECT COUNT(*) FROM hypotheses")
            return int(val or 0)

    async def count_active_experiments(self) -> int:
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            val = await conn.fetchval(
                "SELECT COUNT(*) FROM discoveries WHERE status = 'running'"
            )
            return int(val or 0)

    async def get_validation_rate(self) -> float:
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            total = await conn.fetchval("SELECT COUNT(*) FROM discoveries")
            if not total:
                return 0.0
            validated = await conn.fetchval(
                "SELECT COUNT(*) FROM discoveries WHERE status IN ('validated', 'falsified')"
            )
            return float(validated or 0) / float(total)

    async def get_avg_confidence(self) -> float:
        async with self.pool.acquire() as conn:  # type: ignore[union-attr]
            val = await conn.fetchval("SELECT COALESCE(AVG(confidence), 0) FROM hypotheses")
            return float(val or 0.0)


# Unified database interface
_db_instance: SQLiteDatabase | PostgresDatabase | None = None
_db_lock = asyncio.Lock()


async def get_db() -> SQLiteDatabase | PostgresDatabase:
    """Get database instance (SQLite default, PostgreSQL optional)."""
    global _db_instance
    if _db_instance is None:
        async with _db_lock:
            if _db_instance is None:
                db_url = os.getenv("DATABASE_URL", "")
                if db_url.startswith("postgresql://") and HAS_POSTGRES:
                    _db_instance = PostgresDatabase()
                    await _db_instance.connect()
                else:
                    _db_instance = SQLiteDatabase()
    return _db_instance
