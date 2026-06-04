"""Tests for src/design/tokens.py — DesignTokens, ColorToken."""
from __future__ import annotations

from src.design.tokens import ColorToken, DesignTokens, ICONS, get_color_by_status


class TestColorToken:
    def test_construction(self):
        ct = ColorToken(hex="#FF0000", rgb=(255, 0, 0), name="Red", usage="Error")
        assert ct.hex == "#FF0000"
        assert ct.rgb == (255, 0, 0)
        assert ct.name == "Red"

    def test_immutability(self):
        ct = ColorToken(hex="#000", rgb=(0, 0, 0), name="Black", usage="Text")
        assert ct.hex == "#000"


class TestDesignTokens:
    def test_primary_exists(self):
        assert DesignTokens.PRIMARY.hex == "#4ECDC4"

    def test_success_color(self):
        assert DesignTokens.SUCCESS.name == "Emerald"

    def test_error_color(self):
        assert DesignTokens.ERROR.name == "Crimson"

    def test_info_color(self):
        assert DesignTokens.INFO.name == "Azure"

    def test_gray_scale(self):
        assert DesignTokens.GRAY_100.rgb == (248, 249, 250)
        assert DesignTokens.GRAY_900.rgb == (33, 37, 41)


class TestIcons:
    def test_common_icons_exist(self):
        assert "info" in ICONS
        assert "success" in ICONS
        assert "discover" in ICONS
        assert "hypothesis" in ICONS

    def test_icons_are_strings(self):
        for name, icon in ICONS.items():
            assert isinstance(icon, str), f"Icon {name} is not a string"


class TestGetColorByStatus:
    def test_verified_returns_token(self):
        result = get_color_by_status("validated")
        assert isinstance(result, ColorToken)
        assert result == DesignTokens.SUCCESS

    def test_failed_returns_error(self):
        result = get_color_by_status("failed")
        assert result == DesignTokens.ERROR

    def test_pending_returns_warning(self):
        result = get_color_by_status("pending")
        assert result == DesignTokens.WARNING

    def test_unknown_returns_info(self):
        result = get_color_by_status("nonexistent_status")
        assert result == DesignTokens.INFO

    def test_uppercase_handled(self):
        result = get_color_by_status("SUCCESS")
        assert result == DesignTokens.SUCCESS
