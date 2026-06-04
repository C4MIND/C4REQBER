from __future__ import annotations


"""Policy Engine for Reqber v4.1.
Implements 4 risk tiers: READ, SOFT_WRITE, HARD_WRITE, DANGEROUS
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    """Represents an action that needs policy approval."""
    name: str
    action_type: str  # file_write, exec, git_push, delete, api_call
    params: dict[str, Any] = field(default_factory=dict)
    risk_tier: str = "UNKNOWN"


@dataclass
class Decision:
    """Policy decision result."""
    allowed: bool
    reason: str = ""
    requires_approval: bool = False
    requires_multi_factor: bool = False


class PolicyEngine:
    """Policy engine with 4 risk tiers."""

    def __init__(self) -> None:
        self.risk_rules: dict[str, str] = {
            # Read-only actions
            "file_read": "READ",
            "search": "READ",
            "analyze": "READ",
            "list": "READ",
            # Soft-write actions (log + notify)
            "file_write_non_critical": "SOFT_WRITE",
            "comment_add": "SOFT_WRITE",
            "config_edit": "SOFT_WRITE",
            # Hard-write actions (explicit approval)
            "file_write_critical": "HARD_WRITE",
            "git_commit": "HARD_WRITE",
            "deploy": "HARD_WRITE",
            # Dangerous actions (multi-factor approval)
            "file_delete": "DANGEROUS",
            "exec_shell": "DANGEROUS",
            "git_push": "DANGEROUS",
            "api_call_external": "DANGEROUS",
        }
        self.audit_log: list[dict[str, Any]] = []

    def classify_risk(self, action: Action) -> str:
        """Classify action into risk tier."""
        if action.risk_tier != "UNKNOWN":
            return action.risk_tier
        return self.risk_rules.get(action.action_type, "DANGEROUS")

    def evaluate(self, action: Action) -> Decision:
        """Evaluate action against policy."""
        tier = self.classify_risk(action)

        if tier == "READ":
            return Decision(allowed=True, reason="Read-only action")

        elif tier == "SOFT_WRITE":
            self._log_action(action, "SOFT_WRITE", "allowed")
            return Decision(
                allowed=True,
                reason="Soft-write: logged + notified",
                requires_approval=False,
            )

        elif tier == "HARD_WRITE":
            return Decision(
                allowed=False,
                reason=f"Hard-write action requires approval: {action.name}",
                requires_approval=True,
            )

        elif tier == "DANGEROUS":
            return Decision(
                allowed=False,
                reason=f"Dangerous action requires multi-factor approval: {action.name}",
                requires_multi_factor=True,
            )

        return Decision(allowed=False, reason="Unknown action type")

    def _log_action(self, action: Action, tier: str, result: str) -> None:
        """Log action to audit trail."""
        import time
        entry = {
            "timestamp": time.time(),
            "action": action.name,
            "type": action.action_type,
            "tier": tier,
            "result": result,
            "params": action.params,
        }
        self.audit_log.append(entry)

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Return full audit trail."""
        return self.audit_log.copy()


def pev_loops(policy_engine: PolicyEngine, action: Action) -> Decision:
    """Prevent-Evaluate-Verify loop for side-effects."""
    decision = policy_engine.evaluate(action)
    if not decision.allowed:
        return decision
    return decision
