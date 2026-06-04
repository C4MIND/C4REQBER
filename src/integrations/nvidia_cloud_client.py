"""NVIDIA Cloud GPU Integration — NGC cloud GPU instances."""
from __future__ import annotations

import os
from typing import Any

import httpx


NGC_API_URL = "https://api.ngc.nvidia.com/v2"


class NVIDIACloudClient:
    """NVIDIA Cloud GPU client — $10 balance."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("NVIDIA_CLOUD_API_KEY")
        self.enabled = bool(self.api_key)

    async def list_gpus(self) -> list[dict[str, Any]]:
        """List available GPU instances."""
        if not self.enabled:
            raise RuntimeError("NVIDIA_CLOUD_API_KEY not set")

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{NGC_API_URL}/org/nvidia/team/nga/resources",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("resources", [])

    async def get_balance(self) -> dict[str, Any]:
        """Get account balance/info."""
        if not self.enabled:
            return {"enabled": False, "balance": 0.0}

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{NGC_API_URL}/users/me",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()

    def status(self) -> dict[str, Any]:
        """Return client status for dashboard."""
        return {
            "name": "NVIDIA Cloud",
            "enabled": self.enabled,
            "provider": "nvidia_cloud",
            "icon": "🟢",
            "balance": "$10.00",
        }
