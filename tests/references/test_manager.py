"""Tests for src/references/manager.py — ZoteroImporter, MendeleyImporter."""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.references.manager import (
    MendeleyImporter,
    ReferenceImport,
    ReferenceManager,
    ZoteroImporter,
    get_reference_manager,
)


class TestReferenceImport:
    def test_default_tags(self):
        ref = ReferenceImport(
            title="Test", authors=["Author"], year=2025,
        )
        assert ref.tags == []

    def test_with_all_fields(self):
        ref = ReferenceImport(
            title="Great Paper",
            authors=["John Doe", "Jane Smith"],
            year=2024,
            journal="Nature",
            doi="10.1234/test",
            url="http://example.com",
            abstract="An abstract",
            tags=["AI", "ML"],
            source="zotero",
        )
        assert ref.title == "Great Paper"
        assert len(ref.authors) == 2
        assert ref.tags == ["AI", "ML"]
        assert ref.source == "zotero"


class TestZoteroImporter:
    def test_instantiation(self):
        imp = ZoteroImporter()
        assert imp is not None

    def test_with_library_path(self):
        imp = ZoteroImporter(library_path="/tmp/zotero")
        assert imp.library_path == "/tmp/zotero"

    def test_import_from_csv(self):
        imp = ZoteroImporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Title,Author,Publication Year\n")
            f.write("Paper One,John Doe,2025\n")
            f.write("Paper Two,Jane Smith,2024\n")
            tmp = f.name
        try:
            refs = imp.import_from_csv(tmp)
            assert len(refs) == 2
            assert refs[0].title == "Paper One"
            assert refs[1].year == 2024
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_import_from_csv_missing_columns(self):
        imp = ZoteroImporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Title\n")
            f.write("Only Title\n")
            tmp = f.name
        try:
            refs = imp.import_from_csv(tmp)
            assert len(refs) == 1
        finally:
            Path(tmp).unlink(missing_ok=True)


class TestMendeleyImporter:
    def test_instantiation(self):
        imp = MendeleyImporter()
        assert imp is not None

    def test_import_from_csv(self):
        imp = MendeleyImporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Title,Authors,Year\n")
            f.write("Paper,A and B,2024\n")
            tmp = f.name
        try:
            refs = imp.import_from_csv(tmp)
            assert len(refs) == 1
        finally:
            Path(tmp).unlink(missing_ok=True)


class TestReferenceManager:
    def test_instantiation(self):
        rm = ReferenceManager()
        assert rm is not None

    def test_get_reference_manager(self):
        rm = get_reference_manager()
        assert rm is not None
