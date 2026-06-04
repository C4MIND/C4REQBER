"""Tests for src/core/flywheel.py"""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from core.flywheel import DataFlywheel, FlywheelSnapshot


class TestFlywheelSnapshot:
    def test_creation(self):
        snap = FlywheelSnapshot(
            global_prior=0.5,
            discoveries_count=10,
            success_count=5,
            last_updated=12345.0,
            avg_papers_per_discovery=3.5,
        )
        assert snap.global_prior == 0.5
        assert snap.discoveries_count == 10


class TestDataFlywheelInit:
    def test_default_init(self):
        fw = DataFlywheel()
        assert fw.global_prior == 0.30
        assert fw.discoveries_count == 0
        assert fw.success_count == 0
        assert fw.total_papers_found == 0

    def test_init_loads_existing(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "global_prior": 0.45,
                "discoveries_count": 5,
                "success_count": 3,
                "total_papers_found": 20,
                "last_updated": 1000.0,
            }, f)
            path = f.name
        try:
            fw = DataFlywheel(persist_path=path)
            assert fw.global_prior == 0.45
            assert fw.discoveries_count == 5
            assert fw.success_count == 3
            assert fw.total_papers_found == 20
        finally:
            os.unlink(path)

    def test_init_loads_corrupted(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json")
            path = f.name
        try:
            fw = DataFlywheel(persist_path=path)
            assert fw.global_prior == 0.30  # fallback
        finally:
            os.unlink(path)


class TestDataFlywheelUpdate:
    def test_update_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw = DataFlywheel(persist_path=path)
            fw.update({"papers_found": 10, "status": "complete"})
            assert fw.discoveries_count == 1
            assert fw.success_count == 1
            assert fw.total_papers_found == 10
            assert fw.global_prior > 0.30  # posterior should increase

    def test_update_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw = DataFlywheel(persist_path=path)
            prior = fw.global_prior
            fw.update({"papers_found": 10, "status": "failed"})
            assert fw.discoveries_count == 1
            assert fw.success_count == 0
            # For failure, posterior can decrease
            assert fw.global_prior != prior

    def test_update_zero_papers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw = DataFlywheel(persist_path=path)
            fw.update({"papers_found": 0, "status": "complete"})
            assert fw.discoveries_count == 1

    def test_multiple_updates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw = DataFlywheel(persist_path=path)
            for i in range(5):
                fw.update({"papers_found": i + 1, "status": "complete"})
            assert fw.discoveries_count == 5
            assert fw.success_count == 5

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw1 = DataFlywheel(persist_path=path)
            fw1.update({"papers_found": 5, "status": "complete"})

            fw2 = DataFlywheel(persist_path=path)
            assert fw2.discoveries_count == 1
            assert fw2.total_papers_found == 5


class TestDataFlywheelGetStats:
    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw = DataFlywheel(persist_path=path)
            fw.update({"papers_found": 10, "status": "complete"})
            stats = fw.get_stats()
            assert stats["global_prior"] == fw.global_prior
            assert stats["discoveries"] == 1
            assert stats["successes"] == 1
            assert stats["success_rate"] == 1.0
            assert stats["total_papers"] == 10
            assert stats["avg_papers"] == 10.0

    def test_stats_no_discoveries(self):
        fw = DataFlywheel()
        stats = fw.get_stats()
        assert stats["discoveries"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_papers"] == 0.0


class TestDataFlywheelSnapshot:
    def test_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flywheel.json")
            fw = DataFlywheel(persist_path=path)
            fw.update({"papers_found": 5, "status": "complete"})
            snap = fw.snapshot()
            assert isinstance(snap, FlywheelSnapshot)
            assert snap.global_prior == fw.global_prior
            assert snap.discoveries_count == 1
            assert snap.avg_papers_per_discovery == 5.0


class TestDataFlywheelSaveLoadErrors:
    def test_save_permission_error(self):
        fw = DataFlywheel(persist_path="/nonexistent/dir/flywheel.json")
        # Should not raise
        fw.update({"papers_found": 1, "status": "complete"})

    def test_load_missing_file(self):
        fw = DataFlywheel(persist_path="/tmp/nonexistent_flywheel_12345.json")
        assert fw.global_prior == 0.30
