from __future__ import annotations


"""n8n integration for c44tcdi."""

import os
from typing import Any

import httpx


class N8NClient:
    """Client for n8n workflow automation."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get('N8N_API_KEY', '')
        self.enabled = bool(self.api_key)
        self.base_url = os.environ.get('N8N_BASE_URL', '')

    async def trigger_workflow(self, workflow_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Trigger workflow."""
        if not self.enabled:
            return {'error': 'API key not set'}
        if not self.base_url:
            return {'error': 'N8N base URL not configured'}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/workflows/{workflow_id}/execute",
                    headers={"X-N8N-API-KEY": self.api_key or ''},
                    json=data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {'error': str(e)}

    def test_connection(self) -> dict[str, Any]:
        return {'available': self.enabled, 'error': None if self.enabled else 'No API key'}
