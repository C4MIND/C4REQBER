"""
Database normalization for Discovery Lab.
Creates separate tables for facts and theories instead of JSON blobs.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any


def create_normalized_tables(db_path: Path) -> None:
    """Create normalized tables for discovery data"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Facts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                corpus_id TEXT,
                statement TEXT NOT NULL,
                source TEXT,
                year INTEGER,
                domain TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (corpus_id) REFERENCES corpuses(id)
            )
        """)

        # Theories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theories (
                id TEXT PRIMARY KEY,
                corpus_id TEXT,
                name TEXT NOT NULL,
                principles TEXT,  -- JSON array
                equations TEXT,   -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (corpus_id) REFERENCES corpuses(id)
            )
        """)

        # Add indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_corpus ON facts(corpus_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theories_corpus ON theories(corpus_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_domain ON facts(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theories_name ON theories(name)")

        conn.commit()


def migrate_legacy_corpus(db_path: Path, corpus_id: str) -> None:
    """Migrate existing JSON-based corpus to normalized tables"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Get existing corpus
        cursor.execute("SELECT facts, theories FROM corpuses WHERE id = ?", (corpus_id,))
        row = cursor.fetchone()

        if not row:
            return

        import json

        facts_json = row[0]
        theories_json = row[1]

        if facts_json:
            try:
                facts = json.loads(facts_json)
                for fact in facts:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO facts (id, corpus_id, statement, source, year, domain)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            fact.get("id", f"{corpus_id}_fact_{facts.index(fact)}"),
                            corpus_id,
                            fact.get("statement", ""),
                            fact.get("source", ""),
                            fact.get("year", None),
                            fact.get("domain", ""),
                        ),
                    )
            except json.JSONDecodeError:
                pass

        if theories_json:
            try:
                theories = json.loads(theories_json)
                for theory in theories:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO theories (id, corpus_id, name, principles, equations)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            theory.get("id", f"{corpus_id}_theory_{theories.index(theory)}"),
                            corpus_id,
                            theory.get("name", ""),
                            json.dumps(theory.get("principles", [])),
                            json.dumps(theory.get("equations", [])),
                        ),
                    )
            except json.JSONDecodeError:
                pass

        conn.commit()


# Initialize normalized schema if called directly
if __name__ == "__main__":
    db_path = Path.home() / ".turbo-cdi" / "discovery.db"
    create_normalized_tables(db_path)
    print(f"✅ Normalized discovery database schema created at {db_path}")
