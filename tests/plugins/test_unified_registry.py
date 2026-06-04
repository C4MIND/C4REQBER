"""Tests for src/plugins/unified_registry.py — PluginRegistry and PluginInfo."""
from __future__ import annotations

import inspect
import math

from src.plugins.unified_registry import (
    PluginInfo,
    PluginRegistry,
    _populate_plugin_infos_into,
    _register_plugin_info,
)


class TestPluginInfo:
    def test_dataclass_creation(self) -> None:
        info = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            description="A test plugin",
            category="test",
            execute_fn=math.sqrt,
            icon="star",
        )
        assert info.id == "test_plugin"
        assert info.name == "Test Plugin"
        assert info.description == "A test plugin"
        assert info.category == "test"
        assert info.execute_fn(16) == 4.0
        assert info.icon == "star"

    def test_default_icon(self) -> None:
        info = PluginInfo(
            id="bare",
            name="Bare",
            description="No icon specified",
            category="misc",
            execute_fn=lambda: None,
        )
        assert info.icon == "puzzle"


class TestPluginRegistryInit:
    def test_empty_init(self) -> None:
        registry = PluginRegistry()
        assert len(registry) == 0
        assert len(list(registry.keys())) == 0
        assert registry.get_plugin_info("nonexistent") is None


class TestRegisterPluginInfo:
    def test_adds_plugin_to_registry(self) -> None:
        registry = PluginRegistry()
        _register_plugin_info(
            registry,
            "math_sqrt",
            "Math Sqrt",
            "Square root function",
            "math",
            "math",
            "sqrt",
        )
        info = registry.get_plugin_info("math_sqrt")
        assert info is not None
        assert info.id == "math_sqrt"
        assert info.name == "Math Sqrt"
        assert info.execute_fn(16) == 4.0

    def test_dict_access(self) -> None:
        registry = PluginRegistry()
        _register_plugin_info(
            registry,
            "my_fabs",
            "My Fabs",
            "Absolute float value",
            "utils",
            "math",
            "fabs",
        )
        info = registry["my_fabs"]
        assert info is not None
        assert info.execute_fn(-5.0) == 5.0


class TestPopulatePluginInfos:
    def test_count_after_populate(self) -> None:
        registry = PluginRegistry()
        _populate_plugin_infos_into(registry)
        count = len(registry)
        assert count >= 28, f"Expected at least 28 plugins, got {count}"

    def test_plugin_lookup_by_id(self) -> None:
        registry = PluginRegistry()
        _populate_plugin_infos_into(registry)
        info = registry.get_plugin_info("swot")
        assert info is not None
        assert info.name == "SWOT Analysis"
        assert info.category == "strategy"

    def test_wasm_plugins_present_in_source(self) -> None:
        source = inspect.getsource(_populate_plugin_infos_into)
        assert "@wasm" in source
        for wasm_id in ["monte_carlo_pi", "matrix_mult", "text_distance", "hash_fingerprint"]:
            assert wasm_id in source, f"WASM plugin {wasm_id} not found in source"


class TestPluginRegistryLen:
    def test_len_reflects_registered_plugins(self) -> None:
        registry = PluginRegistry()
        assert len(registry) == 0
        _register_plugin_info(
            registry, "a", "A", "Desc A", "cat", "math", "acos",
        )
        assert len(registry) == 1
        _register_plugin_info(
            registry, "b", "B", "Desc B", "cat", "math", "asin",
        )
        assert len(registry) == 2
