"""
C4REQBER: Comprehensive Audit Logging System
Structured JSON audit logs for security compliance and forensics.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from src.compat import UTC


class AuditEventType(StrEnum):
    """AuditEventType."""

    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    DATA_ACCESS = "data.access"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    ADMIN_ACTION = "admin.action"
    CONFIG_CHANGED = "config.changed"
    SECURITY_ALERT = "security.alert"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    RATE_LIMIT_HIT = "rate_limit.hit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    HSM_OPERATION = "hsm.operation"


class AuditSeverity(StrEnum):
    """AuditSeverity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event with tamper-evident hash chain."""

    event_type: AuditEventType
    actor: str
    action: str
    resource: str
    severity: AuditSeverity = AuditSeverity.INFO
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    status: str = "success"
    details: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    _hash: str = field(default="", repr=False)

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of event data for tamper evidence."""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "severity": self.severity.value,
            "status": self.status,
            "details": self._sanitize_details(),
            "previous_hash": self.previous_hash,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _sanitize_details(self) -> dict[str, Any]:
        """Remove sensitive fields from details for hashing."""
        sensitive = {"password", "token", "secret", "api_key", "private_key", "credit_card"}
        return {k: "***REDACTED***" if k in sensitive else v for k, v in self.details.items()}

    def finalize(self, previous_hash: str = "") -> AuditEvent:
        """Finalize event with hash chain link."""
        self.previous_hash = previous_hash
        self._hash = self.compute_hash()
        return self

    def verify(self) -> bool:
        """Verify event integrity."""
        return self._hash == self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """Export as dictionary for JSON serialization."""
        result = asdict(self)
        result["hash"] = self._hash
        result["event_type"] = self.event_type.value
        result["severity"] = self.severity.value
        del result["_hash"]
        return result

    def to_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogBackend(ABC):
    """Abstract audit log backend — use FileBackend (or Memory) in production."""

    @abstractmethod
    def write(self, event: AuditEvent) -> None: ...

    @abstractmethod
    def read(self, filters: dict[str, Any] | None = None, limit: int = 100) -> list[AuditEvent]: ...


