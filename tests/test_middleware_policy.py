"""Tests for src/api/middleware/policy.py"""
import pytest

from src.api.middleware.policy import Action, Decision, PolicyEngine, pev_loops


class TestAction:
    def test_action_defaults(self):
        action = Action(name="test", action_type="file_read")
        assert action.params == {}
        assert action.risk_tier == "UNKNOWN"

    def test_action_with_params(self):
        action = Action(name="write", action_type="file_write", params={"path": "/tmp"}, risk_tier="SOFT_WRITE")
        assert action.params == {"path": "/tmp"}
        assert action.risk_tier == "SOFT_WRITE"


class TestDecision:
    def test_decision_defaults(self):
        d = Decision(allowed=True)
        assert d.allowed is True
        assert d.reason == ""
        assert d.requires_approval is False
        assert d.requires_multi_factor is False


class TestPolicyEngine:
    def test_init(self):
        pe = PolicyEngine()
        assert "file_read" in pe.risk_rules
        assert pe.risk_rules["file_read"] == "READ"
        assert pe.audit_log == []

    def test_classify_risk_known_action(self):
        pe = PolicyEngine()
        action = Action(name="read", action_type="file_read")
        assert pe.classify_risk(action) == "READ"

    def test_classify_risk_unknown_action(self):
        pe = PolicyEngine()
        action = Action(name="unknown", action_type="unknown_type")
        assert pe.classify_risk(action) == "DANGEROUS"

    def test_classify_risk_override(self):
        pe = PolicyEngine()
        action = Action(name="x", action_type="file_read", risk_tier="DANGEROUS")
        assert pe.classify_risk(action) == "DANGEROUS"

    def test_evaluate_read(self):
        pe = PolicyEngine()
        action = Action(name="search", action_type="search")
        decision = pe.evaluate(action)
        assert decision.allowed is True
        assert decision.reason == "Read-only action"

    def test_evaluate_soft_write(self):
        pe = PolicyEngine()
        action = Action(name="comment", action_type="comment_add")
        decision = pe.evaluate(action)
        assert decision.allowed is True
        assert "Soft-write" in decision.reason
        assert len(pe.audit_log) == 1

    def test_evaluate_hard_write(self):
        pe = PolicyEngine()
        action = Action(name="commit", action_type="git_commit")
        decision = pe.evaluate(action)
        assert decision.allowed is False
        assert decision.requires_approval is True
        assert "Hard-write" in decision.reason

    def test_evaluate_dangerous(self):
        pe = PolicyEngine()
        action = Action(name="push", action_type="git_push")
        decision = pe.evaluate(action)
        assert decision.allowed is False
        assert decision.requires_multi_factor is True
        assert "Dangerous" in decision.reason

    def test_evaluate_unknown(self):
        pe = PolicyEngine()
        action = Action(name="x", action_type="totally_unknown")
        decision = pe.evaluate(action)
        # Unknown action types default to DANGEROUS tier
        assert decision.allowed is False
        assert decision.requires_multi_factor is True
        assert "Dangerous" in decision.reason

    def test_get_audit_trail(self):
        pe = PolicyEngine()
        action = Action(name="c", action_type="comment_add")
        pe.evaluate(action)
        trail = pe.get_audit_trail()
        assert len(trail) == 1
        assert trail[0]["action"] == "c"
        # ensure copy
        trail.pop()
        assert len(pe.audit_log) == 1


class TestPevLoops:
    def test_allowed_action(self):
        pe = PolicyEngine()
        action = Action(name="read", action_type="search")
        decision = pev_loops(pe, action)
        assert decision.allowed is True

    def test_blocked_action(self):
        pe = PolicyEngine()
        action = Action(name="push", action_type="git_push")
        decision = pev_loops(pe, action)
        assert decision.allowed is False
