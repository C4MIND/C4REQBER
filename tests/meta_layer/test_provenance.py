"""Tests for meta_layer provenance module."""
from __future__ import annotations

import pytest

from src.meta_layer.provenance import ProvenanceRecord, ProvenanceTracker


class TestProvenanceRecord:
    def test_create_record(self):
        rec = ProvenanceRecord(
            id="r1",
            entity="Entity A",
            entity_type="hypothesis",
            created_by="agent-1",
            created_at="2026-01-01",
            inputs=["in1"],
            tools_used=["tool1"],
        )
        assert rec.id == "r1"
        assert rec.entity == "Entity A"
        assert rec.entity_type == "hypothesis"
        assert rec.created_by == "agent-1"
        assert rec.inputs == ["in1"]
        assert rec.tools_used == ["tool1"]
        assert rec.version == 1

    def test_default_version(self):
        rec = ProvenanceRecord(
            id="r1", entity="E", entity_type="result",
            created_by="agent", created_at="t",
            inputs=[], tools_used=[],
        )
        assert rec.version == 1

    def test_custom_version(self):
        rec = ProvenanceRecord(
            id="r1", entity="E", entity_type="result",
            created_by="agent", created_at="t",
            inputs=[], tools_used=[], version=3,
        )
        assert rec.version == 3


class TestProvenanceTracker:
    def test_record_entity(self):
        tracker = ProvenanceTracker()
        rec = tracker.record(
            entity="Hypothesis H1",
            entity_type="hypothesis",
            created_by="agent-1",
            inputs=[],
            tools=["GPT-4"],
        )
        assert rec.entity == "Hypothesis H1"
        assert rec.entity_type == "hypothesis"
        assert rec.id in tracker.records

    def test_record_with_inputs(self):
        tracker = ProvenanceTracker()
        tracker.record("E1", "data", "agent", [], [])
        rec2 = tracker.record("E2", "hypothesis", "agent", ["E1"], ["tool"])
        assert "E1" in rec2.inputs

    def test_get_lineage_single_entity(self):
        tracker = ProvenanceTracker()
        rec = tracker.record("E1", "data", "agent", [], [])
        lineage = tracker.get_lineage(rec.id)
        assert lineage == [rec.id]

    def test_get_lineage_chain(self):
        tracker = ProvenanceTracker()
        r1 = tracker.record("E1", "data", "agent", [], [])
        r2 = tracker.record("E2", "analysis", "agent", [r1.id], ["tool1"])
        r3 = tracker.record("E3", "result", "agent", [r2.id], ["tool2"])

        lineage = tracker.get_lineage(r1.id)
        assert len(lineage) == 3
        assert lineage[0] == r1.id

    def test_get_lineage_branch(self):
        tracker = ProvenanceTracker()
        r1 = tracker.record("E1", "data", "agent", [], [])
        r2 = tracker.record("E2", "result", "agent", [r1.id], [])
        r3 = tracker.record("E3", "result", "agent", [r1.id], [])

        lineage = tracker.get_lineage(r1.id)
        assert len(lineage) == 3
        assert r2.id in lineage
        assert r3.id in lineage

    def test_get_lineage_no_children(self):
        tracker = ProvenanceTracker()
        rec = tracker.record("E1", "data", "agent", [], [])
        lineage = tracker.get_lineage(rec.id)
        assert lineage == [rec.id]

    def test_verify_valid_provenance(self):
        tracker = ProvenanceTracker()
        r1 = tracker.record("E1", "data", "agent", [], [])
        r2 = tracker.record("E2", "analysis", "agent", [r1.id], [])
        result = tracker.verify(r2.id)
        assert result["verified"] is True
        assert result["issues"] == []
        assert result["entity"] == "E2"

    def test_verify_missing_input(self):
        tracker = ProvenanceTracker()
        r2 = tracker.record("E2", "analysis", "agent", ["missing-id"], [])
        result = tracker.verify(r2.id)
        assert result["verified"] is False
        assert len(result["issues"]) == 1
        assert "Missing provenance for input" in result["issues"][0]

    def test_verify_nonexistent_record(self):
        tracker = ProvenanceTracker()
        result = tracker.verify("no-exist")
        assert result["verified"] is False
        assert "No provenance record found" in result["reason"]

    def test_list_all(self):
        tracker = ProvenanceTracker()
        tracker.record("E1", "data", "agent", [], [])
        tracker.record("E2", "hypothesis", "agent", [], [])
        all_r = tracker.list_all()
        assert len(all_r) == 2
        entities = {r["entity"] for r in all_r}
        assert entities == {"E1", "E2"}

    def test_graph_adjacency(self):
        tracker = ProvenanceTracker()
        r1 = tracker.record("E1", "data", "agent", [], [])
        r2 = tracker.record("E2", "result", "agent", [r1.id], [])
        assert r1.id in tracker.graph
        assert r2.id in tracker.graph[r1.id]
