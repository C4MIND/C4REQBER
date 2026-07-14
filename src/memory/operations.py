"""
C4REQBER: Structural Memory Bank — Validation Operations
"""
from __future__ import annotations


__all__ = [
    "ValidationOperations",
]

import asyncio
import json
import sqlite3
from typing import Any

from src.memory.core import StructuralMemoryBank


class ValidationOperations:
    """CRUD operations for validation experiments."""

    def __init__(self, bank: StructuralMemoryBank) -> None:
        self.bank = bank

    def create_validation(self, experiment: dict[str, Any]) -> str:
        """Create a validation experiment."""
        with self.bank._connection() as conn:  # type: ignore[var-annotated]
            conn.execute(
                """INSERT INTO validation_experiments
                   (id, user_id, hypothesis_id, name, method, status, observations, conclusion, started_at, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    experiment["id"],
                    experiment.get("user_id"),
                    experiment["hypothesis_id"],
                    experiment["name"],
                    experiment.get("method", "simulation"),
                    experiment.get("status", "draft"),
                    json.dumps(experiment.get("observations", [])),
                    experiment.get("conclusion"),
                    experiment["started_at"],
                    experiment.get("completed_at"),
                ),
            )
            conn.commit()
        return experiment["id"]  # type: ignore[no-any-return]

    def get_validation(
        self, exp_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Get a validation experiment by ID. If user_id provided, enforce ownership."""
        with self.bank._connection() as conn:  # type: ignore[var-annotated]
            if user_id:
                row = conn.execute(
                    "SELECT * FROM validation_experiments WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
                    (exp_id, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM validation_experiments WHERE id = ?", (exp_id,)
                ).fetchone()
            if not row:
                return None
            return self._validation_row_to_dict(row)

    def list_validations(
        self, status: str | None = None, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """List validation experiments, filtered by status and/or user ownership."""
        with self.bank._connection() as conn:  # type: ignore[var-annotated]
            conditions: list[str] = []
            params: list[Any] = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if user_id:
                conditions.append("(user_id = ? OR user_id IS NULL)")
                params.append(user_id)
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            rows = conn.execute(
                f"SELECT * FROM validation_experiments {where} ORDER BY created_at DESC",
                params,
            ).fetchall()
            return [self._validation_row_to_dict(r) for r in rows]

    def update_validation(
        self, exp_id: str, updates: dict[str, Any], user_id: str | None = None
    ) -> bool:
        """Update a validation experiment. If user_id provided, enforce ownership."""
        allowed = {"status", "observations", "conclusion", "completed_at"}
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            return False

        _COLUMN_SQL = {
            "status": "status = ?",
            "observations": "observations = ?",
            "conclusion": "conclusion = ?",
            "completed_at": "completed_at = ?",
        }
        set_parts = [_COLUMN_SQL[k] for k in fields]
        values = list(fields.values())
        if "observations" in fields:
            obs_idx = list(fields.keys()).index("observations")
            values[obs_idx] = json.dumps(fields["observations"])
        values.append(exp_id)

        if user_id:
            sql = f"UPDATE validation_experiments SET {', '.join(set_parts)} WHERE id = ? AND (user_id = ? OR user_id IS NULL)"
            values.append(user_id)
        else:
            sql = (
                f"UPDATE validation_experiments SET {', '.join(set_parts)} WHERE id = ?"
            )
        with self.bank._connection() as conn:  # type: ignore[var-annotated]
            cursor = conn.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0  # type: ignore[no-any-return]

    def _validation_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert validation DB row to dictionary."""
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "hypothesis_id": row["hypothesis_id"],
            "name": row["name"],
            "method": row["method"],
            "status": row["status"],
            "observations": json.loads(row["observations"]),
            "conclusion": row["conclusion"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
        }

    # Async wrappers
    async def get_validation_async(
        self, exp_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Async wrapper for get_validation."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_validation, exp_id, user_id)

    async def list_validations_async(
        self, status: str | None = None, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Async wrapper for list_validations."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.list_validations, status, user_id)

    async def create_validation_async(self, experiment: dict[str, Any]) -> str:
        """Async wrapper for create_validation."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.create_validation, experiment)

    async def update_validation_async(
        self, exp_id: str, updates: dict[str, Any], user_id: str | None = None
    ) -> bool:
        """Async wrapper for update_validation."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.update_validation, exp_id, updates, user_id
        )
