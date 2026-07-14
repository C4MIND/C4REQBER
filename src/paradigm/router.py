"""Paradigm Shift Detection API - /v7/paradigm"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.paradigm.anomaly import AnomalyTracker
from src.paradigm.detector import (  # type: ignore[attr-defined]
    DetectRequest,
    DetectResult,
    ParadigmShiftDetector,
)


router = APIRouter(prefix="/api/v7/paradigm", tags=["paradigm"])

detector = ParadigmShiftDetector()
anomaly_tracker = AnomalyTracker()

@router.post("/detect", response_model=DetectResult)
async def detect_paradigm_shift(request: DetectRequest) -> DetectResult:
    """Detect potential paradigm shifts in a scientific field"""
    return detector.detect(request)

@router.get("/fields")
async def list_fields() -> dict[str, Any]:
    """List fields available for paradigm shift detection"""
    fields = anomaly_tracker.get_all_fields()
    summaries = {f: anomaly_tracker.field_summary(f) for f in fields}
    return {
        "fields": fields,
        "count": len(fields),
        "summaries": summaries,
        "description": "Scientific fields with anomaly databases for paradigm shift detection",
    }

@router.get("/anomalies")
async def list_anomalies(
    field: str = Query(..., description="Scientific field to query"),
    min_severity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum severity threshold"),
    search: str = Query(None, description="Search term for anomaly descriptions"),
) -> dict[str, Any]:
    """List anomalies for a given field"""
    if search:
        results = anomaly_tracker.search_anomalies(search)
        if field != "*":
            results = [a for a in results if a.field.lower() == field.lower()]
    else:
        results = anomaly_tracker.get_by_field(field)

    if min_severity > 0:
        results = [a for a in results if a.severity >= min_severity]

    return {
        "field": field,
        "anomalies": results,
        "count": len(results),
    }

@router.get("/temporal/{field}")
async def temporal_analysis(
    field: str,
    days: int = Query(365, ge=1, description="Time window in days"),
) -> dict[str, Any]:
    """Get temporal analysis for a field"""
    anomalies = detector.detect_anomalies(field, days)
    if not anomalies:
        return {"field": field, "anomalies": [], "analysis": None}

    analysis = detector.analyze_temporal_patterns(anomalies)
    return {
        "field": field,
        "anomaly_count": len(anomalies),
        "analysis": analysis,
    }

@router.post("/anomalies")
async def add_anomaly(anomaly: dict[str, Any]) -> dict[str, Any]:
    """Add a new anomaly to the tracker"""
    from src.paradigm.models import Anomaly

    try:
        new_anomaly = Anomaly(
            id=anomaly["id"],
            field=anomaly["field"],
            description=anomaly["description"],
            severity=float(anomaly["severity"]),
            first_detected=anomaly["first_detected"],
            citations_affected=int(anomaly.get("citations_affected", 0)),
        )
        anomaly_tracker.add_anomaly(new_anomaly)
        return {"status": "added", "anomaly": new_anomaly}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid anomaly data: {e}") from e
