"""@C4ScienceBot — solve problems via Telegram."""
from __future__ import annotations

import asyncio
import os


class TelegramBot:
    """Telegram bot for c4-cdi-turbo."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def start(self) -> None:
        """Start."""
        offset = 0
        while True:
            updates = await self._get_updates(offset)
            for update in updates:
                await self._handle_message(update)
                offset = update["update_id"] + 1
            await asyncio.sleep(1)

    async def _handle_message(self, update: dict) -> None:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]
        if text.startswith("/solve"):
            problem = text.replace("/solve", "").strip()
            await self._send_message(chat_id, f"🔬 Анализ: {problem}\nРешение: [C4 engine processing...]")
        elif text.startswith("/start"):
            await self._send_message(chat_id, "🔬 C4 Science Bot\n/solve [проблема] — решить\n/pricing — тарифы")
        elif text == "/pricing":
            await self._send_message(chat_id, "💰 Free: $0 | PRO: $10 | TEAM: $19 | ENTERPRISE: $49")

    async def _send_message(self, chat_id: int, text: str) -> None:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/sendMessage", json={"chat_id": chat_id, "text": text})

    async def _get_updates(self, offset: int) -> list:
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/getUpdates", params={"offset": offset, "timeout": 30})
            return r.json().get("result", [])

def run_bot() -> None:
    asyncio.run(TelegramBot().start())
