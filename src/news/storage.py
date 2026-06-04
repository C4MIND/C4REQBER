from __future__ import annotations


"""
Local SQLite storage for news feed items.

Table: news_feed
- id, title, body, source, url, category, published_at, created_at, entity_id
"""
import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


DB_PATH = Path(__file__).parent.parent.parent / "data" / "c44tcdi.db"

NEWS_SCHEMA = """
CREATE TABLE IF NOT EXISTS news_feed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    source TEXT DEFAULT '',
    url TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    published_at TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_feed_category ON news_feed(category);
CREATE INDEX IF NOT EXISTS idx_news_feed_created ON news_feed(created_at);
CREATE INDEX IF NOT EXISTS idx_news_feed_entity ON news_feed(entity_id);
"""


class NewsStorage:
    """SQLite-backed storage for news/ticker feed items."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(NEWS_SCHEMA)
            conn.commit()

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _make_entity_id(self, title: str, source: str) -> str:
        raw = f"{title}|{source}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def upsert(self, *, title: str, body: str = "", source: str = "",
               url: str = "", category: str = "general",
               published_at: str = "") -> bool:
        """Insert or skip (on entity_id collision). Returns True if inserted."""
        entity_id = self._make_entity_id(title, source)
        now = datetime.now(UTC).isoformat()
        try:
            with self._connection() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO news_feed
                       (entity_id, title, body, source, url, category, published_at, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (entity_id, title, body, source, url, category,
                     published_at or now, now),
                )
                conn.commit()
                return conn.total_changes > 0
        except Exception:
            return False

    def get_recent(self, limit: int = 50, category: str | None = None) -> list[dict[str, Any]]:
        with self._connection() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM news_feed WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                    (category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM news_feed ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_by_id(self, news_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM news_feed WHERE id = ?", (news_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_entity_id(self, entity_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM news_feed WHERE entity_id = ?", (entity_id,)
            ).fetchone()
            return dict(row) if row else None

    def count(self) -> int:
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM news_feed").fetchone()
            return row[0] if row else 0
