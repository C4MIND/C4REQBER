"""
C4REQBER: Bibliography Manager
Reference management, citations, BibTeX export
"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Reference:
    """Academic reference/citation."""

    id: int | None
    entry_type: str  # article, book, inproceedings, etc.
    cite_key: str
    title: str
    authors: list[str]
    year: int
    journal: str | None = None
    volume: str | None = None
    number: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    publisher: str | None = None
    abstract: str | None = None
    keywords: list[str] = None  # type: ignore[assignment]
    tags: list[str] = None  # type: ignore[assignment]
    notes: str = ""
    project_ids: list[int] = None  # type: ignore[assignment]
    added_at: str = ""


class BibliographyManager:
    """
    Manage academic references and generate citations.
    """

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "bibliography.db"  # type: ignore[assignment]

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize bibliography database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 'references' (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_type TEXT NOT NULL,
                    cite_key TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    journal TEXT,
                    volume TEXT,
                    number TEXT,
                    pages TEXT,
                    doi TEXT,
                    url TEXT,
                    publisher TEXT,
                    abstract TEXT,
                    keywords TEXT,
                    tags TEXT,
                    notes TEXT,
                    project_ids TEXT,
                    added_at TEXT NOT NULL
                )
            """)

            # Citation usage tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference_id INTEGER NOT NULL,
                    discovery_id INTEGER,
                    project_id INTEGER,
                    context TEXT,
                    cited_at TEXT NOT NULL,
                    FOREIGN KEY (reference_id) REFERENCES 'references' (id)
                )
            """)

            conn.commit()

    def add_reference(self, ref: Reference) -> int:
        """Add reference to library."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO 'references'
                   (entry_type, cite_key, title, authors, year, journal, volume,
                    number, pages, doi, url, publisher, abstract, keywords, tags,
                    notes, project_ids, added_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ref.entry_type,
                    ref.cite_key,
                    ref.title,
                    json.dumps(ref.authors),
                    ref.year,
                    ref.journal,
                    ref.volume,
                    ref.number,
                    ref.pages,
                    ref.doi,
                    ref.url,
                    ref.publisher,
                    ref.abstract,
                    json.dumps(ref.keywords) if ref.keywords else None,
                    json.dumps(ref.tags) if ref.tags else None,
                    ref.notes,
                    json.dumps(ref.project_ids) if ref.project_ids else None,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def search_references(
        self,
        query: str,
        tags: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[Reference]:
        """Search references."""
        with sqlite3.connect(self.db_path) as conn:
            sql = """SELECT * FROM 'references'
                     WHERE (title LIKE ? OR authors LIKE ? OR abstract LIKE ?)"""
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]

            if year_from:
                sql += " AND year >= ?"
                params.append(year_from)  # type: ignore[arg-type]

            if year_to:
                sql += " AND year <= ?"
                params.append(year_to)  # type: ignore[arg-type]

            sql += " ORDER BY year DESC"

            cursor = conn.execute(sql, params)
            return [self._row_to_reference(row) for row in cursor.fetchall()]

    def get_by_cite_key(self, cite_key: str) -> Reference | None:
        """Get reference by citation key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM 'references' WHERE cite_key = ?", (cite_key,)
            )
            row = cursor.fetchone()
            return self._row_to_reference(row) if row else None

    def generate_bibtex(self, ref_id: int | None = None) -> str:
        """Generate BibTeX entry."""
        with sqlite3.connect(self.db_path) as conn:
            if ref_id:
                cursor = conn.execute(
                    "SELECT * FROM 'references' WHERE id = ?", (ref_id,)
                )
                rows = [cursor.fetchone()]
            else:
                cursor = conn.execute("SELECT * FROM 'references'")
                rows = cursor.fetchall()

            bibtex_entries = []
            for row in rows:
                if not row:
                    continue
                ref = self._row_to_reference(row)
                entry = self._to_bibtex(ref)
                bibtex_entries.append(entry)

            return "\n\n".join(bibtex_entries)

    def _to_bibtex(self, ref: Reference) -> str:
        """Convert reference to BibTeX format."""
        lines = [f"@{ref.entry_type}{{{ref.cite_key},"]

        lines.append(f"  title = {{{ref.title}}},")

        # Authors
        if len(ref.authors) == 1:
            lines.append(f"  author = {{{ref.authors[0]}}},")
        else:
            authors_str = " and ".join(ref.authors)
            lines.append(f"  author = {{{authors_str}}},")

        lines.append(f"  year = {{{ref.year}}},")

        if ref.journal:
            lines.append(f"  journal = {{{ref.journal}}},")

        if ref.volume:
            lines.append(f"  volume = {{{ref.volume}}},")

        if ref.number:
            lines.append(f"  number = {{{ref.number}}},")

        if ref.pages:
            lines.append(f"  pages = {{{ref.pages}}},")

        if ref.doi:
            lines.append(f"  doi = {{{ref.doi}}},")

        if ref.url:
            lines.append(f"  url = {{{ref.url}}},")

        if ref.publisher:
            lines.append(f"  publisher = {{{ref.publisher}}},")

        if ref.abstract:
            # Escape special characters
            abstract = ref.abstract.replace("{", "{{").replace("}", "}}")
            lines.append(f"  abstract = {{{abstract}}},")

        lines.append("}")

        return "\n".join(lines)

    def generate_citation(self, cite_key: str, style: str = "apa") -> str:
        """Generate inline citation."""
        ref = self.get_by_cite_key(cite_key)
        if not ref:
            return f"[{cite_key}]"

        if style == "apa":
            if len(ref.authors) == 1:
                return f"({ref.authors[0].split()[-1]}, {ref.year})"
            elif len(ref.authors) == 2:
                return f"({ref.authors[0].split()[-1]} & {ref.authors[1].split()[-1]}, {ref.year})"
            else:
                return f"({ref.authors[0].split()[-1]} et al., {ref.year})"

        elif style == "ieee":
            return f"[{cite_key}]"

        elif style == "mla":
            return f"({ref.authors[0].split()[-1]} {ref.year})"

        return f"[{cite_key}]"

    def import_from_bibtex(self, bibtex_text: str) -> list[int]:
        """Import references from BibTeX."""
        ids = []

        # Simple BibTeX parser
        entries = re.split(r"@\w+\{", bibtex_text)[1:]  # Split by entry starts

        for entry_text in entries:
            try:
                # Extract entry type and key
                entry_type = bibtex_text.split("@")[1].split("{")[0].lower()

                # Extract fields
                cite_key = entry_text.split(",")[0].strip()

                def extract_field(field_name: str, _entry_text: str = entry_text) -> str | None:
                    """Extract field."""
                    pattern = rf"{field_name}\s*=\s*\{{([^}}]+)\}}"
                    match = re.search(pattern, _entry_text, re.IGNORECASE)
                    return match.group(1).strip() if match else None

                title = extract_field("title") or "Unknown"
                year_str = extract_field("year") or "2024"
                year = int(year_str) if year_str.isdigit() else 2024

                authors_str = extract_field("author") or "Unknown"
                authors = [a.strip() for a in authors_str.split(" and ")]

                ref = Reference(
                    id=None,
                    entry_type=entry_type,
                    cite_key=cite_key,
                    title=title,
                    authors=authors,
                    year=year,
                    journal=extract_field("journal"),
                    volume=extract_field("volume"),
                    number=extract_field("number"),
                    pages=extract_field("pages"),
                    doi=extract_field("doi"),
                    url=extract_field("url"),
                    publisher=extract_field("publisher"),
                    added_at=datetime.now().isoformat(),
                )

                ref_id = self.add_reference(ref)
                ids.append(ref_id)

            except Exception as e:
                print(f"Failed to parse entry: {e}")
                continue

        return ids

    def export_to_file(self, filepath: str, format: str = "bibtex") -> None:
        """Export bibliography to file."""
        if format == "bibtex":
            content = self.generate_bibtex()
            with open(filepath, "w") as f:
                f.write(content)

        elif format == "json":
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM 'references'")
                refs = [self._row_to_dict(row) for row in cursor.fetchall()]

            with open(filepath, "w") as f:
                json.dump(refs, f, indent=2)

    def _row_to_reference(self, row: Any) -> Reference:
        return Reference(
            id=row[0],
            entry_type=row[1],
            cite_key=row[2],
            title=row[3],
            authors=json.loads(row[4]),
            year=row[5],
            journal=row[6],
            volume=row[7],
            number=row[8],
            pages=row[9],
            doi=row[10],
            url=row[11],
            publisher=row[12],
            abstract=row[13],
            keywords=json.loads(row[14]) if row[14] else [],
            tags=json.loads(row[15]) if row[15] else [],
            notes=row[16] if row[16] else "",
            project_ids=json.loads(row[17]) if row[17] else [],
            added_at=row[18],
        )

    def _row_to_dict(self, row: Any) -> dict[str, Any]:
        """Convert row to dictionary."""
        return {
            "id": row[0],
            "entry_type": row[1],
            "cite_key": row[2],
            "title": row[3],
            "authors": json.loads(row[4]),
            "year": row[5],
            "journal": row[6],
            "volume": row[7],
            "number": row[8],
            "pages": row[9],
            "doi": row[10],
            "url": row[11],
            "publisher": row[12],
            "abstract": row[13],
            "keywords": json.loads(row[14]) if row[14] else [],
            "tags": json.loads(row[15]) if row[15] else [],
            "notes": row[16],
            "added_at": row[18],
        }
