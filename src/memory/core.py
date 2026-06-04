"""
C4REQBER: Structural Memory Bank — Core Classes
"""
from __future__ import annotations


__all__ = [
    "MemoryQuery",
    "StructuralMemoryBank",
]

import asyncio
import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.c4.transformer import DomainFingerprint, IsomorphismResult


DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "structural_memory.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_SQL = """
-- Structural Memory Schema
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA wal_autocheckpoint=1000;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS fingerprints (
    id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    entities TEXT NOT NULL,  -- JSON array
    relations TEXT NOT NULL, -- JSON array of [a, r, b]
    constraints TEXT NOT NULL, -- JSON array
    c4_state TEXT,           -- "T,S,A"
    spectral_hash TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS isomorphisms (
    id TEXT PRIMARY KEY,
    source_fingerprint_id TEXT NOT NULL,
    target_fingerprint_id TEXT,
    source_domain TEXT NOT NULL,
    target_domain TEXT NOT NULL,
    source_c4 TEXT,
    target_c4 TEXT,
    mapping TEXT NOT NULL,   -- JSON dict
    confidence REAL NOT NULL,
    iso_type TEXT NOT NULL,  -- verified, partial, failed
    path TEXT NOT NULL,      -- JSON array of operators
    qzrf_operators TEXT,     -- JSON array
    description TEXT,
    timestamp REAL NOT NULL,
    validation_result TEXT,
    FOREIGN KEY (source_fingerprint_id) REFERENCES fingerprints(id),
    FOREIGN KEY (target_fingerprint_id) REFERENCES fingerprints(id)
);

CREATE INDEX IF NOT EXISTS idx_iso_confidence ON isomorphisms(confidence);
CREATE INDEX IF NOT EXISTS idx_iso_type ON isomorphisms(iso_type);
CREATE INDEX IF NOT EXISTS idx_iso_domains ON isomorphisms(source_domain, target_domain);
CREATE INDEX IF NOT EXISTS idx_fingerprint_hash ON fingerprints(spectral_hash);
CREATE INDEX IF NOT EXISTS idx_fingerprint_domain ON fingerprints(domain);

CREATE TABLE IF NOT EXISTS memory_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_experiments (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    hypothesis_id TEXT NOT NULL,
    name TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'simulation',
    status TEXT NOT NULL DEFAULT 'draft',
    observations TEXT NOT NULL DEFAULT '[]',
    conclusion TEXT,
    started_at REAL NOT NULL,
    completed_at REAL,
    created_at REAL NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_val_hypothesis ON validation_experiments(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_val_status ON validation_experiments(status);
"""


@dataclass
class MemoryQuery:
    """Query parameters for structural memory search."""

    query_text: str | None = None
    domain: str | None = None
    c4_state: tuple[int, int, int] | None = None
    iso_type: str | None = None
    min_confidence: float = 0.0
    include_partial: bool = True
    include_failed: bool = False
    limit: int = 20
    offset: int = 0


class StructuralMemoryBank:
    """
    SQLite-backed structural memory bank for C4REQBER.

    Usage:
        bank = StructuralMemoryBank()
        bank.store_isomorphism(fingerprint, result)
        results = bank.search(query)
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._init_db()

    @contextmanager  # type: ignore[arg-type]
    def _connection(self) -> None:  # type: ignore[misc]
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    async def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
        """Execute SQL in thread pool to avoid blocking event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._execute_sync, sql, params)

    def _execute_sync(self, sql: str, params: tuple[Any, ...]) -> list[Any]:
        with self._connection() as conn:  # type: ignore[var-annotated]
            return conn.execute(sql, params).fetchall()  # type: ignore[no-any-return]

    def _init_db(self) -> None:
        """Initialize database with schema."""
        with self._connection() as conn:  # type: ignore[var-annotated]
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            # Migration: add user_id column if missing (SQLite < 3.35 can't drop columns)
            try:
                conn.execute(
                    "ALTER TABLE validation_experiments ADD COLUMN user_id TEXT"
                )
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            # Create user_id index after column migration
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_val_user ON validation_experiments(user_id)"
                )
                conn.commit()
            except sqlite3.OperationalError:
                pass

    def _fingerprint_id(self, fp: DomainFingerprint) -> str:
        """Deterministic ID for fingerprint."""
        raw = f"{fp.domain}:{fp.spectral_hash}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def store_fingerprint(self, fp: DomainFingerprint) -> str:
        """Store a fingerprint, return its ID."""
        fp_id = self._fingerprint_id(fp)
        with self._connection() as conn:  # type: ignore[var-annotated]
            conn.execute(
                """INSERT OR REPLACE INTO fingerprints
                   (id, domain, entities, relations, constraints, c4_state, spectral_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fp_id,
                    fp.domain,
                    json.dumps(fp.entities),
                    json.dumps(fp.relations),
                    json.dumps(fp.constraints),
                    f"{fp.c4_state.T},{fp.c4_state.S},{fp.c4_state.A}"
                    if fp.c4_state
                    else None,
                    fp.spectral_hash,
                    time.time(),
                ),
            )
            conn.commit()
        return fp_id

    def store_isomorphism(
        self, source_fp: DomainFingerprint, result: IsomorphismResult
    ) -> str:
        """Store an isomorphism result."""
        source_id = self.store_fingerprint(source_fp)
        target_id = None
        if result.target_state:
            # Create a minimal target fingerprint
            target_fp = DomainFingerprint(
                domain=result.target_domain,
                entities=[],
                relations=[],
                constraints=[],
                c4_state=result.target_state,
            )
            target_id = self.store_fingerprint(target_fp)

        iso_id = hashlib.md5(
            f"{source_id}:{result.target_domain}:{time.time()}".encode()
        ).hexdigest()[:16]

        with self._connection() as conn:  # type: ignore[var-annotated]
            conn.execute(
                """INSERT INTO isomorphisms
                   (id, source_fingerprint_id, target_fingerprint_id,
                    source_domain, target_domain, source_c4, target_c4,
                    mapping, confidence, iso_type, path, qzrf_operators,
                    description, timestamp, validation_result)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    iso_id,
                    source_id,
                    target_id,
                    result.source_domain,
                    result.target_domain,
                    f"{result.source_state.T},{result.source_state.S},{result.source_state.A}"
                    if result.source_state
                    else None,
                    f"{result.target_state.T},{result.target_state.S},{result.target_state.A}"
                    if result.target_state
                    else None,
                    json.dumps(result.mapping),
                    result.confidence,
                    result.isomorphism_type.value,
                    json.dumps(result.path),
                    json.dumps(result.qzrf_operators),
                    result.description,
                    time.time(),
                    None,
                ),
            )
            conn.commit()
        return iso_id

    def search_sync(self, query: MemoryQuery) -> list[dict[str, Any]]:
        """Synchronous search — call via run_in_executor from async code."""
        conditions = ["1=1"]
        params: list[Any] = []

        if query.domain:
            conditions.append("(i.source_domain = ? OR i.target_domain = ?)")
            params.extend([query.domain, query.domain])

        if query.iso_type:
            conditions.append("i.iso_type = ?")
            params.append(query.iso_type)
        if not query.include_partial:
            conditions.append("i.iso_type != 'partial'")
        if not query.include_failed:
            conditions.append("i.iso_type != 'failed'")

        if query.min_confidence > 0:
            conditions.append("i.confidence >= ?")
            params.append(query.min_confidence)

        if query.c4_state:
            c4_str = f"{query.c4_state[0]},{query.c4_state[1]},{query.c4_state[2]}"
            conditions.append("(i.source_c4 = ? OR i.target_c4 = ?)")
            params.extend([c4_str, c4_str])

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT i.*,
                   sf.domain as source_domain_name,
                   sf.spectral_hash as source_hash,
                   tf.domain as target_domain_name
            FROM isomorphisms i
            LEFT JOIN fingerprints sf ON i.source_fingerprint_id = sf.id
            LEFT JOIN fingerprints tf ON i.target_fingerprint_id = tf.id
            WHERE {where_clause}
            ORDER BY i.confidence DESC, i.timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([query.limit, query.offset])

        with self._connection() as conn:  # type: ignore[var-annotated]
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        with self._connection() as conn:  # type: ignore[var-annotated]
            total = conn.execute("SELECT COUNT(*) FROM isomorphisms").fetchone()[0]
            verified = conn.execute(
                "SELECT COUNT(*) FROM isomorphisms WHERE iso_type = 'verified'"
            ).fetchone()[0]
            partial = conn.execute(
                "SELECT COUNT(*) FROM isomorphisms WHERE iso_type = 'partial'"
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM isomorphisms WHERE iso_type = 'failed'"
            ).fetchone()[0]
            avg_confidence = (
                conn.execute("SELECT AVG(confidence) FROM isomorphisms").fetchone()[0]
                or 0.0
            )

            return {
                "total_entries": total,
                "verified": verified,
                "partial": partial,
                "failed": failed,
                "avg_confidence": round(avg_confidence, 3),
                "db_path": str(self.db_path),
            }

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert DB row to dictionary."""
        return {
            "id": row["id"],
            "source_domain": row["source_domain"],
            "target_domain": row["target_domain"],
            "source_c4": row["source_c4"],
            "target_c4": row["target_c4"],
            "mapping": json.loads(row["mapping"]),
            "confidence": row["confidence"],
            "iso_type": row["iso_type"],
            "path": json.loads(row["path"]),
            "qzrf_operators": json.loads(row["qzrf_operators"])
            if row["qzrf_operators"]
            else [],
            "description": row["description"],
            "timestamp": row["timestamp"],
            "validation_result": row["validation_result"],
        }

    def export_to_obsidian(self, output_dir: Path) -> int:
        """Export verified isomorphisms as Obsidian markdown notes."""
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0

        with self._connection() as conn:  # type: ignore[var-annotated]
            rows = conn.execute(
                "SELECT * FROM isomorphisms WHERE iso_type = 'verified' ORDER BY timestamp DESC"
            ).fetchall()

            for row in rows:
                filename = f"isomorphism_{row['id']}.md"
                filepath = output_dir / filename

                frontmatter = {
                    "id": row["id"],
                    "source_domain": row["source_domain"],
                    "target_domain": row["target_domain"],
                    "confidence": row["confidence"],
                    "iso_type": row["iso_type"],
                    "timestamp": row["timestamp"],
                    "tags": [
                        "isomorphism",
                        f"domain/{row['source_domain']}",
                        f"domain/{row['target_domain']}",
                    ],
                }

                content = f"""---
{json.dumps(frontmatter, indent=2, ensure_ascii=False)}
---

# Isomorphism: {row["source_domain"]} → {row["target_domain"]}

**Confidence:** {row["confidence"]}
**C4 Path:** {" → ".join(json.loads(row["path"]))}

## Mapping
{chr(10).join(f"- **{k}** → {v}" for k, v in json.loads(row["mapping"]).items())}

## Description
{row["description"] or "No description"}
"""
                filepath.write_text(content, encoding="utf-8")
                count += 1

        return count

    # Async wrappers — run sync SQLite ops in thread pool to avoid blocking the event loop
    async def search(self, query: MemoryQuery) -> list[dict[str, Any]]:
        """Async wrapper for search_sync."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.search_sync, query)

    async def get_stats_async(self) -> dict[str, Any]:
        """Async wrapper for get_stats."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_stats)
