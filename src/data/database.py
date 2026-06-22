"""
C4REQBER: Pattern Database
SQLite/PostgreSQL storage for patterns, discoveries, and research context

Auto-detects database type from DATABASE_URL environment variable.
Supports SQLite (default) and PostgreSQL with connection pooling.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config.db_config import DatabaseConfig, get_database_config
from src.di.container import get_container


logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A discovered pattern or isomorphism."""

    id: int | None
    name: str
    description: str
    source_domain: str
    target_domain: str
    c4_path: list[str]  # JSON
    confidence: float
    times_used: int
    created_at: str
    tags: list[str]  # JSON


@dataclass
class Discovery:
    """A generated hypothesis/discovery."""

    id: int | None
    problem: str
    contradiction: str
    hypothesis: str
    c4_path: list[str]  # JSON
    domain: str
    confidence: float
    falsifiability_criteria: list[str]  # JSON
    status: str  # "pending", "validated", "falsified", "unknown"
    created_at: str
    notes: str


@dataclass
class ResearchContext:
    """Cached research context from arXiv/PubMed."""

    id: int | None
    query: str
    source: str  # "arxiv", "pubmed"
    results: list[dict]  # type: ignore  # JSON
    cached_at: str


class PatternDatabase:
    """
    SQLite database for storing C4REQBER patterns and discoveries.
    """

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            # Default to data directory
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "c4_cdi_turbo.db"  # type: ignore[assignment]

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source_domain TEXT NOT NULL,
                    target_domain TEXT NOT NULL,
                    c4_path TEXT NOT NULL,  -- JSON list
                    confidence REAL NOT NULL,
                    times_used INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    tags TEXT  -- JSON list
                )
            """)

            # Discoveries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem TEXT NOT NULL,
                    contradiction TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    c4_path TEXT NOT NULL,  -- JSON list
                    domain TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    falsifiability_criteria TEXT,  -- JSON list
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    notes TEXT
                )
            """)

            # Research context cache
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    results TEXT NOT NULL,  -- JSON
                    cached_at TEXT NOT NULL
                )
            """)

            # Session log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    problem_count INTEGER DEFAULT 0,
                    discoveries_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)

            conn.commit()

    # Pattern operations
    def save_pattern(self, pattern: Pattern) -> int:
        """Save a pattern and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO patterns
                   (name, description, source_domain, target_domain, c4_path,
                    confidence, times_used, created_at, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pattern.name,
                    pattern.description,
                    pattern.source_domain,
                    pattern.target_domain,
                    json.dumps(pattern.c4_path),
                    pattern.confidence,
                    pattern.times_used,
                    pattern.created_at or datetime.now().isoformat(),
                    json.dumps(pattern.tags) if pattern.tags else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_patterns(
        self, domain: str | None = None, min_confidence: float = 0.0
    ) -> list[Pattern]:
        """Get patterns, optionally filtered by domain."""
        with sqlite3.connect(self.db_path) as conn:
            if domain:
                cursor = conn.execute(
                    """SELECT * FROM patterns
                       WHERE (source_domain = ? OR target_domain = ?)
                       AND confidence >= ?
                       ORDER BY confidence DESC""",
                    (domain, domain, min_confidence),
                )
            else:
                cursor = conn.execute(
                    """SELECT * FROM patterns
                       WHERE confidence >= ?
                       ORDER BY confidence DESC""",
                    (min_confidence,),
                )

            rows = cursor.fetchall()
            return [self._row_to_pattern(row) for row in rows]

    def increment_pattern_usage(self, pattern_id: int) -> None:
        """Increment usage counter for a pattern."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE patterns SET times_used = times_used + 1 WHERE id = ?",
                (pattern_id,),
            )
            conn.commit()

    # Discovery operations
    def save_discovery(self, discovery: Discovery) -> int:
        """Save a discovery and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO discoveries
                   (problem, contradiction, hypothesis, c4_path, domain,
                    confidence, falsifiability_criteria, status, created_at, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    discovery.problem,
                    discovery.contradiction,
                    discovery.hypothesis,
                    json.dumps(discovery.c4_path),
                    discovery.domain,
                    discovery.confidence,
                    json.dumps(discovery.falsifiability_criteria)
                    if discovery.falsifiability_criteria
                    else None,
                    discovery.status,
                    discovery.created_at or datetime.now().isoformat(),
                    discovery.notes,
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_discoveries(
        self, domain: str | None = None, status: str | None = None
    ) -> list[Discovery]:
        """Get discoveries with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM discoveries WHERE 1=1"
            params = []

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_discovery(row) for row in rows]

    def update_discovery_status(self, discovery_id: int, status: str, notes: str = "") -> None:
        """Update status of a discovery."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE discoveries
                   SET status = ?, notes = ? || '\n' || notes
                   WHERE id = ?""",
                (status, notes, discovery_id),
            )
            conn.commit()

    # Research cache operations
    def get_cached_research(self, query: str, source: str) -> list[dict] | None:  # type: ignore[type-arg]
        """Get cached research results if not expired (7 days)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT results, cached_at FROM research_cache
                   WHERE query = ? AND source = ?""",
                (query, source),
            )
            row = cursor.fetchone()

            if row:
                results, cached_at = row
                # Check if cache is still valid (7 days)
                cache_time = datetime.fromisoformat(cached_at)
                if (datetime.now() - cache_time).days < 7:
                    return json.loads(results)  # type: ignore[no-any-return]

            return None

    def cache_research(self, query: str, source: str, results: list[dict]) -> None:  # type: ignore[type-arg]
        """Cache research results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO research_cache
                   (query, source, results, cached_at)
                   VALUES (?, ?, ?, ?)""",
                (query, source, json.dumps(results), datetime.now().isoformat()),
            )
            conn.commit()

    # Session operations
    def start_session(self) -> int:
        """Start a new session and return session ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (started_at) VALUES (?)",
                (datetime.now().isoformat(),),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def update_session_stats(
        self, session_id: int, problems: int = 0, discoveries: int = 0
    ) -> None:
        """Update session statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE sessions
                   SET problem_count = problem_count + ?,
                       discoveries_count = discoveries_count + ?
                   WHERE id = ?""",
                (problems, discoveries, session_id),
            )
            conn.commit()

    # Stats
    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            cursor = conn.execute("SELECT COUNT(*) FROM patterns")
            stats["patterns"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM discoveries")
            stats["discoveries"] = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM discoveries WHERE status = 'validated'"
            )
            stats["validated"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT AVG(confidence) FROM discoveries")
            result = cursor.fetchone()[0]
            stats["avg_confidence"] = round(result, 2) if result else 0.0

            return stats

    # Helper methods
    def _row_to_pattern(self, row: Any) -> Pattern:
        """Convert DB row to Pattern object."""
        return Pattern(
            id=row[0],
            name=row[1],
            description=row[2],
            source_domain=row[3],
            target_domain=row[4],
            c4_path=json.loads(row[5]),
            confidence=row[6],
            times_used=row[7],
            created_at=row[8],
            tags=json.loads(row[9]) if row[9] else [],
        )

    def _row_to_discovery(self, row: Any) -> Discovery:
        """Convert DB row to Discovery object."""
        return Discovery(
            id=row[0],
            problem=row[1],
            contradiction=row[2],
            hypothesis=row[3],
            c4_path=json.loads(row[4]),
            domain=row[5],
            confidence=row[6],
            falsifiability_criteria=json.loads(row[7]) if row[7] else [],
            status=row[8],
            created_at=row[9],
            notes=row[10] if row[10] else "",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Database Engine Detection and Initialization
# ═══════════════════════════════════════════════════════════════════════════════

# Backward-compatible module-level references (source of truth is DI container)
engine: Any = None
_db_config: DatabaseConfig | None = None


def init_database(config: DatabaseConfig | None = None) -> Any:
    """Initialize the database based on configuration.

    Auto-detects database type from DATABASE_URL or environment variables.
    Returns appropriate engine/database instance.

    Priority:
        1. DATABASE_URL env var (sqlite or postgresql)
        2. Individual DB_* settings for PostgreSQL
        3. Default SQLite
    """
    config = config or get_database_config()

    container = get_container()
    container.register("db_config", config)

    _engine: Any
    if config.is_postgresql():
        logger.info("Initializing PostgreSQL database with connection pooling")
        try:
            from src.data.database_pg import init_engine as init_pg_engine

            _engine = init_pg_engine(config)
            container.register("db_engine", _engine)
            return _engine
        except ImportError as e:
            logger.error(
                f"PostgreSQL dependencies not installed: {e}. "
                "Install with: pip install asyncpg psycopg2-binary sqlalchemy"
            )
            raise
    else:
        logger.info("Initializing SQLite database")
        # SQLite uses the PatternDatabase class directly
        _engine = PatternDatabase()
        container.register("db_engine", _engine)
        return _engine


def get_engine() -> Any:
    """Get the global database engine.

    Initializes on first call if not already done.
    """
    container = get_container()
    if container.has("db_engine"):
        return container.resolve("db_engine")
    return init_database()


def is_postgresql() -> bool:
    """Check if currently using PostgreSQL."""
    container = get_container()
    if container.has("db_config"):
        config = container.resolve("db_config")
        return config.is_postgresql()
    return get_database_config().is_postgresql()


def get_database_type() -> str:
    """Get string identifier for current database type."""
    if is_postgresql():
        return "postgresql"
    return "sqlite"


# Auto-initialize on module import if DATABASE_URL is set
if get_database_config().url:
    try:
        init_database()
    except Exception as e:
        logger.warning(f"Auto-initialization failed: {e}. Will retry on first use.")
