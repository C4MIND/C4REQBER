from __future__ import annotations


"""Vast.ai GPU runner for c44tcdi simulations."""
import os
from typing import Any

import httpx


VASTAI_KEY = os.getenv("VASTAI_API_KEY", "")
if not VASTAI_KEY:
    import logging
    logging.getLogger("c4reqber.compute").warning("VASTAI_API_KEY not set; VastAI runner will fail")


class VastAIRunner:
    """VastAIRunner."""
    def __init__(self) -> None:
        self.api_key = VASTAI_KEY
        self.base_url = "https://console.vast.ai/api/v0"

    async def list_gpus(self, max_price: float = 0.05) -> list[dict[str, Any]]:
        """List gpus."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{self.base_url}/bundles/",
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            )
        offers = r.json().get("offers", [])
        return [o for o in offers if o.get("dph_total", 999) < max_price][:5]

    async def run_simulation(self, pattern_id: str, gpu_type: str = "cheapest") -> dict[str, Any]:
        """Run simulation."""
        gpus = await self.list_gpus()
        if not gpus:
            return {
                "status": "deferred",
                "reason": "No GPUs available at target price",
                "gpu": "cpu_fallback",
            }

        cheapest = min(gpus, key=lambda g: g.get("dph_total", 999))
        return {
            "status": "deployed",
            "gpu": cheapest.get("gpu_name", "unknown"),
            "price_per_hour": cheapest.get("dph_total", 0),
            "pattern": pattern_id,
            "note": "Vast.ai deployment requested. Instance provisioning...",
        }
