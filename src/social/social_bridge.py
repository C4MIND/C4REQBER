"""c4reqber: Social Bridge — pipeline-to-drafts handoff hook."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from src.social.profile_manager import UserProfile


DRAFTS_DIR = Path.home() / ".c4reqber" / "drafts"


async def transfer_to_drafts(discovery_record: Any, social_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Hook called by pipeline after Phase G. Copies dissertation to drafts."""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    topic = getattr(discovery_record, "topic", "discovery") if hasattr(discovery_record, "topic") else "discovery"
    slug = topic.lower().replace(" ", "_")[:30]

    date_str = datetime.now().strftime("%Y-%m-%d")
    draft_id = f"{date_str}_{slug}"
    draft_dir = DRAFTS_DIR / draft_id
    draft_dir.mkdir(parents=True, exist_ok=True)

    # Copy dissertation
    diss = getattr(discovery_record, "dissertation", None)
    if diss and hasattr(diss, "content"):
        (draft_dir / "dissertation.md").write_text(str(diss.content), encoding="utf-8")

    # Embed profile
    profile = UserProfile.load()
    metadata: dict[str, Any] = {
        "title": topic,
        "authors": [{"name": a.name, "orcid": a.orcid, "affiliation": a.affiliation} for a in profile.authors],
        "date": date_str,
    }
    (draft_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    # Draft state
    (draft_dir / "draft_state.json").write_text(json.dumps({
        "id": draft_id, "status": "pending_review", "created_at": datetime.now().timestamp(),
        "platforms": {}, "edit_history": [],
    }, indent=2), encoding="utf-8")

    return {"draft_id": draft_id, "path": str(draft_dir), "status": "pending_review"}
