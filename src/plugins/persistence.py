"""
C4REQBER: Plugin Result Persistence
SQLite-backed storage for plugin execution results.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "plugin_results.db"


class PluginResultStore:
    """Persistent store for plugin execution results with SQLite backend."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._connect()
        return self._local.conn  # type: ignore[no-any-return]

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plugin_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_id TEXT NOT NULL,
                    problem_hash TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_plugin_problem
                ON plugin_results(plugin_id, problem_hash)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON plugin_results(created_at DESC)
                """
            )
            conn.commit()

    @staticmethod
    def _hash_problem(problem: str) -> str:
        return hashlib.sha256(problem.encode("utf-8")).hexdigest()

    def save(
        self,
        plugin_id: str,
        problem: str,
        result: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Save a plugin result. Returns the row id."""
        problem_hash = self._hash_problem(problem)
        result_json = json.dumps(result, ensure_ascii=False)
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        created_at = time.time()

        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO plugin_results (plugin_id, problem_hash, result_json, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (plugin_id, problem_hash, result_json, metadata_json, created_at),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get(self, plugin_id: str, problem: str) -> dict[str, Any] | None:
        """Retrieve the most recent result for a plugin+problem combo."""
        problem_hash = self._hash_problem(problem)
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT result_json, metadata_json, created_at
            FROM plugin_results
            WHERE plugin_id = ? AND problem_hash = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (plugin_id, problem_hash),
        ).fetchone()

        if row is None:
            return None

        return {
            "result": json.loads(row["result_json"]),
            "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None,
            "created_at": row["created_at"],
        }

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """List most recent stored results."""
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT id, plugin_id, problem_hash, result_json, metadata_json, created_at
            FROM plugin_results
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "plugin_id": row["plugin_id"],
                "problem_hash": row["problem_hash"],
                "result": json.loads(row["result_json"]),
                "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None,
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def close(self) -> None:
        """Close thread-local connection if open."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
