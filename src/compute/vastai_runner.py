from __future__ import annotations


"""Vast.ai GPU runner — lists offers; does not fake deploy/execute."""

import logging
import os
from typing import Any

import httpx

from src.simulations.vastai_delegate import VastAIDelegate


logger = logging.getLogger("c4reqber.compute")

VASTAI_KEY = os.getenv("VASTAI_API_KEY") or os.getenv("VAST_API_KEY") or ""
if not VASTAI_KEY:
    logger.warning("VASTAI_API_KEY/VAST_API_KEY not set; VastAI runner will fail closed")


class VastAIRunner:
    """List GPU offers; execute only via :class:`VastAIDelegate` SSH path."""

    def __init__(self) -> None:
        self.api_key = VASTAI_KEY
        self.base_url = "https://console.vast.ai/api/v0"
        self._delegate = VastAIDelegate(api_key=self.api_key or None)

    async def list_gpus(self, max_price: float = 0.05) -> list[dict[str, Any]]:
        """List gpus under max_price $/hr."""
        if not self.api_key:
            return []
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{self.base_url}/bundles/",
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            )
        offers = r.json().get("offers", [])
        return [o for o in offers if o.get("dph_total", 999) < max_price][:5]

    async def run_simulation(
        self,
        pattern_id: str,
        gpu_type: str = "cheapest",
        *,
        engine: str = "newton",
        config: dict[str, Any] | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        """
        Without ``execute=True``, only report offers — never ``status: deployed``.

        With ``execute=True``, delegates to :meth:`VastAIDelegate.run_simulation`
        (real SSH remote_argv).
        """
        cfg = dict(config or {})
        cfg.setdefault("pattern_id", pattern_id)
        if gpu_type and gpu_type != "cheapest":
            cfg.setdefault("gpu_name", gpu_type)

        if not execute:
            gpus = await self.list_gpus(max_price=float(cfg.get("max_price_per_hour", 2.0)))
            if not gpus:
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "reason": "No GPUs available (or no API key) — not deployed",
                    "pattern": pattern_id,
                }
            cheapest = min(gpus, key=lambda g: g.get("dph_total", 999))
            return {
                "status": "offer_only",
                "stub": True,
                "executed": False,
                "gpu": cheapest.get("gpu_name", "unknown"),
                "price_per_hour": cheapest.get("dph_total", 0),
                "pattern": pattern_id,
                "note": (
                    "Offer listed only. Pass execute=True (and remote_argv) "
                    "to SSH-run via VastAIDelegate — refusing fake 'deployed'."
                ),
            }

        result = await self._delegate.run_simulation(engine, cfg)
        return {
            "status": "completed" if result.success else "unavailable",
            "stub": not result.success,
            "executed": bool(result.data.get("executed"))
            if isinstance(result.data, dict)
            else False,
            "success": result.success,
            "data": result.data,
            "cost_usd": result.cost_usd,
            "duration_seconds": result.duration_seconds,
            "logs": result.logs,
            "pattern": pattern_id,
            "engine": engine,
        }
