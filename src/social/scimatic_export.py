from __future__ import annotations

import os
from typing import Any

import httpx


SCIMATIC_BASE_URL = "https://scimatic.org/api"


def _get_api_key() -> str:
    api_key = os.getenv("SCIMATIC_API_KEY")
    if not api_key:
        raise ValueError("SCIMATIC_API_KEY environment variable is required")
    return api_key


def export_thesis(chapters: list[dict]) -> str:
    """Export thesis."""
    api_key = _get_api_key()
    response = httpx.post(
        f"{SCIMATIC_BASE_URL}/thesis/export",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"chapters": chapters}
    )
    response.raise_for_status()
    return response.json().get("latex", "")


def export_bibtex(papers: list[str]) -> str:
    """Export bibtex."""
    api_key = _get_api_key()
    response = httpx.post(
        f"{SCIMATIC_BASE_URL}/bibtex/export",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"papers": papers}
    )
    response.raise_for_status()
    return response.json().get("bibtex", "")


class SciMaticClient:
    """Client for SciMatic API."""

    def __init__(self) -> None:
        self.base_url = SCIMATIC_BASE_URL
        self.api_key = os.environ.get("SCIMATIC_API_KEY", "")

    def export(self, data: dict[str, Any]) -> dict[str, Any]:
        """Export data to SciMatic."""
        if not self.api_key:
            return {"status": "error", "message": "SCIMATIC_API_KEY required"}

        return {
            "status": "pending",
            "message": "SciMatic export pending",
            "data": data
        }
