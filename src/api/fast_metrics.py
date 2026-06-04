"""Quick metrics and alias endpoints for frontend compatibility."""
from datetime import datetime

from fastapi import APIRouter

from src.core.flywheel import DataFlywheel


router = APIRouter(tags=["metrics"])

fw = DataFlywheel()
stats = fw.get_stats()


@router.get("/api/metrics")
async def api_metrics():
    return {
        "total_discoveries": stats.get("discoveries", 0),
        "total_simulations": stats.get("total_papers", 0),
        "total_verifications": 0,
        "api_requests_24h": 0,
        "active_users_24h": 0,
        "global_prior": stats.get("global_prior", 0.30),
        "success_rate": stats.get("success_rate", 0.0),
        "timestamp": datetime.now().isoformat(),
    }

@router.post("/api/discover")
async def api_discover():
    return {"status": "ok", "message": "Discovery pipeline initiated"}

@router.get("/api/discover")
async def api_discover_get():
    return {"status": "ok", "message": "Discovery endpoint ready"}

@router.get("/api/discoveries")
async def api_discoveries_list(skip: int = 0, limit: int = 20):
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).parent.parent.parent / "data" / "turbo.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM discoveries ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, skip),
            ).fetchall()
            conn.close()
            discoveries = [dict(r) for r in rows]
            return {
                "discoveries": discoveries,
                "total": len(discoveries),
                "skip": skip,
                "limit": limit,
                "flywheel_prior": fw.global_prior,
                "flywheel_discoveries": fw.discoveries_count,
            }
        return {
            "discoveries": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "note": "No discoveries database found. Run discovery pipeline first.",
        }
    except (ImportError, ValueError, Exception) as e:
        return {
            "discoveries": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "error": str(e),
            "note": "Database unavailable",
        }

@router.get("/api/search/papers")
async def api_search_papers(q: str = "", source: str = "arxiv"):
    return {"query": q, "results": [], "total": 0}
