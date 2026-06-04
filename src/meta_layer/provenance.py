"""Provenance tracking"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ProvenanceRecord:
    """ProvenanceRecord."""
    id: str
    entity: str
    entity_type: str  # hypothesis, experiment, result, artifact
    created_by: str
    created_at: str
    inputs: list[str]  # IDs of upstream entities
    tools_used: list[str]
    version: int = 1

class ProvenanceTracker:
    """ProvenanceTracker."""
    def __init__(self) -> None:
        self.records: dict[str, ProvenanceRecord] = {}
        self.graph: dict[str, list[str]] = {}  # adjacency list[Any]

    def record(
        self,
        entity: str,
        entity_type: str,
        created_by: str,
        inputs: list[str],
        tools: list[str],
    ) -> ProvenanceRecord:
        """Record."""
        rid = str(uuid.uuid4())[:8]
        record = ProvenanceRecord(
            id=rid,
            entity=entity,
            entity_type=entity_type,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            inputs=inputs,
            tools_used=tools,
        )
        self.records[rid] = record
        for inp in inputs:
            self.graph.setdefault(inp, []).append(rid)
        return record

    def get_lineage(self, entity_id: str) -> list[str]:
        """Get upstream lineage (DFS)"""
        lineage: list[str] = []
        visited: set[str] = set()

        def dfs(node: str) -> None:
            """Dfs."""
            if node in visited:
                return
            visited.add(node)
            lineage.append(node)
            for child in self.graph.get(node, []):
                dfs(child)

        dfs(entity_id)
        return lineage

    def verify(self, entity_id: str) -> dict[str, Any]:
        """Verify an entity's provenance"""
        record = self.records.get(entity_id)
        if not record:
            return {"verified": False, "reason": "No provenance record found"}
        issues = []
        for inp in record.inputs:
            if inp not in self.records:
                issues.append(f"Missing provenance for input: {inp}")
        return {
            "verified": len(issues) == 0,
            "issues": issues,
            "entity": record.entity,
            "version": record.version,
        }

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "id": rec.id,
                "entity": rec.entity,
                "entity_type": rec.entity_type,
                "created_by": rec.created_by,
                "created_at": rec.created_at,
                "inputs": rec.inputs,
                "tools_used": rec.tools_used,
                "version": rec.version,
            }
            for rec in self.records.values()
        ]
