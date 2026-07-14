"""
c4reqber: Agenda API Router (v8)

Endpoints for self-directed research agenda generation and management.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

import networkx as nx
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from src.agenda.feasibility import FeasibilityChecker
from src.agenda.generator import AgendaGenerator
from src.agenda.priority import PriorityScorer
from src.agenda.progress import ProgressTracker
from src.api.errors import C4APIError, ValidationError


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/agenda", tags=["v8-agenda"])
_tracker = ProgressTracker()


class AgendaRequest(BaseModel):
    """Request to generate research agenda from knowledge state."""

    model_config = {"json_schema_extra": {"example": {
        "knowledge_graph": {"nodes": ["causality", "quantum_entanglement"], "edges": [["causality", "quantum_entanglement"]]},
        "recent_results": [{"hypothesis": {"text": "Entanglement enables nonlocal causality"}}],
        "n_questions": 5,
    }}}

    knowledge_graph: dict[str, Any] = Field(
        default_factory=dict,
        description="Graph with 'nodes' and 'edges' keys",
    )
    recent_results: list[dict] = Field(default_factory=list)
    n_questions: int = Field(default=5, ge=1, le=50)


class ApproveRequest(BaseModel):
    """Request to approve, reject, or modify a research question."""

    model_config = {"json_schema_extra": {"example": {
        "question_text": "Does quantum entanglement violate Bell inequalities under weak measurement?",
        "action": "approve",
    }}}

    question_text: str = Field(..., min_length=1, max_length=2000)
    action: Literal["approve", "reject", "modify"]
    modified_text: str | None = Field(default=None, max_length=2000)


class ModifyRequest(BaseModel):
    """Request to modify and enqueue a research question."""

    model_config = {"json_schema_extra": {"example": {
        "question_text": "Original question",
        "modified_text": "Refined question with narrower scope",
    }}}

    question_text: str = Field(..., min_length=1, max_length=2000)
    modified_text: str = Field(..., min_length=1, max_length=2000)


@router.post("/generate")
async def generate_agenda(req: AgendaRequest) -> dict[str, Any]:
    """Generate research agenda from current knowledge state."""
    try:
        # Reconstruct knowledge graph from dict
        graph = nx.Graph()
        for node in req.knowledge_graph.get("nodes", []):
            graph.add_node(node)
        for edge in req.knowledge_graph.get("edges", []):
            if isinstance(edge, (list, tuple)) and len(edge) == 2:
                graph.add_edge(edge[0], edge[1])

        generator = AgendaGenerator()
        questions = generator.generate(graph, req.recent_results, req.n_questions)

        # Check feasibility and score
        checker = FeasibilityChecker()
        scorer = PriorityScorer()
        scored = []
        for q in questions:
            feasibility = checker.check(q)
            score = scorer.score(q, feasibility)
            scored.append({
                **q.to_dict(),
                "feasibility": feasibility.to_dict(),
                "priority_score": round(score, 3),
            })

        return {
            "questions": scored,
            "count": len(scored),
        }
    except Exception as e:
        logger.exception("Agenda generation failed")
        raise C4APIError(
            message=f"Agenda generation failed: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="agenda_generation_failed",
        ) from e


@router.post("/approve")
async def approve_question(req: ApproveRequest) -> dict[str, Any]:
    """Approve, reject, or modify a research question."""
    if req.action == "approve":
        _tracker.add_approved(req.question_text)
        return {
            "status": "approved",
            "question": req.question_text,
            "message": "Question queued for next discovery pipeline run.",
        }
    if req.action == "reject":
        _tracker.add_rejected(req.question_text)
        return {
            "status": "rejected",
            "question": req.question_text,
            "message": "Question rejected.",
        }
    if req.action == "modify":
        if not req.modified_text:
            raise ValidationError(
                message="modified_text is required when action='modify'",
                detail={"field": "modified_text", "action": req.action},
            )
        _tracker.add_approved(req.modified_text)
        return {
            "status": "modified",
            "original": req.question_text,
            "modified": req.modified_text,
            "message": "Question modified and queued.",
        }
    raise ValidationError(
        message=f"Unknown action: {req.action}",
        detail={"field": "action", "received": req.action},
    )


@router.get("/progress")
async def get_progress() -> dict[str, Any]:
    """Get current research progress."""
    try:
        return _tracker.to_dict()
    except Exception as e:
        logger.exception("Failed to retrieve agenda progress")
        raise C4APIError(
            message=f"Failed to retrieve progress: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="progress_retrieval_failed",
        ) from e
