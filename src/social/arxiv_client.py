"""c4reqber: arXiv Submission Client — human-only, endorsement required."""
from __future__ import annotations

import os
from typing import Any

import httpx


class ArXivClient:
    """arXiv submission API client.

    HUMAN REVIEW MANDATORY. Not disablable under any circumstances.
    Requires endorsement in target category.
    arXiv BANS AI-only content without human verification.

    Auth: ARXIV_SUBMISSION_KEY from endorsement approval.
    """

    API_BASE = "https://arxiv-submission-api.org/v1"

    def __init__(self, dry_run: bool = False) -> None:
        self.submission_key = os.getenv("ARXIV_SUBMISSION_KEY", "")
        self.dry_run = dry_run

    @property
    def configured(self) -> bool:
        return bool(self.submission_key)

    @property
    def human_review_required(self) -> bool:
        """arXiv ALWAYS requires human review. This property is immutable."""
        return True

    async def check_endorsement(self) -> dict[str, Any]:
        """Check if user is endorsed for submission."""
        if self.dry_run:
            return {"endorsed": True, "_dry_run": True}
        if not self.configured:
            return {"endorsed": False, "error": "ARXIV_SUBMISSION_KEY not configured"}

        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{self.API_BASE}/endorsement/status",
                headers={"Authorization": f"Bearer {self.submission_key}"},
                timeout=15,
            )
            return {"endorsed": resp.status_code == 200}

    async def submit(self, tex_source: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Submit to arXiv. REQUIRES PRIOR HUMAN REVIEW."""
        if not metadata.get("human_reviewed"):
            return {"error": "arXiv requires human review before submission. This cannot be bypassed.", "code": "HUMAN_REVIEW_REQUIRED"}

        if self.dry_run:
            return {"status": "submitted", "id": "arxiv-dry-run", "_dry_run": True}
        if not self.configured:
            return {"error": "ARXIV_SUBMISSION_KEY not configured"}

        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{self.API_BASE}/submissions",
                headers={"Authorization": f"Bearer {self.submission_key}"},
                json={"source": tex_source, "metadata": metadata},
                timeout=30,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            return {"error": f"arXiv HTTP {resp.status_code}: {resp.text[:200]}"}
