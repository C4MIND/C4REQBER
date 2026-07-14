from __future__ import annotations

from c4.structured_input import (
    PREFIXES,
    highlight_formal_notation,
    parse_structured_input,
    render_structured_sections,
)


class TestParseStructuredInput:
    def test_req_lines_go_to_req_section(self):
        text = "REQ: system must handle 1000 req/s\nREQ: latency under 10ms"
        sections = parse_structured_input(text)
        assert "REQ" in sections
        assert len(sections["REQ"]) == 2
        assert sections["REQ"][0] == "system must handle 1000 req/s"

    def test_mixed_input_uses_multiple_sections(self):
        text = "REQ: fast response\nHYP: caching reduces latency\nplain line"
        sections = parse_structured_input(text)
        assert "REQ" in sections
        assert "HYP" in sections
        assert len(sections["REQ"]) == 1
        assert len(sections["HYP"]) == 2
        assert sections["HYP"][1] == "plain line"

    def test_empty_input_returns_raw(self):
        sections = parse_structured_input("")
        assert sections == {}

    def test_plain_text_all_raw(self):
        sections = parse_structured_input("just some\nplain lines")
        assert "_raw" in sections
        assert len(sections["_raw"]) == 2

    def test_verify_prefix_parsed(self):
        text = "VERIFY: all gates pass"
        sections = parse_structured_input(text)
        assert "VERIFY" in sections
        assert sections["VERIFY"][0] == "all gates pass"


class TestRenderStructuredSections:
    def test_renders_req_section_with_tags(self):
        text = "REQ: fast response"
        rendered = render_structured_sections(text)
        assert "[cyan]REQ:[/]" in rendered
        assert "fast response" in rendered

    def test_renders_mixed_sections(self):
        text = "REQ: a\nHYP: b\nDATA: c"
        rendered = render_structured_sections(text)
        assert "REQ:" in rendered
        assert "HYP:" in rendered
        assert "DATA:" in rendered

    def test_renders_raw_lines_with_dim(self):
        text = "plain text"
        rendered = render_structured_sections(text)
        assert "[dim]plain text[/]" in rendered


class TestHighlightFormalNotation:
    def test_highlights_forall(self):
        result = highlight_formal_notation("forall x, exists y")
        assert "[bold yellow]forall[/]" in result
        assert "[bold yellow]exists[/]" in result
