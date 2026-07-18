"""Smoke tests for TUI binary locator and LLM gateway public API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.cli.tui_binary import _platform_asset_suffix, find_tui_v9_binary
from src.llm import generate_with_fallback, get_gateway
from src.llm.gateway import DefaultGateway


def test_platform_asset_suffix_known():
    suffix = _platform_asset_suffix()
    assert suffix is None or any(suffix.startswith(p) for p in ("linux-", "darwin-", "windows-"))


def test_find_tui_binary_dev_tree_or_none():
    # Dev machine may have bin/c4tui-v9; CI may not — both OK.
    found = find_tui_v9_binary()
    assert found is None or (isinstance(found, Path) and found.is_file())


def test_get_gateway_singleton():
    a = get_gateway()
    b = get_gateway()
    assert a is b
    assert isinstance(a, DefaultGateway)


def test_generate_with_fallback_delegates_to_gateway():
    gw = get_gateway()
    with patch.object(gw, "generate_sync", return_value="ok") as mock_sync:
        out = generate_with_fallback("hi", preferred_model="x")
        assert out == "ok"
        mock_sync.assert_called_once()
        assert mock_sync.call_args.kwargs.get("preferred_model") == "x"
