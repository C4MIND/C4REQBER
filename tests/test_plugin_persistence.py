"""
Tests for plugin result persistence.
"""
import json
import os
import tempfile

import pytest

from src.plugins.persistence import PluginResultStore


class TestPluginResultStore:
    """Test suite for PluginResultStore."""

    @pytest.fixture
    def store(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        store = PluginResultStore(db_path=path)
        yield store
        store.close()
        os.unlink(path)

    def test_save_and_get(self, store):
        result = {"strengths": ["Brand"], "weaknesses": ["Cost"]}
        row_id = store.save("swot", "Analyze our startup", result)
        assert isinstance(row_id, int)
        assert row_id > 0

        cached = store.get("swot", "Analyze our startup")
        assert cached is not None
        assert cached["result"] == result
        assert cached["metadata"] is None
        assert "created_at" in cached

    def test_get_nonexistent(self, store):
        assert store.get("swot", "nonexistent problem") is None

    def test_get_wrong_plugin(self, store):
        store.save("swot", "problem", {"data": "x"})
        assert store.get("five_whys", "problem") is None

    def test_list_recent(self, store):
        for i in range(3):
            store.save("swot", f"problem {i}", {"index": i})
        recent = store.list_recent(limit=2)
        assert len(recent) == 2
        # Most recent first
        assert recent[0]["result"]["index"] == 2

    def test_list_recent_default_limit(self, store):
        for i in range(60):
            store.save("swot", f"problem {i}", {"index": i})
        recent = store.list_recent()
        assert len(recent) == 50  # default limit

    def test_save_with_metadata(self, store):
        result = {"output": "ok"}
        meta = {"source": "test", "version": 1}
        store.save("plugin_a", "task", result, metadata=meta)
        cached = store.get("plugin_a", "task")
        assert cached["metadata"] == meta

    def test_problem_hash_stability(self, store):
        store.save("swot", "hello", {"a": 1})
        cached = store.get("swot", "hello")
        assert cached is not None
        # Different problem = different hash
        assert store.get("swot", "hello ") is None

    def test_multiple_plugins_same_problem(self, store):
        store.save("swot", "same", {"type": "swot"})
        store.save("five_whys", "same", {"type": "five_whys"})
        assert store.get("swot", "same")["result"]["type"] == "swot"
        assert store.get("five_whys", "same")["result"]["type"] == "five_whys"

    def test_persistence_across_instances(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            store1 = PluginResultStore(db_path=path)
            store1.save("swot", "persist me", {"key": "value"})
            store1.close()

            store2 = PluginResultStore(db_path=path)
            cached = store2.get("swot", "persist me")
            assert cached is not None
            assert cached["result"]["key"] == "value"
            store2.close()
        finally:
            os.unlink(path)
