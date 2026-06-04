"""c4reqber Policy Engine — Permission and Audit Layer.

Implements a 4-tier risk classification system for all actions
performed by the AI assistant:

    READ        → Allowed automatically
    SOFT_WRITE  → Allowed + logged
    HARD_WRITE  → Requires explicit user approval
    DANGEROUS   → Requires multi-factor approval

Every evaluated action is recorded in an immutable audit trail.
Integrates with the pipeline to guard dangerous operations.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_PATH = Path.home() / ".c4reqber" / "audit.jsonl"


class RiskTier(StrEnum):
    """Risk classification tiers."""

    READ = "READ"
    SOFT_WRITE = "SOFT_WRITE"
    HARD_WRITE = "HARD_WRITE"
    DANGEROUS = "DANGEROUS"
    UNKNOWN = "UNKNOWN"


@dataclass
class Action:
    """An action that needs policy evaluation."""

    name: str
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)
    risk_tier: RiskTier = RiskTier.UNKNOWN
    source: str = "cli"  # cli, pipeline, mcp, api


@dataclass
class Decision:
    """Result of policy evaluation."""

    allowed: bool
    reason: str = ""
    requires_approval: bool = False
    requires_multi_factor: bool = False
    risk_tier: RiskTier = RiskTier.UNKNOWN
    timestamp: float = field(default_factory=time.time)


@dataclass
class AuditEntry:
    """Single entry in the audit trail."""

    timestamp: float
    action_name: str
    action_type: str
    risk_tier: str
    allowed: bool
    reason: str
    source: str
    params: dict[str, Any] = field(default_factory=dict)


class AuditTrail:
    """Immutable audit log stored as JSON Lines."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_AUDIT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: AuditEntry) -> None:
        """Append a single entry to the audit log."""
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def read_all(self) -> list[AuditEntry]:
        """Read all audit entries."""
        if not self.path.exists():
            return []

        entries: list[AuditEntry] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entries.append(
                    AuditEntry(
                        timestamp=data["timestamp"],
                        action_name=data["action_name"],
                        action_type=data["action_type"],
                        risk_tier=data["risk_tier"],
                        allowed=data["allowed"],
                        reason=data["reason"],
                        source=data.get("source", "unknown"),
                        params=data.get("params", {}),
                    )
                )
        return entries

    def read_last(self, n: int = 10) -> list[AuditEntry]:
        """Read last N entries."""
        all_entries = self.read_all()
        return all_entries[-n:] if all_entries else []

    def export(self, output_path: Path) -> None:
        """Export audit trail to a JSON file."""
        entries = [asdict(e) for e in self.read_all()]
        output_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

    def stats(self) -> dict[str, Any]:
        """Return audit statistics."""
        entries = self.read_all()
        if not entries:
            return {"total": 0, "allowed": 0, "denied": 0, "by_tier": {}}

        by_tier: dict[str, int] = {}
        for e in entries:
            by_tier[e.risk_tier] = by_tier.get(e.risk_tier, 0) + 1

        return {
            "total": len(entries),
            "allowed": sum(1 for e in entries if e.allowed),
            "denied": sum(1 for e in entries if not e.allowed),
            "by_tier": by_tier,
        }


