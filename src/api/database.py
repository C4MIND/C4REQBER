"""
TURBO-CDI API: Database Layer
PostgreSQL async operations
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg


class Database:
    """Async PostgreSQL database manager."""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """Create connection pool."""
        self.pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL", "postgresql://localhost/turbo_cdi"),
            min_size=5,
            max_size=20,
        )

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

    async def ping(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except (asyncpg.PostgresError, ConnectionError, OSError) as e:
            return False

    # ═══════════════════════════════════════════════════════════════
    # DISCOVERY OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    async def save_discovery(self, result: Any, user_id: str) -> str:
        """Save discovery result."""
        async with self.pool.acquire() as conn:
            discovery_id = await conn.fetchval(
                """
                INSERT INTO discoveries 
                (user_id, problem, top_hypothesis, duration_seconds, estimated_cost, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                user_id,
                result.problem,
                result.hypotheses[0]["hypothesis"] if result.hypotheses else None,
                result.duration_seconds,
                result.estimated_cost_usd,
                datetime.utcnow(),
            )

            # Save hypotheses
            for h in result.hypotheses:
                await conn.execute(
                    """
                    INSERT INTO hypotheses
                    (discovery_id, hypothesis_text, confidence, method, c4_path, triz_principles)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    discovery_id,
                    h["hypothesis"],
                    h["confidence"],
                    h["method"],
                    h.get("c4_path", []),
                    h.get("triz_principles", []),
                )

            return str(discovery_id)

    async def get_discovery(
        self, discovery_id: str, user_id: str | None = None
    ) -> dict | None:
        """Get discovery by ID."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM discoveries WHERE id = $1"
            params = [discovery_id]

            if user_id:
                query += " AND user_id = $2"
                params.append(user_id)

            row = await conn.fetchrow(query, *params)
            return dict(row) if row else None

    async def get_user_discoveries(
        self, user_id: str, skip: int, limit: int
    ) -> list[dict]:
        """Get user's discoveries."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM discoveries
                WHERE user_id = $1
                ORDER BY created_at DESC
                OFFSET $2 LIMIT $3
                """,
                user_id,
                skip,
                limit,
            )
            return [dict(r) for r in rows]

    async def get_all_discoveries(self, skip: int, limit: int) -> list[dict]:
        """Get all discoveries (for unauthenticated access)."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM discoveries
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
                """,
                skip,
                limit,
            )
            return [dict(r) for r in rows]

    async def update_discovery_status(
        self, discovery_id: str, status: str, notes: str | None, user_id: str
    ):
        """Update discovery validation status."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE discoveries 
                SET status = $1, validation_notes = $2, updated_at = $3
                WHERE id = $4 AND user_id = $5
                """,
                status,
                notes,
                datetime.utcnow(),
                discovery_id,
                user_id,
            )

    # ═══════════════════════════════════════════════════════════════
    # METRICS
    # ═══════════════════════════════════════════════════════════════

    async def count_discoveries(self) -> int:
        """Count total discoveries."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM discoveries")

    async def count_hypotheses(self) -> int:
        """Count total hypotheses."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM hypotheses")

    async def count_active_experiments(self) -> int:
        """Count active experiments."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM discoveries WHERE status = 'running'"
            )

    async def get_validation_rate(self) -> float:
        """Get validation rate."""
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM discoveries")
            if total == 0:
                return 0.0
            validated = await conn.fetchval(
                "SELECT COUNT(*) FROM discoveries WHERE status IN ('validated', 'falsified')"
            )
            return validated / total

    async def get_avg_confidence(self) -> float:
        """Get average confidence score."""
        async with self.pool.acquire() as conn:
            return (
                await conn.fetchval(
                    "SELECT COALESCE(AVG(confidence), 0) FROM hypotheses"
                )
                or 0.0
            )


# Singleton
_db: Database | None = None


async def get_db() -> Database:
    """Get database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.connect()
    return _db
