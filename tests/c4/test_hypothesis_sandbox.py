from __future__ import annotations

from c4.hypothesis_sandbox import HypothesisSandbox


class TestHypothesisSandbox:
    def test_spawn_creates_sandbox_with_unresolved_state(self) -> None:
        sandbox = HypothesisSandbox()
        sid = sandbox.spawn("All swans are white")
        result = sandbox.get(sid)
        assert result is not None
        assert result.hypothesis == "All swans are white"
        assert result.verification == "unresolved"
        assert result.confidence == 0.0
        assert result.conclusion == ""

    def test_spawn_returns_unique_ids(self) -> None:
        sandbox = HypothesisSandbox()
        id1 = sandbox.spawn("H1")
        id2 = sandbox.spawn("H2")
        assert id1 != id2
        assert len(id1) == 8
        assert len(id2) == 8

    def test_conclude_updates_all_fields(self) -> None:
        sandbox = HypothesisSandbox()
        sid = sandbox.spawn("Water boils at 100C")
        sandbox.conclude(sid, "Confirmed at sea level", 0.95, "verified")
        result = sandbox.get(sid)
        assert result.conclusion == "Confirmed at sea level"
        assert result.confidence == 0.95
        assert result.verification == "verified"

    def test_conclude_nonexistent_id_is_noop(self) -> None:
        sandbox = HypothesisSandbox()
        sandbox.conclude("fake-id", "no", 1.0, "verified")

    def test_conflicts_detected_verified_vs_falsified(self) -> None:
        sandbox = HypothesisSandbox()
        id1 = sandbox.spawn("H1: all metals conduct")
        id2 = sandbox.spawn("H2: some metals insulate")
        sandbox.conclude(id1, "false", 1.0, "falsified")
        sandbox.conclude(id2, "true", 1.0, "verified")
        conflicts = sandbox.conflicts()
        assert len(conflicts) == 1
        assert conflicts[0][0] == id1
        assert conflicts[0][1] == id2

    def test_conflicts_detected_same_hypothesis_different_conclusions(self) -> None:
        sandbox = HypothesisSandbox()
        id1 = sandbox.spawn("H")
        id2 = sandbox.spawn("H")
        sandbox.conclude(id1, "yes", 0.9, "unresolved")
        sandbox.conclude(id2, "no", 0.8, "unresolved")
        conflicts = sandbox.conflicts()
        assert len(conflicts) == 1
        assert "Same hypothesis, different conclusions" in conflicts[0][2]

    def test_no_conflicts_with_one_unresolved(self) -> None:
        sandbox = HypothesisSandbox()
        sid = sandbox.spawn("H")
        sandbox.conclude(sid, "maybe", 0.5, "unresolved")
        conflicts = sandbox.conflicts()
        assert conflicts == []

    def test_no_conflicts_when_all_agree(self) -> None:
        sandbox = HypothesisSandbox()
        id1 = sandbox.spawn("H")
        id2 = sandbox.spawn("H")
        sandbox.conclude(id1, "yes", 0.9, "verified")
        sandbox.conclude(id2, "yes", 0.9, "verified")
        assert sandbox.conflicts() == []

    def test_get_nonexistent_returns_none(self) -> None:
        sandbox = HypothesisSandbox()
        assert sandbox.get("nonexistent") is None
