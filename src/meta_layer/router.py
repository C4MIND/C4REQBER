"""Meta Layer API Router — /v7/meta"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.meta_layer.collaboration import CollaborationManager
from src.meta_layer.ethics import ETHICS_CHECKLIST, run_ethics_check
from src.meta_layer.provenance import ProvenanceTracker


router = APIRouter(prefix="/api/v7/meta", tags=["meta"])

collab_manager = CollaborationManager()
provenance_tracker = ProvenanceTracker()

# ═══════════════════════════════════════════════════════════
# Collaboration endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/collaborations")
async def create_collaboration(request: dict[str, Any]) -> dict[str, Any]:
    """
    Create a collaboration.

    Body:
    {
        "project": "C4REQBER",
        "contributors": [
            {"name": "Alice", "role": "researcher"},
            {"name": "Bob", "role": "engineer"}
        ]
    }
    """
    project = request.get("project")
    contributors = request.get("contributors", [])
    if not project:
        raise HTTPException(status_code=400, detail="project is required")
    if not contributors:
        raise HTTPException(status_code=400, detail="contributors is required")

    collab = collab_manager.create(project=project, contributors=contributors)
    return {
        "id": collab.id,
        "project": collab.project,
        "contributors": [
            {"id": c.id, "name": c.name, "role": c.role} for c in collab.contributors
        ],
        "created_at": collab.created_at,
        "status": collab.status,
    }

@router.post("/collaborations/{collab_id}/contributions")
async def add_contribution(
    collab_id: str, request: dict[str, Any]
) -> dict[str, Any]:
    """
    Add a contribution to a collaboration.

    Body:
    {
        "contributor_id": "abc12345",
        "action": "wrote",
        "detail": "Added literature review module"
    }
    """
    contributor_id = request.get("contributor_id", "")
    action = request.get("action", "")
    detail = request.get("detail", "")
    if not all([contributor_id, action, detail]):
        raise HTTPException(
            status_code=400,
            detail="contributor_id, action, and detail are required",
        )

    if collab_id not in collab_manager.collaborations:
        raise HTTPException(status_code=404, detail=f"Collaboration {collab_id} not found")

    collab_manager.add_contribution(
        collab_id=collab_id,
        contributor_id=contributor_id,
        action=action,
        detail=detail,
    )
    return {"status": "ok", "collab_id": collab_id, "contributor_id": contributor_id}

@router.get("/collaborations/{collab_id}/stats")
async def get_collaboration_stats(collab_id: str) -> dict[str, Any]:
    """Get collaboration statistics."""
    stats = collab_manager.get_stats(collab_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Collaboration {collab_id} not found")
    return stats

@router.get("/collaborations")
async def list_collaborations() -> dict[str, Any]:
    """List all collaborations."""
    return {"collaborations": collab_manager.list_all()}

# ═══════════════════════════════════════════════════════════
# Provenance endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/provenance")
async def record_provenance(request: dict[str, Any]) -> dict[str, Any]:
    """
    Record provenance for an entity.

    Body:
    {
        "entity": "SWOT analysis for Market X",
        "entity_type": "hypothesis",
        "created_by": "agent-7",
        "inputs": ["data-source-1", "data-source-2"],
        "tools": ["SWOT_plugin", "GPT-4"]
    }
    """
    entity = request.get("entity", "")
    entity_type = request.get("entity_type", "")
    created_by = request.get("created_by", "")
    inputs = request.get("inputs", [])
    tools = request.get("tools", [])

    if not all([entity, entity_type, created_by]):
        raise HTTPException(
            status_code=400,
            detail="entity, entity_type, and created_by are required",
        )

    record = provenance_tracker.record(
        entity=entity,
        entity_type=entity_type,
        created_by=created_by,
        inputs=inputs,
        tools=tools,
    )
    return {
        "id": record.id,
        "entity": record.entity,
        "entity_type": record.entity_type,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "inputs": record.inputs,
        "tools_used": record.tools_used,
        "version": record.version,
    }

@router.get("/provenance/{entity_id}/lineage")
async def get_lineage(entity_id: str) -> dict[str, Any]:
    """Get upstream lineage for an entity."""
    lineage = provenance_tracker.get_lineage(entity_id)
    return {"entity_id": entity_id, "lineage": lineage, "depth": len(lineage)}

@router.get("/provenance/{entity_id}/verify")
async def verify_provenance(entity_id: str) -> dict[str, Any]:
    """Verify provenance integrity for an entity."""
    return provenance_tracker.verify(entity_id)

@router.get("/provenance")
async def list_provenance() -> dict[str, Any]:
    """List all provenance records."""
    return {"records": provenance_tracker.list_all()}

# ═══════════════════════════════════════════════════════════
# Ethics endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/ethics/check")
async def check_ethics(request: dict[str, Any]) -> dict[str, Any]:
    """
    Run an ethics assessment.

    Body:
    {
        "explainability": true,
        "no_bias": true,
        "no_pii": true,
        "fair": true,
        "safety_on": true
    }
    """
    report = run_ethics_check(request)
    return {
        "overall_score": report.overall_score,
        "checks": [
            {"name": c.name, "passed": c.passed, "score": c.score, "details": c.details}
            for c in report.checks
        ],
        "recommendations": report.recommendations,
    }

@router.get("/ethics/checklist")
async def get_checklist() -> dict[str, Any]:
    """Get the ethics checklist definition."""
    return {
        "checklist": [
            {"id": name, "description": desc, "weight": weight}
            for name, desc, weight in ETHICS_CHECKLIST
        ]
    }

@router.get("/")
async def meta_overview() -> dict[str, Any]:
    """Meta layer overview."""
    return {
        "module": "meta_layer",
        "version": "1.0.0",
        "components": {
            "collaboration": {
                "endpoints": [
                    "POST /v7/meta/collaborations",
                    "POST /v7/meta/collaborations/{id}/contributions",
                    "GET /v7/meta/collaborations/{id}/stats",
                    "GET /v7/meta/collaborations",
                ],
            },
            "provenance": {
                "endpoints": [
                    "POST /v7/meta/provenance",
                    "GET /v7/meta/provenance/{id}/lineage",
                    "GET /v7/meta/provenance/{id}/verify",
                    "GET /v7/meta/provenance",
                ],
            },
            "ethics": {
                "endpoints": [
                    "POST /v7/meta/ethics/check",
                    "GET /v7/meta/ethics/checklist",
                ],
            },
        },
    }