class FileBackend(AuditLogBackend):
    """File-based audit log backend with rotation."""

    def __init__(self, log_dir: str | None = None, max_file_size: int = 10_485_760) -> None:
        self.log_dir = Path(log_dir or os.getenv("AUDIT_LOG_DIR") or "logs/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self._lock = threading.Lock()
        self._current_file: Path | None = None
        self._last_hash: str = ""

    def _get_current_file(self) -> Path:
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        return self.log_dir / f"audit-{date_str}.ndjson"

    def _rotate_if_needed(self, filepath: Path) -> Path:
        if filepath.exists() and filepath.stat().st_size > self.max_file_size:
            timestamp = datetime.now(UTC).strftime("%H%M%S")
            rotated = filepath.with_suffix(f".{timestamp}.ndjson")
            filepath.rename(rotated)
        return filepath

    def write(self, event: AuditEvent) -> None:
        with self._lock:
            event.finalize(self._last_hash)
            self._last_hash = event._hash
            filepath = self._get_current_file()
            filepath = self._rotate_if_needed(filepath)
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
                f.flush()
                os.fsync(f.fileno())

    def read(self, filters: dict[str, Any] | None = None, limit: int = 100) -> list[AuditEvent]:
        """Read."""
        events: list[AuditEvent] = []
        files = sorted(self.log_dir.glob("audit-*.ndjson"), reverse=True)
        for filepath in files:
            with open(filepath, encoding="utf-8") as f:
                for line in reversed(f.readlines()):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if filters and not self._matches_filters(data, filters):
                            continue
                        events.append(self._dict_to_event(data))
                        if len(events) >= limit:
                            return events
                    except json.JSONDecodeError:
                        continue
        return events

    def _matches_filters(self, data: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, value in filters.items():
            if key == "since":
                if data.get("timestamp", "") < value:
                    return False
            elif key == "until":
                if data.get("timestamp", "") > value:
                    return False
            elif data.get(key) != value:
                return False
        return True

    def _dict_to_event(self, data: dict[str, Any]) -> AuditEvent:
        event = AuditEvent(
            event_type=AuditEventType(data["event_type"]),
            actor=data["actor"],
            action=data["action"],
            resource=data["resource"],
            severity=AuditSeverity(data.get("severity", "info")),
            timestamp=data["timestamp"],
            event_id=data["event_id"],
            session_id=data.get("session_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            status=data.get("status", "success"),
            details=data.get("details", {}),
            previous_hash=data.get("previous_hash", ""),
        )
        event._hash = data.get("hash", "")
        return event

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify integrity of entire hash chain."""
        errors: list[str] = []
        files = sorted(self.log_dir.glob("audit-*.ndjson"))
        prev_hash = ""
        for filepath in files:
            with open(filepath, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("previous_hash") != prev_hash:
                            errors.append(
                                f"{filepath}:{line_num}: hash chain broken "
                                f"(expected {prev_hash[:16]}..., got {data.get('previous_hash', '')[:16]}...)"
                            )
                        prev_hash = data.get("hash", "")
                    except json.JSONDecodeError:
                        errors.append(f"{filepath}:{line_num}: invalid JSON")
        return len(errors) == 0, errors


class MemoryBackend(AuditLogBackend):
    """In-memory audit log backend for testing."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = threading.Lock()
        self._last_hash: str = ""

    def write(self, event: AuditEvent) -> None:
        with self._lock:
            event.finalize(self._last_hash)
            self._last_hash = event._hash
            self._events.append(event)

    def read(self, filters: dict[str, Any] | None = None, limit: int = 100) -> list[AuditEvent]:
        with self._lock:
            events = list(reversed(self._events))
            if filters:
                events = [e for e in events if self._matches(e, filters)]
            return events[:limit]

    def _matches(self, event: AuditEvent, filters: dict[str, Any]) -> bool:
        for key, value in filters.items():
            if key == "since":
                if event.timestamp < value:
                    return False
            elif key == "until":
                if event.timestamp > value:
                    return False
            elif getattr(event, key, None) != value:
                return False
        return True

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._last_hash = ""


class AuditLogger:
    """Main audit logger with structured event logging."""

    _instance: AuditLogger | None = None
    _lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls, backend: AuditLogBackend | None = None) -> AuditLogger:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, backend: AuditLogBackend | None = None) -> None:
        if self._initialized:
            return
        self._backend = backend or FileBackend()
        self._logger = logging.getLogger("c4_cdi_turbo.audit")
        self._initialized = True

    def log(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        resource: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a structured audit event."""
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            action=action,
            resource=resource,
            severity=severity,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details or {},
        )
        self._backend.write(event)
        self._logger.info(
            "AUDIT: %s | %s | %s | %s | %s",
            event.event_id,
            event.event_type.value,
            event.actor,
            event.action,
            event.resource,
        )
        return event

    def log_auth_login(
        self,
        actor: str,
        success: bool = True,
        ip_address: str | None = None,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log authentication attempt."""
        return self.log(
            event_type=AuditEventType.AUTH_LOGIN if success else AuditEventType.AUTH_FAILED,
            actor=actor,
            action="login",
            resource="auth",
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            ip_address=ip_address,
            session_id=session_id,
            status="success" if success else "failed",
            details=details,
        )

    def log_data_access(
        self,
        actor: str,
        resource: str,
        action: str = "read",
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log data access event."""
        return self.log(
            event_type=AuditEventType.DATA_ACCESS,
            actor=actor,
            action=action,
            resource=resource,
            ip_address=ip_address,
            details=details,
        )

    def log_security_alert(
        self,
        actor: str,
        alert_type: str,
        severity: AuditSeverity = AuditSeverity.WARNING,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log security alert."""
        return self.log(
            event_type=AuditEventType.SECURITY_ALERT,
            actor=actor,
            action=alert_type,
            resource="security",
            severity=severity,
            status="alert",
            details=details,
        )

    def log_admin_action(
        self,
        actor: str,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log administrative action."""
        return self.log(
            event_type=AuditEventType.ADMIN_ACTION,
            actor=actor,
            action=action,
            resource=resource,
            severity=AuditSeverity.WARNING,
            details=details,
        )

    def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit log with filters."""
        return self._backend.read(filters=filters, limit=limit)

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Verify log integrity if backend supports it."""
        if isinstance(self._backend, FileBackend):
            return self._backend.verify_chain()
        return True, []


def get_audit_logger(backend: AuditLogBackend | None = None) -> AuditLogger:
    """Get or create the global audit logger instance."""
    return AuditLogger(backend)


def reset_audit_logger() -> None:
    """Reset singleton for testing."""
    AuditLogger._instance = None
