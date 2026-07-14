"""YandexGPT integration — real async client via Yandex Cloud."""

from __future__ import annotations

import os
from typing import Any

import httpx


class YandexGPTClient:
    """Client for YandexGPT API (Yandex Cloud)."""

    def __init__(
        self,
        api_key: str | None = None,
        folder_id: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("YANDEX_API_KEY", "")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID", "")
        self.base_url = os.getenv(
            "YANDEX_API_URL",
            "https://llm.api.cloud.yandex.net/foundationModels/v1",
        )
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.folder_id)

    def _headers(self) -> dict[str, str]:
        folder = self.folder_id or ""
        return {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": folder,
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[dict],
        model: str = "yandexgpt-lite",
        temperature: float = 0.6,
        max_tokens: int = 800,
    ) -> dict:
        """Send chat completion request to YandexGPT."""
        if not self.available:
            return {"error": "YANDEX_API_KEY + YANDEX_FOLDER_ID required"}

        yandex_messages = []
        for msg in messages:
            yandex_messages.append({
                "role": msg.get("role", "user"),
                "text": msg.get("content", ""),
            })

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/completion",
                headers=self._headers(),
                json={
                    "modelUri": f"gpt://{self.folder_id}/{model}",
                    "completionOptions": {
                        "stream": False,
                        "temperature": temperature,
                        "maxTokens": str(max_tokens),
                    },
                    "messages": yandex_messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            alternatives = data.get("result", {}).get("alternatives", [])
            if alternatives:
                return {
                    "choices": [{
                        "message": {
                            "content": alternatives[0].get("message", {}).get("text", ""),
                            "role": "assistant",
                        }
                    }]
                }
            return data

    async def test_connection(self) -> dict[str, Any]:
        """Test API connectivity."""
        try:
            resp = await self.chat(
                [{"role": "user", "content": "ping"}],
                max_tokens=3,
            )
            return {"healthy": "choices" in resp}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
