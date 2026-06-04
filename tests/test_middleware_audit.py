"""Tests for src/api/middleware/audit.py"""
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestAuditTrail:
    def test_init_creates_parent_dir(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "subdir" / "audit.log"
        trail = AuditTrail(str(log_path))
        assert log_path.parent.exists()

    def test_log_action_appends_entry(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        trail.log_action(
            action="test_action",
            params={"key": "value"},
            result="success",
            cost={"usd": 1.5},
            session_id="sess_123",
            approval="approved",
        )

        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["action"] == "test_action"
        assert entry["params"] == {"key": "value"}
        assert entry["result"] == "success"
        assert entry["cost"] == {"usd": 1.5}
        assert entry["session_id"] == "sess_123"
        assert entry["approval"] == "approved"
        assert "timestamp" in entry

    def test_log_action_default_cost(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        trail.log_action(action="test", params={})

        lines = log_path.read_text().strip().split("\n")
        entry = json.loads(lines[0])
        assert entry["cost"] == {}

    def test_query_trail_empty_file(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        result = trail.query_trail()
        assert result == []

    def test_query_trail_no_file(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        log_path.unlink(missing_ok=True)
        result = trail.query_trail()
        assert result == []

    def test_query_trail_with_filter(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        trail.log_action(action="action_a", params={})
        trail.log_action(action="action_b", params={})
        trail.log_action(action="action_a", params={})

        result = trail.query_trail(action_filter="action_a")
        assert len(result) == 2
        assert all(e["action"] == "action_a" for e in result)

    def test_query_trail_session_filter(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        trail.log_action(action="test", params={}, session_id="sess_1")
        trail.log_action(action="test", params={}, session_id="sess_2")

        result = trail.query_trail(session_filter="sess_1")
        assert len(result) == 1
        assert result[0]["session_id"] == "sess_1"

    def test_query_trail_limit(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        for i in range(5):
            trail.log_action(action=f"action_{i}", params={})

        result = trail.query_trail(limit=2)
        assert len(result) == 2
        assert result[0]["action"] == "action_3"
        assert result[1]["action"] == "action_4"

    def test_query_trail_skips_bad_lines(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        log_path.write_text('{"action": "ok"}\nbad json\n{"action": "ok2"}\n')
        trail = AuditTrail(str(log_path))
        result = trail.query_trail()
        assert len(result) == 2
        assert result[0]["action"] == "ok"
        assert result[1]["action"] == "ok2"

    def test_rotate_log(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        trail._rotation_size = 10  # small for testing
        trail.log_action(action="test", params={"data": "x" * 100})

        backup = log_path.with_suffix(".log.1")
        assert backup.exists()
        # After rotation, original file is moved; next log_action recreates it
        trail._rotation_size = 10000  # prevent second rotation
        trail.log_action(action="test2", params={})
        assert log_path.exists()

    def test_get_statistics_empty(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        stats = trail.get_statistics()
        assert stats["total_entries"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["total_cost_usd"] == 0.0
        assert stats["actions_by_type"] == {}

    def test_get_statistics_with_data(self, tmp_path):
        from src.api.middleware.audit import AuditTrail

        log_path = tmp_path / "audit.log"
        trail = AuditTrail(str(log_path))
        trail.log_action(action="read", params={}, result="success", cost={"usd": 1.0})
        trail.log_action(action="read", params={}, result="success", cost={"usd": 2.0})
        trail.log_action(action="write", params={}, result="failure", cost={"usd": 0.5})

        stats = trail.get_statistics()
        assert stats["total_entries"] == 3
        assert stats["actions_by_type"]["read"] == 2
        assert stats["actions_by_type"]["write"] == 1
        assert stats["success_rate"] == 2 / 3
        assert stats["total_cost_usd"] == 3.5
