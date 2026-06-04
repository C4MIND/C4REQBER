"""
Tests for DiscoveryChainer.

Coverage:
- compute_path (Theorem 11 / belief-path)
- path_distance
- store_discovery / load_history (SQLite)
- chain_from_history
- get_state_after_path
- Antipodal and edge cases
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from c4.engine import C4State
from discovery.chainer import (
    C4Op,
    ChainSuggestion,
    DiscoveryChainer,
    DiscoveryRecord,
)


class TestComputePath:
    def test_same_state_returns_empty(self):
        """compute_path(s, s) == []"""
        s = C4State(1, 1, 1)
        assert DiscoveryChainer.compute_path(s, s) == []

    def test_one_axis_one_step(self):
        s1 = C4State(0, 0, 0)
        s2 = C4State(1, 0, 0)
        assert DiscoveryChainer.compute_path(s1, s2) == ["tau+"]

    def test_one_axis_two_steps(self):
        """Auditor: (0,0,0) → (2,0,0) returns 2 time operators."""
        s1 = C4State(0, 0, 0)
        s2 = C4State(2, 0, 0)
        path = DiscoveryChainer.compute_path(s1, s2)
        assert path == ["tau+", "tau+"]
        assert len(path) == 2

    def test_two_axes(self):
        s1 = C4State(0, 0, 0)
        s2 = C4State(1, 2, 0)
        path = DiscoveryChainer.compute_path(s1, s2)
        assert path == ["tau+", "lambda+", "lambda+"]

    def test_three_axes(self):
        s1 = C4State(0, 0, 0)
        s2 = C4State(1, 1, 1)
        path = DiscoveryChainer.compute_path(s1, s2)
        assert path == ["tau+", "lambda+", "kappa+"]

    def test_antipodal_zero_to_two(self):
        """Auditor: (0,0,0) → (2,2,2) returns exactly 6 operators."""
        s1 = C4State(0, 0, 0)
        s2 = C4State(2, 2, 2)
        path = DiscoveryChainer.compute_path(s1, s2)
        assert len(path) == 6
        assert path.count("tau+") == 2
        assert path.count("lambda+") == 2
        assert path.count("kappa+") == 2

    def test_antipodal_two_to_zero(self):
        """Reverse antipodal: (2,2,2) → (0,0,0) = 3 steps (all +1 wraps)."""
        s1 = C4State(2, 2, 2)
        s2 = C4State(0, 0, 0)
        path = DiscoveryChainer.compute_path(s1, s2)
        assert len(path) == 3
        assert set(path) == {"tau+", "lambda+", "kappa+"}

    def test_preserves_maximum_diameter_bound(self):
        """For all 27x27 ordered pairs, path length <= 6."""
        states = C4State.all_states()
        for a in states:
            for b in states:
                path = DiscoveryChainer.compute_path(a, b)
                assert len(path) <= 6

    def test_path_is_canonical_order(self):
        """Operators appear in T, S, A axis order."""
        s1 = C4State(0, 0, 0)
        s2 = C4State(2, 1, 2)
        path = DiscoveryChainer.compute_path(s1, s2)
        # tau+ comes first, then lambda+, then kappa+
        tau_indices = [i for i, op in enumerate(path) if op == "tau+"]
        lambda_indices = [i for i, op in enumerate(path) if op == "lambda+"]
        kappa_indices = [i for i, op in enumerate(path) if op == "kappa+"]
        assert all(t < l for t in tau_indices for l in lambda_indices)
        assert all(l < k for l in lambda_indices for k in kappa_indices)


class TestPathDistance:
    def test_distance_same_state(self):
        s = C4State(1, 1, 1)
        assert DiscoveryChainer.path_distance(s, s) == 0

    def test_distance_one_axis(self):
        assert DiscoveryChainer.path_distance(C4State(0, 0, 0), C4State(1, 0, 0)) == 1

    def test_distance_two_on_one_axis(self):
        assert DiscoveryChainer.path_distance(C4State(0, 0, 0), C4State(2, 0, 0)) == 2

    def test_distance_antipodal(self):
        assert DiscoveryChainer.path_distance(C4State(0, 0, 0), C4State(2, 2, 2)) == 6


class TestStateAfterPath:
    def test_apply_tau_plus(self):
        chainer = DiscoveryChainer()
        end = chainer.get_state_after_path(C4State(0, 0, 0), ["tau+"])
        assert end.to_tuple() == (1, 0, 0)

    def test_apply_two_tau_plus(self):
        chainer = DiscoveryChainer()
        end = chainer.get_state_after_path(C4State(0, 0, 0), ["tau+", "tau+"])
        assert end.to_tuple() == (2, 0, 0)

    def test_apply_full_path(self):
        chainer = DiscoveryChainer()
        start = C4State(0, 0, 0)
        end = C4State(2, 2, 2)
        path = chainer.compute_path(start, end)
        result = chainer.get_state_after_path(start, path)
        assert result.to_tuple() == end.to_tuple()


class TestSQLiteStorage:
    def test_store_and_load(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        state = C4State(1, 2, 0)
        rid = chainer.store_discovery("test-prob", state, {"key": "val"})
        assert rid > 0

        history = chainer.load_history("test-prob")
        assert len(history) == 1
        assert history[0].problem == "test-prob"
        assert history[0].state.to_tuple() == (1, 2, 0)
        assert history[0].result["key"] == "val"

    def test_load_all_when_no_filter(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        chainer.store_discovery("p1", C4State(0, 0, 0), {"a": 1})
        chainer.store_discovery("p2", C4State(1, 1, 1), {"b": 2})
        history = chainer.load_history()
        assert len(history) == 2

    def test_load_filters_by_problem(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        chainer.store_discovery("alpha", C4State(0, 0, 0), {})
        chainer.store_discovery("beta", C4State(1, 1, 1), {})
        history = chainer.load_history("alpha")
        assert len(history) == 1
        assert history[0].problem == "alpha"


class TestChainFromHistory:
    def test_empty_history_returns_none(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        result = chainer.chain_from_history("empty", [])
        assert result is None

    def test_single_record_zero_distance(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        rec = DiscoveryRecord("p", C4State(1, 1, 1), {})
        suggestion = chainer.chain_from_history("p", [rec])
        assert suggestion is not None
        assert suggestion.distance == 0
        assert suggestion.path == []

    def test_finds_nearest(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        history = [
            DiscoveryRecord("p", C4State(0, 0, 0), {"id": 0}),
            DiscoveryRecord("p", C4State(2, 0, 0), {"id": 1}),
            DiscoveryRecord("p", C4State(1, 1, 1), {"id": 2}),
        ]
        # reference state = last record = (1,1,1)
        # distances: to (0,0,0)=3, to (2,0,0)=3, to (1,1,1)=0
        suggestion = chainer.chain_from_history("p", history)
        assert suggestion is not None
        assert suggestion.record.result["id"] == 2
        assert suggestion.distance == 0

    def test_nearest_not_last(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        history = [
            DiscoveryRecord("p", C4State(0, 0, 0), {"id": 0}),
            DiscoveryRecord("p", C4State(1, 0, 0), {"id": 1}),
            DiscoveryRecord("p", C4State(2, 2, 2), {"id": 2}),
        ]
        # reference = (2,2,2)
        # distances: to (0,0,0)=6, to (1,0,0)=5, to (2,2,2)=0
        suggestion = chainer.chain_from_history("p", history)
        assert suggestion is not None
        assert suggestion.record.result["id"] == 2

    def test_fallback_to_db(self, tmp_path: Path):
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        chainer.store_discovery("q", C4State(0, 0, 0), {"src": "db"})
        suggestion = chainer.chain_from_history("q", [])
        assert suggestion is not None
        assert suggestion.record.result["src"] == "db"

    def test_chaining_demo_two_discoveries(self, tmp_path: Path):
        """Auditor: 2+ past discoveries stored, nearest found correctly."""
        db = tmp_path / "test_chain.db"
        chainer = DiscoveryChainer(db_path=db)
        chainer.store_discovery("demo", C4State(0, 0, 0), {"discovery": "first"})
        chainer.store_discovery("demo", C4State(2, 0, 0), {"discovery": "second"})

        history = chainer.load_history("demo")
        assert len(history) == 2

        suggestion = chainer.chain_from_history("demo", history)
        assert suggestion is not None
        # reference = last stored = (2,0,0)
        # nearest to (2,0,0) among [(0,0,0), (2,0,0)] is (2,0,0) itself
        assert suggestion.distance == 0
        assert suggestion.path == []
        assert suggestion.record.state.to_tuple() == (2, 0, 0)


class TestTypes:
    def test_discovery_record_to_dict(self):
        rec = DiscoveryRecord("x", C4State(1, 1, 1), {"k": "v"})
        d = rec.to_dict()
        assert d["problem"] == "x"
        assert d["state"] == [1, 1, 1]
        assert d["result"] == {"k": "v"}
        assert "created_at" in d

    def test_chain_suggestion_to_dict(self):
        rec = DiscoveryRecord("x", C4State(1, 1, 1), {})
        sugg = ChainSuggestion(
            problem="x",
            from_state=C4State(0, 0, 0),
            to_state=C4State(1, 1, 1),
            path=["tau+", "lambda+", "kappa+"],
            record=rec,
            distance=3,
        )
        d = sugg.to_dict()
        assert d["distance"] == 3
        assert d["path"] == ["tau+", "lambda+", "kappa+"]
        assert d["from_state"] == [0, 0, 0]
        assert d["to_state"] == [1, 1, 1]
