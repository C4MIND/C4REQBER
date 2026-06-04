"""Tests for src/design/cli_output.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from design.cli_output import (
    ConfirmationPrompt,
    ErrorDisplay,
    PanelType,
    ProgressIndicator,
    ResultDisplay,
    StatusIndicator,
    StyledPanel,
    StyledTable,
    TreeDisplay,
    print_divider,
    print_empty_line,
    print_section_header,
)


class TestPanelType:
    def test_panel_type_values(self):
        assert PanelType.INFO.value["icon"] is not None
        assert PanelType.SUCCESS.value["border"] is not None
        assert PanelType.ERROR.value["title_style"] is not None
        assert PanelType.DISCOVERY.value["icon"] is not None
        assert PanelType.AGENT.value["border"] is not None
        assert PanelType.NEUTRAL.value["icon"] is not None
        assert PanelType.RESULT.value["border"] is not None
        assert PanelType.WARNING.value["icon"] is not None


class TestStyledPanel:
    def test_create_returns_panel(self):
        panel = StyledPanel.create("content", "Title", PanelType.INFO)
        assert isinstance(panel, Panel)

    def test_create_with_subtitle(self):
        panel = StyledPanel.create("content", "Title", PanelType.INFO, subtitle="sub")
        assert isinstance(panel, Panel)

    def test_info_shortcut(self):
        panel = StyledPanel.info("content")
        assert isinstance(panel, Panel)

    def test_success_shortcut(self):
        panel = StyledPanel.success("content")
        assert isinstance(panel, Panel)

    def test_warning_shortcut(self):
        panel = StyledPanel.warning("content")
        assert isinstance(panel, Panel)

    def test_error_shortcut(self):
        panel = StyledPanel.error("content")
        assert isinstance(panel, Panel)

    def test_result_shortcut(self):
        panel = StyledPanel.result("content")
        assert isinstance(panel, Panel)

    def test_discovery_shortcut(self):
        panel = StyledPanel.discovery("content")
        assert isinstance(panel, Panel)


class TestStyledTable:
    def test_create_returns_table(self):
        cols = [{"name": "Col1", "type": "id"}, {"name": "Col2", "type": "name"}]
        table = StyledTable.create("Test Table", cols)
        assert isinstance(table, Table)

    def test_create_with_options(self):
        cols = [{"name": "Col1", "type": "id", "width": 10, "justify": "center"}]
        table = StyledTable.create("Test", cols, show_header=False)
        assert isinstance(table, Table)

    def test_hypothesis_table(self):
        table = StyledTable.hypothesis_table()
        assert isinstance(table, Table)

    def test_discovery_table(self):
        table = StyledTable.discovery_table()
        assert isinstance(table, Table)

    def test_search_results_table(self):
        table = StyledTable.search_results_table()
        assert isinstance(table, Table)

    def test_column_styles_coverage(self):
        for col_type in StyledTable.COLUMN_STYLES:
            cols = [{"name": "Col", "type": col_type}]
            table = StyledTable.create("Test", cols)
            assert isinstance(table, Table)


class TestProgressIndicator:
    def test_discovery_progress(self):
        prog = ProgressIndicator.discovery_progress()
        assert prog is not None

    def test_search_progress(self):
        prog = ProgressIndicator.search_progress()
        assert prog is not None

    def test_agent_progress(self):
        prog = ProgressIndicator.agent_progress()
        assert prog is not None

    def test_validation_progress(self):
        prog = ProgressIndicator.validation_progress()
        assert prog is not None


class TestErrorDisplay:
    @patch("design.cli_output._displays.console.print")
    def test_show_error_raises(self, mock_print):
        with pytest.raises(SystemExit):
            ErrorDisplay.show_error("msg", suggestion="sugg", raise_exception=True)

    @patch("design.cli_output._displays.console.print")
    def test_show_error_no_raise(self, mock_print):
        ErrorDisplay.show_error("msg", raise_exception=False)
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_show_warning(self, mock_print):
        ErrorDisplay.show_warning("msg", suggestion="sugg")
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_show_info(self, mock_print):
        ErrorDisplay.show_info("msg", title="Title")
        mock_print.assert_called_once()


class TestResultDisplay:
    @patch("design.cli_output._displays.console.print")
    def test_hypothesis_card(self, mock_print):
        ResultDisplay.hypothesis_card("hyp", 0.75, "method")
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_hypothesis_card_with_path(self, mock_print):
        ResultDisplay.hypothesis_card("hyp", 0.5, "method", c4_path=["a", "b"])
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_hypothesis_card_with_evidence(self, mock_print):
        ResultDisplay.hypothesis_card("hyp", 0.5, "method", supporting_evidence=["e1", "e2"])
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_discovery_summary(self, mock_print):
        ResultDisplay.discovery_summary("problem", 3, 0.8, ["m1", "m2"])
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_metrics_grid(self, mock_print):
        ResultDisplay.metrics_grid({"a": 1, "b": 2})
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_agent_result(self, mock_print):
        ResultDisplay.agent_result("agent", "result")
        mock_print.assert_called_once()

    @patch("design.cli_output._displays.console.print")
    def test_agent_result_with_details(self, mock_print):
        ResultDisplay.agent_result("agent", "result", confidence=0.9, execution_time=1.5)
        mock_print.assert_called_once()


class TestStatusIndicator:
    def test_get_status_badge(self):
        badge = StatusIndicator.get_status_badge("success")
        assert "SUCCESS" in badge

    def test_get_status_badge_unknown(self):
        badge = StatusIndicator.get_status_badge("unknown_status")
        assert isinstance(badge, str)

    def test_get_confidence_bar_high(self):
        bar = StatusIndicator.get_confidence_bar(0.9)
        assert "90%" in bar

    def test_get_confidence_bar_medium(self):
        bar = StatusIndicator.get_confidence_bar(0.5)
        assert "50%" in bar

    def test_get_confidence_bar_low(self):
        bar = StatusIndicator.get_confidence_bar(0.2)
        assert "20%" in bar

    def test_get_loading_spinner(self):
        spinner = StatusIndicator.get_loading_spinner()
        assert "Loading" in spinner


class TestTreeDisplay:
    def test_create(self):
        tree = TreeDisplay.create("Root")
        assert isinstance(tree, Tree)

    def test_add_c4_path(self):
        tree = TreeDisplay.create("Root")
        TreeDisplay.add_c4_path(tree, [{"dimension": "Time", "value": "Past"}])
        assert isinstance(tree, Tree)

    def test_add_c4_path_empty(self):
        tree = TreeDisplay.create("Root")
        TreeDisplay.add_c4_path(tree, [])
        assert isinstance(tree, Tree)


class TestConfirmationPrompt:
    @patch("design.cli_output._widgets.console.print")
    def test_confirm_default_false(self, mock_print):
        result = ConfirmationPrompt.confirm("delete")
        assert result is False

    @patch("design.cli_output._widgets.console.print")
    def test_confirm_with_details(self, mock_print):
        result = ConfirmationPrompt.confirm("delete", details="This will remove data")
        assert result is False

    @patch("design.cli_output._widgets.console.print")
    def test_destructive(self, mock_print):
        result = ConfirmationPrompt.destructive("delete all")
        assert result is False

    @patch("design.cli_output._widgets.console.print")
    def test_destructive_with_details(self, mock_print):
        result = ConfirmationPrompt.destructive("delete all", details="irreversible")
        assert result is False


class TestPrintHelpers:
    @patch("design.cli_output._widgets.console.print")
    def test_print_section_header(self, mock_print):
        print_section_header("Section")
        assert mock_print.call_count == 3

    @patch("design.cli_output._widgets.console.print")
    def test_print_section_header_with_icon(self, mock_print):
        print_section_header("Section", icon="*")
        assert mock_print.call_count == 3

    @patch("design.cli_output._widgets.console.print")
    def test_print_divider(self, mock_print):
        print_divider()
        mock_print.assert_called_once()

    @patch("design.cli_output._widgets.console.print")
    def test_print_divider_custom_style(self, mock_print):
        print_divider(style="red")
        mock_print.assert_called_once()

    @patch("design.cli_output._widgets.console.print")
    def test_print_empty_line(self, mock_print):
        print_empty_line()
        mock_print.assert_called_once()
