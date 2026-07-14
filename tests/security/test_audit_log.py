"""
Tests for TURBO-CDI Audit Logging System
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from src.security.audit_log import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    FileBackend,
    MemoryBackend,
    get_audit_logger,
    reset_audit_logger,
)


class TestAuditEvent:
    def test_event_creation(self) -> None:
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user@example.com",
            action="login",
            resource="auth",
        )
        assert event.event_type == AuditEventType.AUTH_LOGIN
        assert event.actor == "user@example.com"
        assert event.status == "success"
        assert event.event_id
        assert event.timestamp

    def test_hash_computation(self) -> None:
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            actor="admin",
            action="read",
            resource="users",
        )
        event.finalize()
        assert event._hash
        assert len(event._hash) == 64  # SHA-256 hex
        assert event.verify() is True

    def test_hash_chain(self) -> None:
        event1 = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user1",
            action="login",
            resource="auth",
        )
        event1.finalize("genesis")

        event2 = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            actor="user1",
            action="read",
            resource="data",
        )
        event2.finalize(event1._hash)

        assert event2.previous_hash == event1._hash
        assert event2.verify() is True

    def test_sanitization(self) -> None:
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user",
            action="login",
            resource="auth",
            details={"password": "secret123", "token": "abc", "normal": "ok"},
        )
        sanitized = event._sanitize_details()
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["normal"] == "ok"

    def test_to_dict(self) -> None:
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user",
            action="login",
            resource="auth",
        )
        event.finalize()
        data = event.to_dict()
        assert "hash" in data
        assert data["event_type"] == "auth.login"
        assert data["actor"] == "user"

    def test_to_json(self) -> None:
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user",
            action="login",
            resource="auth",
        )
        event.finalize()
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "auth.login"
        assert parsed["hash"]


class TestMemoryBackend:
    def test_write_and_read(self) -> None:
        backend = MemoryBackend()
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user",
            action="login",
            resource="auth",
        )
        backend.write(event)
        events = backend.read()
        assert len(events) == 1
        assert events[0].actor == "user"

    def test_read_with_filter(self) -> None:
        backend = MemoryBackend()
        backend.write(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="alice",
                action="login",
                resource="auth",
            )
        )
        backend.write(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGOUT,
                actor="bob",
                action="logout",
                resource="auth",
            )
        )
        events = backend.read(filters={"actor": "alice"})
        assert len(events) == 1
        assert events[0].actor == "alice"

    def test_clear(self) -> None:
        backend = MemoryBackend()
        backend.write(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="user",
                action="login",
                resource="auth",
            )
        )
        backend.clear()
        assert len(backend.read()) == 0

    def test_hash_chain_integrity(self) -> None:
        backend = MemoryBackend()
        event1 = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user",
            action="login",
            resource="auth",
        )
        backend.write(event1)
        event2 = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            actor="user",
            action="read",
            resource="data",
        )
        backend.write(event2)

        assert event2.previous_hash == event1._hash


class TestFileBackend:
    def test_write_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            event = AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="user",
                action="login",
                resource="auth",
            )
            backend.write(event)
            events = backend.read()
            assert len(events) == 1
            assert events[0].actor == "user"

    def test_file_rotation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir, max_file_size=1)
            for i in range(5):
                event = AuditEvent(
                    event_type=AuditEventType.AUTH_LOGIN,
                    actor=f"user{i}",
                    action="login",
                    resource="auth",
                )
                backend.write(event)

            files = list(os.listdir(tmpdir))
            assert len(files) > 1  # Rotation occurred

    def test_verify_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            for i in range(3):
                event = AuditEvent(
                    event_type=AuditEventType.AUTH_LOGIN,
                    actor=f"user{i}",
                    action="login",
                    resource="auth",
                )
                backend.write(event)

            valid, errors = backend.verify_chain()
            assert valid is True
            assert errors == []

    def test_read_with_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            backend.write(
                AuditEvent(
                    event_type=AuditEventType.AUTH_LOGIN,
                    actor="alice",
                    action="login",
                    resource="auth",
                )
            )
            backend.write(
                AuditEvent(
                    event_type=AuditEventType.AUTH_LOGOUT,
                    actor="bob",
                    action="logout",
                    resource="auth",
                )
            )
            events = backend.read(filters={"actor": "alice"})
            assert len(events) == 1
            assert events[0].actor == "alice"

    def test_read_with_since_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            backend.write(
                AuditEvent(
                    event_type=AuditEventType.AUTH_LOGIN,
                    actor="alice",
                    action="login",
                    resource="auth",
                )
            )
            events = backend.read(filters={"since": "9999-01-01T00:00:00"})
            assert len(events) == 0

    def test_read_with_until_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            backend.write(
                AuditEvent(
                    event_type=AuditEventType.AUTH_LOGIN,
                    actor="alice",
                    action="login",
                    resource="auth",
                )
            )
            events = backend.read(filters={"until": "1970-01-01T00:00:00"})
            assert len(events) == 0

    def test_verify_chain_broken(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            event = AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="user",
                action="login",
                resource="auth",
            )
            backend.write(event)
            # Tamper with the file to break the chain
            files = list(os.listdir(tmpdir))
            with open(os.path.join(tmpdir, files[0]), "w") as f:
                f.write('{"previous_hash": "tampered", "hash": "fake"}\n')
            valid, errors = backend.verify_chain()
            assert valid is False
            assert len(errors) > 0

    def test_verify_chain_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            event = AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="user",
                action="login",
                resource="auth",
            )
            backend.write(event)
            files = list(os.listdir(tmpdir))
            with open(os.path.join(tmpdir, files[0]), "a") as f:
                f.write("not json\n")
            valid, errors = backend.verify_chain()
            assert valid is False
            assert len(errors) > 0

    def test_read_empty_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            event = AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="user",
                action="login",
                resource="auth",
            )
            backend.write(event)
            files = list(os.listdir(tmpdir))
            with open(os.path.join(tmpdir, files[0]), "a") as f:
                f.write("\n")
            events = backend.read()
            assert len(events) == 1

    def test_read_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            event = AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor="user",
                action="login",
                resource="auth",
            )
            backend.write(event)
            files = list(os.listdir(tmpdir))
            with open(os.path.join(tmpdir, files[0]), "a") as f:
                f.write("not json\n")
            events = backend.read()
            assert len(events) == 1


class TestAuditLogger:
    def setup_method(self) -> None:
        reset_audit_logger()

    def teardown_method(self) -> None:
        reset_audit_logger()

    def test_log_basic(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        event = logger.log(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user@example.com",
            action="login",
            resource="auth",
        )
        assert event.event_type == AuditEventType.AUTH_LOGIN
        assert event._hash

    def test_log_auth_login(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        event = logger.log_auth_login("user@example.com", success=True)
        assert event.event_type == AuditEventType.AUTH_LOGIN
        assert event.status == "success"

        event = logger.log_auth_login("user@example.com", success=False)
        assert event.event_type == AuditEventType.AUTH_FAILED
        assert event.status == "failed"
        assert event.severity == AuditSeverity.WARNING

    def test_log_data_access(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        event = logger.log_data_access("user", "users", action="read")
        assert event.event_type == AuditEventType.DATA_ACCESS
        assert event.action == "read"

    def test_log_security_alert(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        event = logger.log_security_alert(
            "system", "brute_force_detected", severity=AuditSeverity.CRITICAL
        )
        assert event.event_type == AuditEventType.SECURITY_ALERT
        assert event.severity == AuditSeverity.CRITICAL
        assert event.status == "alert"

    def test_log_admin_action(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        event = logger.log_admin_action("admin", "delete_user", "users")
        assert event.event_type == AuditEventType.ADMIN_ACTION
        assert event.severity == AuditSeverity.WARNING

    def test_query(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        logger.log_auth_login("alice", success=True)
        logger.log_auth_login("bob", success=True)
        logger.log_auth_login("alice", success=False)

        events = logger.query(filters={"actor": "alice"})
        assert len(events) == 2

    def test_query_with_since_until(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        logger.log_auth_login("alice", success=True)

        events = logger.query(filters={"since": "9999-01-01T00:00:00"})
        assert len(events) == 0

        events = logger.query(filters={"until": "1970-01-01T00:00:00"})
        assert len(events) == 0

    def test_verify_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(log_dir=tmpdir)
            logger = get_audit_logger(backend)
            logger.log_auth_login("user", success=True)
            logger.log_data_access("user", "data")

            valid, errors = logger.verify_integrity()
            assert valid is True
            assert errors == []

    def test_verify_integrity_memory_backend(self) -> None:
        backend = MemoryBackend()
        logger = get_audit_logger(backend)
        logger.log_auth_login("user", success=True)

        valid, errors = logger.verify_integrity()
        assert valid is True
        assert errors == []

    def test_singleton(self) -> None:
        reset_audit_logger()
        backend = MemoryBackend()
        logger1 = get_audit_logger(backend)
        logger2 = get_audit_logger()
        assert logger1 is logger2
