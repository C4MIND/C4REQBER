"""c4reqber: Slack Webhook — post preprint links to Slack channels."""
from __future__ import annotations

import os
from typing import Any

import httpx


class SlackWebhook:
    """Slack Incoming Webhook for posting preprint announcements.

    Auth: SLACK_WEBHOOK_URL from https://api.slack.com/apps → Incoming Webhooks.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.dry_run = dry_run

    @property
    def configured(self) -> bool:
        return bool(self.url)

    async def send(self, text: str = "", blocks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Send a message to Slack."""
        if self.dry_run:
            return {"status": "sent", "_dry_run": True}
        if not self.url:
            return {"error": "SLACK_WEBHOOK_URL not configured"}

        payload: dict[str, Any] = {}
        if text:
            payload["text"] = text[:3000]
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient() as c:
            resp = await c.post(self.url, json=payload, timeout=15)
            if resp.status_code == 200:
                return {"status": "sent"}
            return {"error": f"Slack HTTP {resp.status_code}: {resp.text[:200]}"}

    async def send_preprint(self, title: str, url: str, abstract: str = "") -> dict[str, Any]:
        """Post a preprint announcement with Slack blocks."""
        return await self.send(
            text=f"📄 *New Preprint:* <{url}|{title}>",
            blocks=[
                {"type": "header", "text": {"type": "plain_text", "text": "📄 New Preprint"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*<{url}|{title}>*\n{abstract[:500]}"}},
            ],
        )
