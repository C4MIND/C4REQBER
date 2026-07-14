"""
Comprehensive tests for src/plugins/persistence.py

Covers: PluginResultStore save/load, listing, hashing, metadata,
thread-local connections, and cross-instance persistence.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time

import pytest

from src.plugins.persistence import PluginResultStore


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def store():
    """Fresh PluginResultStore backed by a temporary SQLite file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    s = PluginResultStore(db_path=path)
    yield s
    s.close()
    os.unlink(path)


@pytest.fixture
def store_path():
    """Yield a temp path without creating the store (for cross-instance tests)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


# ═══════════════════════════════════════════════════════════════════
# SAVE / GET
# ═══════════════════════════════════════════════════════════════════


class TestSaveAndGet:
    def test_save_returns_positive_row_id(self, store):
        row_id = store.save("swot", "Analyze startup", {"s": ["brand"]})
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_save_and_get_roundtrip(self, store):
        result = {"strengths": ["Brand"], "weaknesses": ["Cost"]}
        store.save("swot", "Analyze our startup", result)
        cached = store.get("swot", "Analyze our startup")
        assert cached is not None
        assert cached["result"] == result
        assert cached["metadata"] is None
        assert "created_at" in cached

    def test_get_nonexistent_returns_none(self, store):
        assert store.get("swot", "does not exist") is None

    def test_get_wrong_plugin(self, store):
        store.save("swot", "problem", {"data": "x"})
        assert store.get("five_whys", "problem") is None

    def test_get_wrong_problem(self, store):
        store.save("swot", "problem A", {"data": "x"})
        assert store.get("swot", "problem B") is None

    def test_save_overwrites_previous(self, store):
        store.save("swot", "same", {"v": 1})
        store.save("swot", "same", {"v": 2})
        cached = store.get("swot", "same")
        assert cached["result"] == {"v": 2}


# ═══════════════════════════════════════════════════════════════════
# METADATA
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    def test_save_with_metadata(self, store):
        result = {"output": "ok"}
        meta = {"source": "test", "version": 1}
        store.save("plugin_a", "task", result, metadata=meta)
        cached = store.get("plugin_a", "task")
        assert cached["metadata"] == meta

    def test_save_with_none_metadata(self, store):
        store.save("p", "t", {"r": 1}, metadata=None)
        cached = store.get("p", "t")
        assert cached["metadata"] is None

    def test_save_with_empty_metadata(self, store):
        store.save("p", "t", {"r": 1}, metadata={})
        cached = store.get("p", "t")
        assert cached["metadata"] is None


# ═══════════════════════════════════════════════════════════════════
# PROBLEM HASHING
# ═══════════════════════════════════════════════════════════════════


class TestProblemHashing:
    def test_same_problem_same_hash(self, store):
        store.save("swot", "hello", {"a": 1})
        assert store.get("swot", "hello") is not None

    def test_different_problem_different_hash(self, store):
        store.save("swot", "hello", {"a": 1})
        assert store.get("swot", "hello ") is None
        assert store.get("swot", "Hello") is None

    def test_unicode_problem_hashing(self, store):
        store.save("swot", "привет мир 🔬", {"a": 1})
        cached = store.get("swot", "привет мир 🔬")
        assert cached is not None
        assert cached["result"] == {"a": 1}


# ═══════════════════════════════════════════════════════════════════
# LIST RECENT
# ═══════════════════════════════════════════════════════════════════


class TestListRecent:
    def test_list_recent_ordered_by_time_desc(self, store):
        for i in range(3):
            store.save("swot", f"problem {i}", {"index": i})
        recent = store.list_recent(limit=2)
        assert len(recent) == 2
        assert recent[0]["result"]["index"] == 2
        assert recent[1]["result"]["index"] == 1

    def test_list_recent_default_limit_50(self, store):
        for i in range(60):
            store.save("swot", f"problem {i}", {"index": i})
        recent = store.list_recent()
        assert len(recent) == 50

    def test_list_recent_custom_limit(self, store):
        for i in range(5):
            store.save("swot", f"problem {i}", {"index": i})
        recent = store.list_recent(limit=3)
        assert len(recent) == 3

    def test_list_recent_returns_all_fields(self, store):
        store.save("swot", "p", {"k": "v"}, metadata={"m": 1})
        recent = store.list_recent(limit=1)
        assert len(recent) == 1
        item = recent[0]
        assert "id" in item
        assert "plugin_id" in item
        assert "problem_hash" in item
        assert "result" in item
        assert "metadata" in item
        assert "created_at" in item

    def test_list_recent_empty_store(self, store):
        assert store.list_recent() == []


# ═══════════════════════════════════════════════════════════════════
# MULTIPLE PLUGINS SAME PROBLEM
# ═══════════════════════════════════════════════════════════════════


class TestMultiplePlugins:
    def test_same_problem_different_plugins(self, store):
        store.save("swot", "same", {"type": "swot"})
        store.save("five_whys", "same", {"type": "five_whys"})
        assert store.get("swot", "same")["result"]["type"] == "swot"
        assert store.get("five_whys", "same")["result"]["type"] == "five_whys"

    def test_list_recent_shows_all_plugins(self, store):
        store.save("a", "p", {"x": 1})
        store.save("b", "p", {"x": 2})
        recent = store.list_recent(limit=10)
        plugin_ids = {r["plugin_id"] for r in recent}
        assert plugin_ids == {"a", "b"}


# ═══════════════════════════════════════════════════════════════════
# CROSS-INSTANCE PERSISTENCE
# ═══════════════════════════════════════════════════════════════════


class TestCrossInstancePersistence:
    def test_data_survives_instance_recreation(self, store_path):
        store1 = PluginResultStore(db_path=store_path)
        store1.save("swot", "persist me", {"key": "value"})
        store1.close()

        store2 = PluginResultStore(db_path=store_path)
        cached = store2.get("swot", "persist me")
        assert cached is not None
        assert cached["result"]["key"] == "value"
        store2.close()

    def test_schema_recreated_on_new_instance(self, store_path):
        store1 = PluginResultStore(db_path=store_path)
        store1.save("x", "y", {"z": 1})
        store1.close()

        store2 = PluginResultStore(db_path=store_path)
        # Table should already exist; no error
        cached = store2.get("x", "y")
        assert cached["result"] == {"z": 1}
        store2.close()


# ═══════════════════════════════════════════════════════════════════
# THREAD SAFETY
# ═══════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_thread_local_connections(self, store):
        results = []

        def worker():
            row_id = store.save("swot", "thread-test", {"thread": threading.current_thread().name})
            results.append(row_id)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5
        assert all(isinstance(r, int) and r > 0 for r in results)

    def test_concurrent_reads_and_writes(self, store):
        errors = []

        def writer(n):
            try:
                store.save("swot", f"w{n}", {"n": n})
            except Exception as e:
                errors.append(e)

        def reader(n):
            try:
                store.get("swot", f"w{n}")
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=writer, args=(i,)))
            threads.append(threading.Thread(target=reader, args=(i,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []


# ═══════════════════════════════════════════════════════════════════
# CLOSE
# ═══════════════════════════════════════════════════════════════════


class TestClose:
    def test_close_clears_connection(self, store):
        store.save("p", "t", {"r": 1})
        store.close()
        # After close, a new operation should still work because
        # _get_conn will recreate the connection.
        store.save("p", "t2", {"r": 2})
        assert store.get("p", "t2") is not None

    def test_close_idempotent(self, store):
        store.close()
        store.close()  # should not raise


# ═══════════════════════════════════════════════════════════════════
# SERIALIZATION
# ═══════════════════════════════════════════════════════════════════


class TestSerialization:
    def test_result_with_none_values(self, store):
        result = {"a": None, "b": "value"}
        store.save("p", "t", result)
        cached = store.get("p", "t")
        assert cached["result"]["a"] is None
        assert cached["result"]["b"] == "value"

    def test_result_with_boolean_values(self, store):
        result = {"flag": True, "other": False}
        store.save("p", "t", result)
        cached = store.get("p", "t")
        assert cached["result"]["flag"] is True
        assert cached["result"]["other"] is False

    def test_result_with_float_values(self, store):
        result = {"pi": 3.14159, "e": 2.71828}
        store.save("p", "t", result)
        cached = store.get("p", "t")
        assert abs(cached["result"]["pi"] - 3.14159) < 1e-6

    def test_result_with_list_of_dicts(self, store):
        result = {"items": [{"id": 1}, {"id": 2}]}
        store.save("p", "t", result)
        cached = store.get("p", "t")
        assert len(cached["result"]["items"]) == 2
        assert cached["result"]["items"][0]["id"] == 1

    def test_metadata_with_nested_structure(self, store):
        meta = {"config": {"depth": 3, "enabled": True}, "tags": ["a", "b"]}
        store.save("p", "t", {"r": 1}, metadata=meta)
        cached = store.get("p", "t")
        assert cached["metadata"]["config"]["depth"] == 3
        assert cached["metadata"]["tags"] == ["a", "b"]


# ═══════════════════════════════════════════════════════════════════
# VERSIONING
# ═══════════════════════════════════════════════════════════════════


class TestVersioning:
    def test_multiple_saves_create_multiple_versions(self, store):
        store.save("p", "t", {"v": 1})
        time.sleep(0.01)
        store.save("p", "t", {"v": 2})
        time.sleep(0.01)
        store.save("p", "t", {"v": 3})
        recent = store.list_recent(limit=5)
        # Most recent should be v=3
        assert recent[0]["result"] == {"v": 3}

    def test_version_timestamps_increase(self, store):
        store.save("p", "t", {"v": 1})
        time.sleep(0.01)
        store.save("p", "t", {"v": 2})
        recent = store.list_recent(limit=2)
        assert recent[0]["created_at"] > recent[1]["created_at"]

    def test_get_returns_latest_version(self, store):
        store.save("p", "t", {"v": 1})
        time.sleep(0.01)
        store.save("p", "t", {"v": 2})
        cached = store.get("p", "t")
        assert cached["result"] == {"v": 2}

    def test_different_plugins_same_problem_versioned_independently(self, store):
        store.save("a", "t", {"v": 1})
        time.sleep(0.01)
        store.save("b", "t", {"v": 2})
        time.sleep(0.01)
        store.save("a", "t", {"v": 3})
        assert store.get("a", "t")["result"] == {"v": 3}
        assert store.get("b", "t")["result"] == {"v": 2}


# ═══════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_result(self, store):
        store.save("p", "t", {})
        cached = store.get("p", "t")
        assert cached["result"] == {}

    def test_large_result(self, store):
        large = {"items": list(range(10000))}
        store.save("p", "t", large)
        cached = store.get("p", "t")
        assert cached["result"] == large

    def test_nested_json(self, store):
        nested = {"a": {"b": {"c": [1, 2, {"d": "e"}]}}}
        store.save("p", "t", nested)
        cached = store.get("p", "t")
        assert cached["result"] == nested

    def test_special_characters_in_problem(self, store):
        problem = "Problem with \"quotes\" and 'apostrophes' and \\backslashes"
        store.save("p", problem, {"r": 1})
        cached = store.get("p", problem)
        assert cached is not None

    def test_very_long_problem(self, store):
        problem = "x" * 10000
        store.save("p", problem, {"r": 1})
        cached = store.get("p", problem)
        assert cached is not None