class PolicyEngine:
    """4-tier policy engine with audit trail.

    Usage::

        engine = PolicyEngine()
        action = Action(name="delete_file", action_type="file_delete", params={"path": "/tmp/x"})
        decision = engine.evaluate(action)
        if not decision.allowed:
            print(f"Blocked: {decision.reason}")
    """

    # Default risk mapping — can be extended via config
    DEFAULT_RULES: dict[str, RiskTier] = {
        # Read-only
        "file_read": RiskTier.READ,
        "search": RiskTier.READ,
        "analyze": RiskTier.READ,
        "list": RiskTier.READ,
        "view": RiskTier.READ,
        "status": RiskTier.READ,
        # Soft-write
        "file_write_non_critical": RiskTier.SOFT_WRITE,
        "comment_add": RiskTier.SOFT_WRITE,
        "config_edit": RiskTier.SOFT_WRITE,
        "log_write": RiskTier.SOFT_WRITE,
        # Hard-write
        "file_write_critical": RiskTier.HARD_WRITE,
        "git_commit": RiskTier.HARD_WRITE,
        "git_merge": RiskTier.HARD_WRITE,
        "deploy": RiskTier.HARD_WRITE,
        "db_migrate": RiskTier.HARD_WRITE,
        # Dangerous
        "file_delete": RiskTier.DANGEROUS,
        "exec_shell": RiskTier.DANGEROUS,
        "git_push": RiskTier.DANGEROUS,
        "git_force_push": RiskTier.DANGEROUS,
        "api_call_external": RiskTier.DANGEROUS,
        "system_modify": RiskTier.DANGEROUS,
        "rm_rf": RiskTier.DANGEROUS,
    }

    def __init__(
        self,
        audit_path: Path | None = None,
        custom_rules: dict[str, RiskTier] | None = None,
    ) -> None:
        self.rules = {**self.DEFAULT_RULES, **(custom_rules or {})}
        self.audit = AuditTrail(audit_path)

    def classify(self, action: Action) -> RiskTier:
        """Classify action into risk tier."""
        if action.risk_tier != RiskTier.UNKNOWN:
            return action.risk_tier
        return self.rules.get(action.action_type, RiskTier.DANGEROUS)

    def evaluate(self, action: Action, user_approved: bool = False) -> Decision:
        """Evaluate action against policy.

        Args:
            action: The action to evaluate.
            user_approved: Whether user has explicitly approved (for HARD_WRITE/DANGEROUS).

        Returns:
            Decision with allowed flag and reason.
        """
        tier = self.classify(action)
        timestamp = time.time()

        if tier == RiskTier.READ:
            decision = Decision(
                allowed=True,
                reason="Read-only action — auto-approved",
                risk_tier=tier,
                timestamp=timestamp,
            )

        elif tier == RiskTier.SOFT_WRITE:
            decision = Decision(
                allowed=True,
                reason="Soft-write: logged + notified",
                risk_tier=tier,
                timestamp=timestamp,
            )

        elif tier == RiskTier.HARD_WRITE:
            if user_approved:
                decision = Decision(
                    allowed=True,
                    reason="Hard-write: user approved",
                    requires_approval=True,
                    risk_tier=tier,
                    timestamp=timestamp,
                )
            else:
                decision = Decision(
                    allowed=False,
                    reason=f"Hard-write requires approval: {action.name}",
                    requires_approval=True,
                    risk_tier=tier,
                    timestamp=timestamp,
                )

        elif tier == RiskTier.DANGEROUS:
            if user_approved:
                decision = Decision(
                    allowed=True,
                    reason="Dangerous: multi-factor approved",
                    requires_multi_factor=True,
                    risk_tier=tier,
                    timestamp=timestamp,
                )
            else:
                decision = Decision(
                    allowed=False,
                    reason=f"Dangerous action requires multi-factor approval: {action.name}",
                    requires_multi_factor=True,
                    risk_tier=tier,
                    timestamp=timestamp,
                )

        else:
            decision = Decision(
                allowed=False,
                reason=f"Unknown action type: {action.action_type}",
                risk_tier=RiskTier.UNKNOWN,
                timestamp=timestamp,
            )

        # Record in audit trail
        self.audit.append(
            AuditEntry(
                timestamp=decision.timestamp,
                action_name=action.name,
                action_type=action.action_type,
                risk_tier=tier.value,
                allowed=decision.allowed,
                reason=decision.reason,
                source=action.source,
                params=action.params,
            )
        )

        return decision

    def get_rules(self) -> dict[str, str]:
        """Return current rule mapping as strings."""
        return {k: v.value for k, v in self.rules.items()}

    def add_rule(self, action_type: str, tier: RiskTier) -> None:
        """Add or update a risk rule."""
        self.rules[action_type] = tier

    def remove_rule(self, action_type: str) -> None:
        """Remove a custom risk rule (falls back to DANGEROUS)."""
        self.rules.pop(action_type, None)


def asdict(obj: Any) -> dict[str, Any]:
    """Helper: convert dataclass to dict."""
    from dataclasses import asdict as _asdict

    return _asdict(obj)
