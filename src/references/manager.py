"""
TURBO-CDI: Reference Manager Integration
Import from Zotero and Mendeley
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ReferenceImport:
    """Imported reference."""

    title: str
    authors: List[str]
    year: int
    journal: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    tags: List[str] = None
    source: str = ""  # zotero, mendeley

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ZoteroImporter:
    """Import references from Zotero."""

    def __init__(self, library_path: Optional[str] = None):
        self.library_path = library_path

    def import_from_csv(self, csv_path: str) -> List[ReferenceImport]:
        """Import from Zotero CSV export."""
        import csv

        references = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref = ReferenceImport(
                    title=row.get("Title", ""),
                    authors=row.get("Author", "").split("; "),
                    year=int(row.get("Publication Year", 0))
                    if row.get("Publication Year")
                    else 0,
                    journal=row.get("Publication Title", ""),
                    doi=row.get("DOI", ""),
                    url=row.get("Url", ""),
                    abstract=row.get("Abstract Note", ""),
                    tags=row.get("Manual Tags", "").split("; "),
                    source="zotero",
                )
                references.append(ref)

        return references

    def import_from_bib(self, bib_path: str) -> List[ReferenceImport]:
        """Import from BibTeX file."""
        # Simple BibTeX parser
        references = []

        with open(bib_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split entries
        entries = content.split("@")[1:]

        for entry in entries:
            lines = entry.split("\n")

            # Extract fields
            fields = {}
            for line in lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('{},"').strip(",")
                    fields[key] = value

            ref = ReferenceImport(
                title=fields.get("title", ""),
                authors=fields.get("author", "").split(" and "),
                year=int(fields.get("year", 0)) if fields.get("year") else 0,
                journal=fields.get("journal", ""),
                doi=fields.get("doi", ""),
                url=fields.get("url", ""),
                abstract=fields.get("abstract", ""),
                source="zotero",
            )
            references.append(ref)

        return references


class MendeleyImporter:
    """Import references from Mendeley."""

    def import_from_csv(self, csv_path: str) -> List[ReferenceImport]:
        """Import from Mendeley CSV export."""
        import csv

        references = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref = ReferenceImport(
                    title=row.get("Title", ""),
                    authors=row.get("Authors", "").split(", "),
                    year=int(row.get("Year", 0)) if row.get("Year") else 0,
                    journal=row.get("Publication", ""),
                    doi=row.get("DOI", ""),
                    url=row.get("URL", ""),
                    abstract=row.get("Abstract", ""),
                    source="mendeley",
                )
                references.append(ref)

        return references


class ReferenceManager:
    """Unified reference manager integration."""

    def __init__(self):
        self.zotero = ZoteroImporter()
        self.mendeley = MendeleyImporter()

    def import_references(
        self, file_path: str, source: str = "auto"
    ) -> List[ReferenceImport]:
        """
        Import references from file.

        Args:
            file_path: Path to export file
            source: "zotero", "mendeley", or "auto"

        Returns:
            List of imported references
        """
        path = Path(file_path)

        # Auto-detect source
        if source == "auto":
            if "zotero" in path.name.lower():
                source = "zotero"
            elif "mendeley" in path.name.lower():
                source = "mendeley"
            else:
                # Detect by extension
                if path.suffix == ".bib":
                    source = "zotero"
                else:
                    source = "zotero"  # Default

        # Import based on source and format
        if source == "zotero":
            if path.suffix == ".csv":
                return self.zotero.import_from_csv(file_path)
            elif path.suffix == ".bib":
                return self.zotero.import_from_bib(file_path)

        elif source == "mendeley":
            if path.suffix == ".csv":
                return self.mendeley.import_from_csv(file_path)

        raise ValueError(f"Unsupported format: {path.suffix} for source {source}")

    def save_to_knowledge_graph(self, references: List[ReferenceImport]):
        """Save imported references to knowledge graph."""
        from src.graph.knowledge_graph import get_knowledge_graph

        kg = get_knowledge_graph()

        for ref in references:
            kg.add_reference(
                title=ref.title,
                authors=ref.authors,
                year=ref.year,
                source=ref.source,
                source_id=ref.doi or ref.url,
                metadata={
                    "journal": ref.journal,
                    "doi": ref.doi,
                    "url": ref.url,
                    "abstract": ref.abstract,
                    "tags": ref.tags,
                },
            )

        kg.save()


# Singleton
_manager: Optional[ReferenceManager] = None


def get_reference_manager() -> ReferenceManager:
    """Get singleton reference manager."""
    global _manager
    if _manager is None:
        _manager = ReferenceManager()
    return _manager
