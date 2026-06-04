"""c4reqber: Zenodo REST API Client — deposit, upload, publish, get DOI."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import httpx


ZENODO_BASE = "https://zenodo.org/api"


class ZenodoClient:
    """Zenodo REST API client for preprint deposit and publication.

    Auth: ``ZENODO_ACCESS_TOKEN`` from https://zenodo.org/account/settings/applications/

    Usage::

        zc = ZenodoClient()
        dep = await zc.create_deposit(title="My Paper", description="...")
        await zc.upload_file(dep["id"], Path("paper.pdf"))
        result = await zc.publish(dep["id"])
        print(result["doi"])  # 10.5281/zenodo.12345
    """

    def __init__(self, access_token: str = "", dry_run: bool = False) -> None:
        self.token = access_token or os.getenv("ZENODO_ACCESS_TOKEN", "")
        self.dry_run = dry_run
        self._headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self._last_status: int = 0

    @property
    def configured(self) -> bool:
        return bool(self.token)

    # ── Core API ────────────────────────────────────────────────────

    async def create_deposit(self, title: str, description: str = "", creators: list[dict[str, str]] | None = None, **meta: Any) -> dict[str, Any]:
        """Create a new deposit. Returns deposit JSON with ``id``."""
        if self.dry_run:
            return {"id": "dry-run-1", "doi": "10.5281/zenodo.dry-run", "title": title, "_dry_run": True}

        payload: dict[str, Any] = {
            "metadata": {
                "title": title[:500],
                "upload_type": "preprint",
                "description": description[:2000] if description else f"Preprint: {title}",
                "creators": creators or [{"name": "c4reqber Researcher"}],
                **{k: v for k, v in meta.items() if k not in ("title", "description", "creators")},
            }
        }
        return await self._request("POST", "/deposit/depositions", json=payload)

    async def upload_file(self, deposit_id: str, filepath: Path) -> dict[str, Any]:
        """Upload a file to an existing deposit."""
        if self.dry_run:
            return {"filename": filepath.name, "filesize": filepath.stat().st_size if filepath.exists() else 0, "_dry_run": True}

        if not filepath.exists():
            return {"error": f"File not found: {filepath}"}

        with filepath.open("rb") as f:
            return await self._request(
                "POST",
                f"/deposit/depositions/{deposit_id}/files",
                data={"name": filepath.name},
                files={"file": (filepath.name, f, "application/octet-stream")},
            )

    async def add_metadata(self, deposit_id: str, **meta: Any) -> dict[str, Any]:
        """Update deposit metadata."""
        if self.dry_run:
            return {"id": deposit_id, "_dry_run": True}
        return await self._request("PUT", f"/deposit/depositions/{deposit_id}", json={"metadata": meta})

    async def publish(self, deposit_id: str) -> dict[str, Any]:
        """Publish a deposit. Returns published record with DOI."""
        if self.dry_run:
            return {"id": deposit_id, "doi": f"10.5281/zenodo.{deposit_id}.dry-run", "conceptdoi": f"10.5281/zenodo.{deposit_id}", "_dry_run": True}

        result = await self._request("POST", f"/deposit/depositions/{deposit_id}/actions/publish")
        return result

    async def list_deposits(self, query: str = "") -> list[dict[str, Any]]:
        """List user's deposits (for dedup check)."""
        if self.dry_run:
            return []
        params = {"q": query} if query else {}
        return await self._request("GET", "/deposit/depositions", params=params)

    async def get_deposit(self, deposit_id: str) -> dict[str, Any]:
        """Get a single deposit by ID."""
        if self.dry_run:
            return {"id": deposit_id, "_dry_run": True}
        return await self._request("GET", f"/deposit/depositions/{deposit_id}")

    # ── High-level flow ─────────────────────────────────────────────

    async def publish_preprint(self, title: str, filepath: Path, description: str = "", creators: list[dict[str, str]] | None = None) -> dict[str, Any]:
        """Full flow: create deposit → upload file → publish → return DOI."""
        if not self.configured and not self.dry_run:
            return {"error": "ZENODO_ACCESS_TOKEN not configured. Get token: https://zenodo.org/account/settings/applications/"}

        # 1. Check for existing deposit with same title
        existing = await self.list_deposits(query=f"title:\"{title[:100]}\"")
        if existing:
            for dep in existing:
                if dep.get("title", "").lower() == title.lower():
                    return {"status": "exists", "doi": dep.get("doi", ""), "id": dep.get("id", ""),
                            "message": "Deposit with this title already exists. Use update or skip."}

        # 2. Create
        dep = await self.create_deposit(title=title, description=description, creators=creators)
        if "error" in dep:
            return dep
        deposit_id = str(dep.get("id", ""))

        # 3. Upload
        up = await self.upload_file(deposit_id, filepath)
        if "error" in up:
            return {**up, "deposit_id": deposit_id, "status": "upload_failed"}

        # 4. Publish
        result = await self.publish(deposit_id)
        result["deposit_id"] = deposit_id
        return result

    # ── HTTP helper ──────────────────────────────────────────────────

    async def _request(self, method: str, path: str, max_retries: int = 3, **kwargs: Any) -> Any:
        if not self.token and not self.dry_run:
            return {"error": "ZENODO_ACCESS_TOKEN not set"}

        url = f"{ZENODO_BASE}{path}"
        headers = {**self._headers}
        if "files" not in kwargs:
            headers["Content-Type"] = "application/json"

        last_error = ""
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.request(method, url, headers=headers, **kwargs)
                    self._last_status = resp.status_code
                    if resp.status_code in (200, 201, 202):
                        return resp.json() if resp.text else {"status": "ok"}
                    if resp.status_code == 429:
                        wait = min(2 ** attempt, 30)
                        time.sleep(wait)
                        continue
                    return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
            except httpx.TimeoutException:
                last_error = "timeout"
                time.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return {"error": f"Zenodo API failed after {max_retries} retries: {last_error}"}
