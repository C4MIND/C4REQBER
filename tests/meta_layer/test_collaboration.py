"""Tests for meta_layer collaboration module."""
from __future__ import annotations

import pytest

from src.meta_layer.collaboration import Collaboration, CollaborationManager, Contributor


class TestContributor:
    def test_create_contributor(self):
        c = Contributor(id="alice-1", name="Alice", role="researcher")
        assert c.id == "alice-1"
        assert c.name == "Alice"
        assert c.role == "researcher"
        assert c.contributions == []

    def test_contributor_default_contributions(self):
        c = Contributor(id="bob-1", name="Bob", role="engineer")
        assert isinstance(c.contributions, list)
        assert len(c.contributions) == 0

    def test_contributor_with_contributions(self):
        c = Contributor(
            id="bob-1",
            name="Bob",
            role="engineer",
            contributions=[{"action": "coded", "detail": "Added module"}],
        )
        assert len(c.contributions) == 1
        assert c.contributions[0]["action"] == "coded"


class TestCollaboration:
    def test_create_collaboration(self):
        contributors = [Contributor(id="a", name="Alice", role="researcher")]
        collab = Collaboration(
            id="c1", project="Test", contributors=contributors,
            created_at="2026-01-01", status="active",
        )
        assert collab.id == "c1"
        assert collab.project == "Test"
        assert len(collab.contributors) == 1
        assert collab.status == "active"

    def test_collaboration_statuses(self):
        for status in ["active", "completed", "archived"]:
            collab = Collaboration(
                id="c1", project="P", contributors=[],
                created_at="2026-01-01", status=status,
            )
            assert collab.status == status


class TestCollaborationManager:
    def test_create_collaboration(self):
        mgr = CollaborationManager()
        collab = mgr.create("Project X", [{"name": "Alice", "role": "researcher"}])
        assert collab.project == "Project X"
        assert collab.status == "active"
        assert len(collab.contributors) == 1
        assert collab.id in mgr.collaborations

    def test_create_multiple_contributors(self):
        mgr = CollaborationManager()
        collab = mgr.create("P", [
            {"name": "Alice", "role": "researcher"},
            {"name": "Bob", "role": "engineer"},
            {"name": "Charlie", "role": "reviewer"},
        ])
        assert len(collab.contributors) == 3

    def test_add_contribution(self):
        mgr = CollaborationManager()
        collab = mgr.create("P", [{"name": "Alice", "role": "researcher"}])
        alice = collab.contributors[0]
        mgr.add_contribution(collab.id, alice.id, "wrote", "Added intro")
        assert len(alice.contributions) == 1
        assert alice.contributions[0]["action"] == "wrote"
        assert alice.contributions[0]["detail"] == "Added intro"
        assert "timestamp" in alice.contributions[0]

    def test_add_contribution_nonexistent_collab(self):
        mgr = CollaborationManager()
        mgr.add_contribution("no-exist", "alice", "did", "stuff")

    def test_add_contribution_nonexistent_contributor(self):
        mgr = CollaborationManager()
        collab = mgr.create("P", [{"name": "Alice", "role": "researcher"}])
        mgr.add_contribution(collab.id, "no-exist", "did", "stuff")
        assert len(collab.contributors[0].contributions) == 0

    def test_get_stats(self):
        mgr = CollaborationManager()
        collab = mgr.create("P", [
            {"name": "Alice", "role": "researcher"},
            {"name": "Bob", "role": "engineer"},
        ])
        mgr.add_contribution(collab.id, collab.contributors[0].id, "wrote", "A")
        mgr.add_contribution(collab.id, collab.contributors[0].id, "edited", "B")
        mgr.add_contribution(collab.id, collab.contributors[1].id, "reviewed", "C")

        stats = mgr.get_stats(collab.id)
        assert stats["project"] == "P"
        assert stats["contributors"] == 2
        assert stats["total_contributions"] == 3
        assert stats["status"] == "active"

    def test_get_stats_nonexistent(self):
        mgr = CollaborationManager()
        assert mgr.get_stats("no-exist") == {}

    def test_list_all(self):
        mgr = CollaborationManager()
        mgr.create("P1", [{"name": "A", "role": "r"}])
        mgr.create("P2", [{"name": "B", "role": "e"}])
        all_c = mgr.list_all()
        assert len(all_c) == 2
        assert {c["project"] for c in all_c} == {"P1", "P2"}
