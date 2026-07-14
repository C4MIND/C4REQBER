"""Tests for src/publishing/submitter.py — PreprintSubmitter and module-level functions."""
from __future__ import annotations

import inspect

from src.publishing import submitter as submitter_module
from src.publishing.submitter import (
    PreprintSubmitter,
    generate_arxiv_package,
    generate_biorxiv_package,
)


class TestEscapeLatex:
    def test_ampersand(self):
        assert PreprintSubmitter._escape_latex("a & b") == "a \\& b"

    def test_percent(self):
        assert PreprintSubmitter._escape_latex("50%") == "50\\%"

    def test_underscore(self):
        assert PreprintSubmitter._escape_latex("hello_world") == "hello\\_world"

    def test_braces(self):
        result = PreprintSubmitter._escape_latex("{test}")
        assert "\\{" in result
        assert "\\}" in result

    def test_no_changes(self):
        assert PreprintSubmitter._escape_latex("Hello World") == "Hello World"

    def test_jats_tags(self):
        result = PreprintSubmitter._escape_latex("<jats:p>text</jats:p>")
        assert "<jats:p>" not in result
        assert "text" in result

    def test_null_chars(self):
        result = PreprintSubmitter._escape_latex("a\x00b")
        assert "\x00" not in result

    def test_textless(self):
        result = PreprintSubmitter._escape_latex("a < b")
        assert "\\textless" in result


class TestReferencesToBibtex:
    def test_single_reference(self):
        refs = [{"title": "Great Paper", "authors": "John Doe", "year": "2023",
                 "cite_key": "Doe2023", "journal": "Nature", "doi": "10.0/xyz", "url": "http://example.com"}]
        result = PreprintSubmitter._references_to_bibtex(refs)
        assert "@article{" in result
        assert "Great Paper" in result
        assert "Doe2023" in result

    def test_multiple_references(self):
        refs = [
            {"title": f"Paper {i}", "authors": f"Author {i}", "year": str(2020 + i),
             "cite_key": f"Key{i}", "journal": "J", "doi": "x", "url": "http://x.com"}
            for i in range(3)
        ]
        result = PreprintSubmitter._references_to_bibtex(refs)
        assert result.count("@article{") == 3

    def test_missing_cite_key_uses_default(self):
        refs = [{"title": "Paper", "authors": "Alpha Beta", "year": "2025",
                 "journal": "J", "doi": "x", "url": "http://x.com"}]
        result = PreprintSubmitter._references_to_bibtex(refs)
        assert "ref1" in result

    def test_empty_references(self):
        result = PreprintSubmitter._references_to_bibtex([])
        assert result == ""

    def test_authors_list_converted(self):
        refs = [{"title": "T", "authors": ["A", "B", "C"], "year": "2025",
                 "cite_key": "key", "journal": "J", "doi": "x", "url": "http://x.com"}]
        result = PreprintSubmitter._references_to_bibtex(refs)
        assert "A and B and C" in result


class TestPreprintSubmitter:
    def test_instantiation(self):
        ps = PreprintSubmitter()
        assert ps is not None

    def test_generate_arxiv_submission(self):
        result = PreprintSubmitter.generate_arxiv_submission(
            paper_body="## Introduction\n\nThis is a test paper.",
            abstract="A test abstract for arXiv submission.",
            title="Test Paper",
            author="Test Author",
        )
        assert "title" in result
        assert len(result.get("references", [])) == 0

    def test_generate_arxiv_with_references(self):
        result = PreprintSubmitter.generate_arxiv_submission(
            paper_body="Content",
            abstract="Abstract",
            title="Paper",
            author="A",
            references=[{"title": "R", "authors": "X", "year": "2025",
                         "cite_key": "k", "journal": "J", "doi": "d", "url": "u"}],
        )
        assert "@article{" in result.get("bibtex", "")

    def test_generate_biorxiv_submission(self):
        result = PreprintSubmitter.generate_biorxiv_submission(
            paper_body="Content",
            abstract="Abstract",
            title="Bio Paper",
        )
        assert "title" in result


class TestModuleLevelFunctions:
    def test_module_imports_cleanly(self) -> None:
        assert submitter_module is not None

    def test_generate_arxiv_package_signature(self) -> None:
        sig = inspect.signature(generate_arxiv_package)
        params = list(sig.parameters.keys())
        assert "paper_body" in params
        assert "abstract" in params

    def test_generate_biorxiv_package_signature(self) -> None:
        sig = inspect.signature(generate_biorxiv_package)
        params = list(sig.parameters.keys())
        assert "paper_body" in params
        assert "abstract" in params

    def test_generate_arxiv_package_returns_dict(self) -> None:
        result = generate_arxiv_package(
            paper_body="Test body.",
            abstract="Test abstract.",
            title="Test",
        )
        assert isinstance(result, dict)
        assert "title" in result
        assert "format" in result

    def test_generate_biorxiv_package_returns_dict(self) -> None:
        result = generate_biorxiv_package(
            paper_body="Bio content.",
            abstract="Bio abstract.",
            title="Bio Test",
        )
        assert isinstance(result, dict)
        assert "format" in result
