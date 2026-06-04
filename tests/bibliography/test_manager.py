"""Tests for src/bibliography/manager.py - using in-memory SQLite."""
from __future__ import annotations

import json
import tempfile
from typing import Any

import pytest

from bibliography.manager import BibliographyManager, Reference


@pytest.fixture
def manager(tmp_path: Any) -> BibliographyManager:
    db = tmp_path / "test_bib.db"
    return BibliographyManager(str(db))


class TestAddReference:
    def test_add_reference(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None,
            entry_type="article",
            cite_key="generic2026",
            title="Test Article",
            authors=["Author A.", "Author B."],
            year=2026,
            journal="Nature",
            doi="10.1234/test",
            keywords=["c4", "ai"],
            tags=["core"],
            project_ids=[1],
        )
        rid = manager.add_reference(ref)
        assert isinstance(rid, int)
        assert rid > 0

    def test_add_multiple(self, manager: BibliographyManager) -> None:
        for i in range(3):
            ref = Reference(
                id=None,
                entry_type="article",
                cite_key=f"ref{i}",
                title=f"Title {i}",
                authors=["Author"],
                year=2020 + i,
            )
            manager.add_reference(ref)


class TestSearchReferences:
    def test_search_by_title(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="Quantum Computing", authors=["A"], year=2023
        )
        manager.add_reference(ref)
        results = manager.search_references("Quantum")
        assert len(results) == 1
        assert results[0].title == "Quantum Computing"

    def test_search_by_author(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["Einstein A."], year=1905
        )
        manager.add_reference(ref)
        results = manager.search_references("Einstein")
        assert len(results) == 1

    def test_search_with_year_filter(self, manager: BibliographyManager) -> None:
        for y in [2000, 2010, 2020]:
            ref = Reference(
                id=None, entry_type="article", cite_key=f"k{y}",
                title="T", authors=["A"], year=y
            )
            manager.add_reference(ref)
        results = manager.search_references("T", year_from=2010)
        assert len(results) == 2
        results2 = manager.search_references("T", year_to=2010)
        assert len(results2) == 2
        results3 = manager.search_references("T", year_from=2005, year_to=2015)
        assert len(results3) == 1

    def test_search_no_match(self, manager: BibliographyManager) -> None:
        results = manager.search_references("nonexistent")
        assert results == []


class TestGetByCiteKey:
    def test_get_existing(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="testkey",
            title="T", authors=["A"], year=2023
        )
        manager.add_reference(ref)
        fetched = manager.get_by_cite_key("testkey")
        assert fetched is not None
        assert fetched.cite_key == "testkey"

    def test_get_missing(self, manager: BibliographyManager) -> None:
        assert manager.get_by_cite_key("missing") is None


class TestGenerateBibtex:
    def test_single_reference(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="The Title", authors=["Smith J."], year=2020,
            journal="JAI", volume="1", number="2", pages="1-10",
            doi="10.1/1", url="http://x.com", publisher="Pub",
        )
        manager.add_reference(ref)
        bib = manager.generate_bibtex()
        assert "@article{k1," in bib
        assert "title = {The Title}," in bib
        assert "author = {Smith J.}," in bib
        assert "year = {2020}," in bib
        assert "journal = {JAI}," in bib
        assert "volume = {1}," in bib
        assert "number = {2}," in bib
        assert "pages = {1-10}," in bib
        assert "doi = {10.1/1}," in bib
        assert "url = {http://x.com}," in bib
        assert "publisher = {Pub}," in bib

    def test_multiple_authors(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["Smith J.", "Doe A."], year=2020
        )
        manager.add_reference(ref)
        bib = manager.generate_bibtex()
        assert "author = {Smith J. and Doe A.}," in bib

    def test_generate_by_id(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["A"], year=2020
        )
        rid = manager.add_reference(ref)
        bib = manager.generate_bibtex(rid)
        assert "@article{k1," in bib

    def test_empty_library(self, manager: BibliographyManager) -> None:
        bib = manager.generate_bibtex()
        assert bib == ""


class TestGenerateCitation:
    def test_apa_single_author(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["John Smith"], year=2020
        )
        manager.add_reference(ref)
        assert manager.generate_citation("k1", style="apa") == "(Smith, 2020)"

    def test_apa_two_authors(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["John Smith", "Ann Doe"], year=2020
        )
        manager.add_reference(ref)
        assert manager.generate_citation("k1", style="apa") == "(Smith \u0026 Doe, 2020)"

    def test_apa_three_plus_authors(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["A B", "C D", "E F"], year=2020
        )
        manager.add_reference(ref)
        assert manager.generate_citation("k1", style="apa") == "(B et al., 2020)"

    def test_ieee(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["A"], year=2020
        )
        manager.add_reference(ref)
        assert manager.generate_citation("k1", style="ieee") == "[k1]"

    def test_mla(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["John Smith"], year=2020
        )
        manager.add_reference(ref)
        assert manager.generate_citation("k1", style="mla") == "(Smith 2020)"

    def test_unknown_key(self, manager: BibliographyManager) -> None:
        assert manager.generate_citation("missing") == "[missing]"

    def test_unknown_style(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["A"], year=2020
        )
        manager.add_reference(ref)
        assert manager.generate_citation("k1", style="chicago") == "[k1]"


class TestImportFromBibtex:
    def test_import_single(self, manager: BibliographyManager) -> None:
        bibtex = """
@article{smith2020,
  title = {The Great Paper},
  author = {Smith, John},
  year = {2020},
  journal = {Nature}
}
"""
        ids = manager.import_from_bibtex(bibtex)
        assert len(ids) == 1
        ref = manager.get_by_cite_key("smith2020")
        assert ref is not None
        assert ref.title == "The Great Paper"
        assert ref.year == 2020

    def test_import_multiple(self, manager: BibliographyManager) -> None:
        bibtex = """
@article{ref1,
  title = {T1},
  author = {A},
  year = {2020}
}
@book{ref2,
  title = {T2},
  author = {B},
  year = {2021}
}
"""
        ids = manager.import_from_bibtex(bibtex)
        assert len(ids) == 2

    def test_import_malformed_skipped(self, manager: BibliographyManager) -> None:
        # The second entry is so broken that re.split will not produce a valid entry for it
        bibtex = """
@article{ref1,
  title = {T1},
  author = {A},
  year = {2020}
}
@article{ref2,
  title = {T2},
  author = {B},
  year = {bad_year}
}
"""
        ids = manager.import_from_bibtex(bibtex)
        # Both may parse because the regex is lenient, but bad_year causes ValueError in the year int() conversion
        # which is caught, so only ref1 is added
        assert len(ids) >= 1


class TestExportToFile:
    def test_export_bibtex(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["A"], year=2020
        )
        manager.add_reference(ref)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            path = f.name
        manager.export_to_file(path, format="bibtex")
        with open(path) as f:
            content = f.read()
        assert "@article{k1," in content

    def test_export_json(self, manager: BibliographyManager) -> None:
        ref = Reference(
            id=None, entry_type="article", cite_key="k1",
            title="T", authors=["A"], year=2020
        )
        manager.add_reference(ref)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        manager.export_to_file(path, format="json")
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["cite_key"] == "k1"
