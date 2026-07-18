"""Discovery export endpoints — extracted from discovery_v8.py for God Object decomposition."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


logger = logging.getLogger("c4_cdi_turbo.api.v8.discovery.export")


class ExportRequest(BaseModel):
    """ExportRequest."""

    discovery: dict[str, Any]
    format: str = "markdown"


class ExportResponse(BaseModel):
    """ExportResponse."""

    status: str
    format: str
    filepath: str | None = None
    content_preview: str | None = None
    error: str | None = None


EXPORT_DIR = Path("discovery/batch_v3/exports").resolve()


def _normalize_discovery_for_markdown(discovery: dict[str, Any]) -> dict[str, Any]:
    hypothesis = discovery.get("hypothesis", {})
    if isinstance(hypothesis, dict):
        hypothesis_text = hypothesis.get("text", str(hypothesis))
    else:
        hypothesis_text = str(hypothesis) if hypothesis else "N/A"
    c4_path = discovery.get("c4_path", {})
    if isinstance(c4_path, dict):
        c4_path_list = c4_path.get("operators", [c4_path.get("summary", "")])
    elif isinstance(c4_path, list):
        c4_path_list = c4_path
    else:
        c4_path_list = []
    contradiction = (
        discovery.get("contradiction")
        or str(discovery.get("triz_result", {}).get("contradiction", ""))
        or str(discovery.get("contradiction_mining", {}).get("contradiction", ""))
        or "N/A"
    )
    confidence = discovery.get("confidence") or discovery.get("best_hypothesis", {}).get(
        "confidence", 0.0
    )
    if not isinstance(confidence, (int, float)):
        confidence = float(confidence)
    falsifiability = discovery.get("falsifiability_criteria") or discovery.get("falsifier", {}).get(
        "counter_args", []
    )
    if not isinstance(falsifiability, list):
        falsifiability = []
    return {
        "created_at": discovery.get("created_at")
        or discovery.get("timestamp")
        or datetime.now().isoformat(),
        "domain": discovery.get("domain", "general"),
        "confidence": confidence,
        "problem": discovery.get("problem", "N/A"),
        "contradiction": contradiction,
        "hypothesis": hypothesis_text,
        "c4_path": c4_path_list,
        "falsifiability_criteria": falsifiability,
    }


def export_discovery(req: ExportRequest) -> ExportResponse:
    """Export discovery."""
    from src.export.manager import ExportManager

    supported: set[str] = {"markdown", "json", "latex", "bib", "html"}
    fmt = req.format.lower()
    if fmt not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {fmt}. Use: {', '.join(sorted(supported))}",
        )
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manager = ExportManager(output_dir=str(EXPORT_DIR))
    try:
        if fmt == "markdown":
            normalized = _normalize_discovery_for_markdown(req.discovery)
            filepath = manager.export_discovery_markdown(normalized)
        elif fmt == "json":
            filepath = manager.export_json(req.discovery)
        elif fmt == "bib":
            bibtex = req.discovery.get("paper", {}).get("bibtex") or req.discovery.get("bibtex", "")
            if not bibtex:
                raise HTTPException(
                    status_code=400,
                    detail="No bibtex field found in discovery. Include paper.bibtex or bibtex data.",
                )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = EXPORT_DIR / f"discovery_{timestamp}.bib"
            fp.write_text(str(bibtex))
            filepath = str(fp)
        elif fmt == "latex":
            paper = req.discovery.get("paper", {})
            if paper.get("error"):
                raise HTTPException(
                    status_code=400,
                    detail="Paper generation failed in the discovery. Cannot export LaTeX.",
                )
            hypothesis = req.discovery.get("hypothesis", {})
            if not hypothesis:
                raise HTTPException(
                    status_code=400, detail="No hypothesis found in discovery. Cannot export LaTeX."
                )
            from .pipeline import generate_paper

            paper_parts = generate_paper(
                hypothesis=hypothesis,
                papers=req.discovery.get("papers", []),
                proof=req.discovery.get("proof", {}),
            )
            latex_content = paper_parts.get("latex", "")
            if not latex_content:
                raise HTTPException(
                    status_code=400, detail="LaTeX generation returned empty content."
                )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = EXPORT_DIR / f"discovery_{timestamp}.tex"
            fp.write_text(latex_content)
            filepath = str(fp)
        elif fmt == "html":
            confidence = req.discovery.get("confidence") or req.discovery.get(
                "best_hypothesis", {}
            ).get("confidence", 0.0)
            if not isinstance(confidence, (int, float)):
                confidence = float(confidence)
            stats = {
                "discoveries": 1,
                "patterns": len(req.discovery.get("triz_principles", [])),
                "validated": 1 if req.discovery.get("status") == "complete" else 0,
                "avg_confidence": confidence,
            }
            filepath = manager.export_dashboard_html(stats, [req.discovery])
        content = Path(filepath).read_text()
        preview = content[:500] + ("..." if len(content) > 500 else "")
        # Audit 2026-06-22: increment DISCOVERIES_GENERATED Prometheus counter
        # on successful export. Best-effort — observability must not crash
        # the response.
        try:
            from src.api.routers.metrics import DISCOVERIES_GENERATED

            DISCOVERIES_GENERATED.labels(output_format=fmt).inc()
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)
        return ExportResponse(
            status="success", format=fmt, filepath=filepath, content_preview=preview
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Export error: %s", e)
        return ExportResponse(status="error", format=fmt, error=str(e))
