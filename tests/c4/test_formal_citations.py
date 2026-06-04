from __future__ import annotations

import pytest

from src.c4.formal_citations import (
    CITATION_TEMPLATES,
    CitationFormatter,
    FormalCitation,
    create_discovery_citation,
    create_formalized_citation,
)


class TestCreateCitations:
    def test_create_discovery_citation_returns_f1(self) -> None:
        c = create_discovery_citation()
        assert c.id == "F1"
        assert c.tool == "search"

    def test_create_formalized_citation_returns_f2(self) -> None:
        c = create_formalized_citation()
        assert c.id == "F2"
        assert c.tool == "logic"


class TestCitationFormatter:
    def test_format_inline_returns_string_with_brackets(self) -> None:
        c1 = FormalCitation(id="F1", label="test", tool="test", result="verified")
        c2 = FormalCitation(id="F2", label="test", tool="test", result="confirmed")
        result = CitationFormatter.format_inline([c1, c2])
        assert "[" in result
        assert "]" in result
        assert len(result) > 0

    def test_format_footnotes_produces_multiple_lines(self) -> None:
        c1 = FormalCitation(id="F1", label="Prior art found", tool="search", result="found")
        c2 = FormalCitation(id="CE", label="Counterexample found", tool="falsifier", result="falsified")
        result = CitationFormatter.format_footnotes([c1, c2])
        lines = result.split("\n")
        assert len(lines) == 2
        assert "[F1]" in lines[0]
        assert "[CE]" in lines[1]
        assert "search" in lines[0]
        assert "falsifier" in lines[1]

    def test_format_footnotes_empty_list(self) -> None:
        result = CitationFormatter.format_footnotes([])
        assert result == ""

    def test_to_terminal_all_verified_shows_checkmark(self) -> None:
        c1 = FormalCitation(id="F1", label="test", tool="test", result="verified")
        c2 = FormalCitation(id="F2", label="test", tool="test", result="confirmed")
        result = CitationFormatter.to_terminal([c1, c2])
        assert "Results:" in result
        assert "[2/2 ✓]" in result

    def test_to_terminal_with_falsified_shows_cross(self) -> None:
        c1 = FormalCitation(id="F1", label="test", tool="test", result="verified")
        c2 = FormalCitation(id="CE", label="test", tool="test", result="falsified")
        result = CitationFormatter.to_terminal([c1, c2])
        assert "[1/2 ✗]" in result

    def test_to_terminal_empty_list(self) -> None:
        result = CitationFormatter.to_terminal([])
        assert "[0/0 ✓]" in result


class TestCitationTemplates:
    def test_has_eight_entries(self) -> None:
        assert len(CITATION_TEMPLATES) >= 8
