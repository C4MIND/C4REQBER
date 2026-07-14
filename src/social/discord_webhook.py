"""c4reqber: Discord Webhook + Bot — post preprint links, interactive review."""
from __future__ import annotations

import os
from typing import Any

import httpx


class DiscordWebhook:
    """Discord webhook for posting preprint announcements.

    Auth: DISCORD_WEBHOOK_URL from channel settings → Integrations → Webhooks.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.url = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.dry_run = dry_run

    @property
    def configured(self) -> bool:
        return bool(self.url)

    async def send(self, content: str = "", embeds: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Send a message to Discord channel."""
        if self.dry_run:
            return {"status": "sent", "_dry_run": True}
        if not self.url:
            return {"error": "DISCORD_WEBHOOK_URL not configured"}

        payload: dict[str, Any] = {}
        if content:
            payload["content"] = content[:2000]
        if embeds:
            payload["embeds"] = embeds

        async with httpx.AsyncClient() as c:
            resp = await c.post(self.url, json=payload, timeout=15)
            if resp.status_code in (200, 204):
                return {"status": "sent"}
            return {"error": f"Discord HTTP {resp.status_code}: {resp.text[:200]}"}

    async def send_preprint(self, title: str, url: str, abstract: str = "") -> dict[str, Any]:
        """Post a preprint announcement with rich embed."""
        return await self.send(embeds=[{
            "title": title[:256],
            "url": url,
            "description": abstract[:2000] if abstract else f"New preprint: {title}",
            "color": 0x00ffcc,
            "fields": [{"name": "Platform", "value": "c4reqber", "inline": True}],
        }])
