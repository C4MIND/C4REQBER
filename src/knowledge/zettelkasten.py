from __future__ import annotations


"""Zettelkasten-style personal knowledge base with vector search."""
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


class Zettelkasten:
    """Slip-box PKB with discovery tracking, search, and linking.

    Stores atomic notes in a local SQLite database with tags,
    links, and source attribution. Also indexes notes in ChromaDB
    for semantic vector search.
    """

    def __init__(self, db_path: str = "~/.c44tcdi/zettelkasten.db") -> None:
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                tags TEXT,
                links TEXT,
                source TEXT,
                created TEXT,
                updated TEXT
            )""")

    def _store_in_chroma(self, note_id: str, title: str, content: str) -> None:
        """Store note embedding in ChromaDB for semantic search."""
        try:
            from src.knowledge.chroma_store import ChromaVectorStore
            store = ChromaVectorStore()
            store.store_memory(
                session_id="zettelkasten",
                text=f"{title}\n{content}",
                metadata={"note_id": note_id, "title": title},
            )
        except Exception as e:
            logger.debug("ChromaDB store failed for note %s: %s", note_id, e)

    def _search_chroma(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic search via ChromaDB vector store."""
        try:
            from src.knowledge.chroma_store import ChromaVectorStore
            store = ChromaVectorStore()
            results = store.recall_memory("zettelkasten", query, n_results=top_k)
            return [{"text": r, "source": "vector"} for r in results]
        except Exception as e:
            logger.debug("ChromaDB search failed: %s", e)
            return []

    def add_note(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        source: str | None = None,
    ) -> str:
        """Create a new Zettelkasten note. Returns the note id."""
        note_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?)",
                (
                    note_id,
                    title,
                    content,
                    json.dumps(tags or []),
                    "[]",
                    source or "manual",
                    now,
                    now,
                ),
            )
        self._store_in_chroma(note_id, title, content)
        return note_id

    def add_discovery(
        self, problem: str, hypothesis: str, papers: list[dict[str, Any]]
    ) -> str:
        """Save a C4 discovery as a Zettelkasten note."""
        return self.add_note(
            title=f"Discovery: {problem[:80]}",
            content=hypothesis[:1000],
            tags=["discovery"] + [p.get("source", "") for p in papers[:3]],
            source="c44tcdi",
        )

    def get_note(self, note_id: str) -> dict[str, Any] | None:
        """Retrieve a single note by id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def search(self, query: str) -> list[dict[str, Any]]:
        """Full-text + semantic search across notes.

        Returns combined results from SQLite LIKE search and
        ChromaDB vector similarity search.
        """
        # SQLite full-text search
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? "
                "ORDER BY updated DESC LIMIT 20",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        text_results = [dict(r) for r in rows]

        # ChromaDB vector search
        vector_results = self._search_chroma(query, top_k=5)

        # Merge and deduplicate
        seen = {r["id"] for r in text_results if "id" in r}
        combined = text_results[:]
        for vr in vector_results:
            # Try to match vector result back to note id via metadata
            # ChromaDB recall_memory returns raw text; we can't easily get note_id
            # So just append as supplementary result
            combined.append(vr)

        return combined

    def get_related(self, note_id: str) -> list[dict[str, Any]]:
        """Find notes related by shared tags or vector similarity."""
        note = self.get_note(note_id)
        if not note:
            return []
        tags = json.loads(note.get("tags", "[]"))
        related = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            for tag in tags:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE tags LIKE ? AND id != ? LIMIT 5",
                    (f"%{tag}%", note_id),
                ).fetchall()
                related.extend([dict(r) for r in rows])

        # Add vector-similar notes via ChromaDB
        vector_related = self._search_chroma(note.get("title", ""), top_k=3)
        related.extend(vector_related)

        # Deduplicate
        seen = set()
        unique = []
        for r in related:
            rid = r.get("id", r.get("text", ""))
            if rid not in seen:
                seen.add(rid)
                unique.append(r)
        return unique[:10]
