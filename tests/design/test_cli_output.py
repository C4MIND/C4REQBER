"""Tests for src/design/cli_output.py — CLI output formatting."""
from __future__ import annotations

from src.design.cli_output import (
    PanelType,
    StyledPanel,
    StyledTable,
    print_divider,
    print_section_header,
)


class TestPanelType:
    def test_all_panel_types_exist(self):
        for pt in PanelType:
            assert pt.value["border"]
            assert pt.value["icon"]


class TestStyledPanel:
    def test_create_info(self):
        panel = StyledPanel.create("Content here", title="Test", panel_type=PanelType.INFO)
        assert panel is not None

    def test_create_success(self):
        panel = StyledPanel.create("Done", title="Success", panel_type=PanelType.SUCCESS)
        assert panel is not None

    def test_create_error(self):
        panel = StyledPanel.create("Failed", title="Error", panel_type=PanelType.ERROR)
        assert panel is not None


class TestStyledTable:
    def test_create(self):
        columns = [
            {"name": "Name", "key": "name"},
            {"name": "Value", "key": "value"},
        ]
        table = StyledTable.create(title="Results", columns=columns)
        assert table is not None


class TestPrintFunctions:
    def test_section_header_returns(self):
        result = print_section_header("Test Section")
        assert result is None

    def test_divider_returns(self):
        result = print_divider()
        assert result is None
