"""c4reqber: Telegram Bot — preprint notifications + LLM-assisted editing."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import httpx


class TelegramBot:
    """Telegram Bot for preprint review notifications and LLM-assisted editing.

    Auth: TELEGRAM_BOT_TOKEN from @BotFather.
    Flow: bot sends preprint → inline buttons → user approves/requests changes → LLM edits.

    Uses raw httpx POST to api.telegram.org (no heavy deps).
    """

    API = "https://api.telegram.org"
    EDIT_SESSION_EXPIRY = 3600  # 1 hour

    def __init__(self, dry_run: bool = False) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.dry_run = dry_run
        self._edit_sessions: dict[str, dict[str, Any]] = {}

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    async def send_preprint_review(self, title: str, words: int, abstract: str, draft_id: str) -> dict[str, Any]:
        """Send a preprint for review with Approve/Changes/Reject buttons."""
        text = (
            f"📄 *{title[:200]}*\n"
            f"Words: {words} · Status: pending review\n\n"
            f"*Abstract:* {abstract[:500]}"
        )
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Approve", "callback_data": f"approve_{draft_id}"},
                {"text": "📝 Changes", "callback_data": f"edit_{draft_id}"},
                {"text": "❌ Reject", "callback_data": f"reject_{draft_id}"},
            ]]
        }
        return await self._send_message(text, reply_markup=keyboard)

    async def send_status(self, text: str) -> dict[str, Any]:
        """Send a simple status update."""
        return await self._send_message(text[:4000])

    async def _send_message(self, text: str, reply_markup: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.dry_run:
            return {"ok": True, "_dry_run": True}
        if not self.configured:
            return {"error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured"}

        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text[:4096],
            "parse_mode": "Markdown",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient() as c:
            resp = await c.post(f"{self.API}/bot{self.token}/sendMessage", json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"Telegram HTTP {resp.status_code}: {resp.text[:200]}"}

    async def get_updates(self, offset: int = 0) -> list[dict[str, Any]]:
        """Poll for callback queries (button clicks)."""
        if self.dry_run:
            return []
        async with httpx.AsyncClient() as c:
            resp = await c.get(f"{self.API}/bot{self.token}/getUpdates", params={"offset": offset, "timeout": 10})
            if resp.status_code == 200:
                return resp.json().get("result", [])
            return []

    # ── Callback Handler ───────────────────────────────────────────

    async def handle_updates(self) -> dict[str, Any]:
        """Process pending updates: detect button clicks, execute actions."""
        updates = await self.get_updates()
        results: dict[str, Any] = {}
        if not updates:
            return {}

        max_id = 0
        for update in updates:
            uid = update.get("update_id", 0)
            if uid > max_id:
                max_id = uid

            callback = update.get("callback_query")
            if not callback:
                continue

            data = callback.get("data", "")
            cb_id = callback.get("id", "")
            chat_id = str(callback.get("message", {}).get("chat", {}).get("id", ""))

            if data.startswith("approve_"):
                draft_id = data.replace("approve_", "")
                results[draft_id] = await self._handle_approve(draft_id, cb_id, chat_id)
            elif data.startswith("edit_"):
                draft_id = data.replace("edit_", "")
                results[draft_id] = await self._handle_edit_request(draft_id, cb_id, chat_id)
            elif data.startswith("reject_"):
                draft_id = data.replace("reject_", "")
                results[draft_id] = await self._handle_reject(draft_id, cb_id, chat_id)

        await self.get_updates(offset=max_id + 1)  # acknowledge
        return results

    async def _handle_approve(self, draft_id: str, callback_id: str, chat_id: str) -> dict[str, Any]:
        import json
        import time
        from pathlib import Path
        state_path = Path.home() / ".c4reqber" / "drafts" / draft_id / "draft_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state.get("status") != "pending_review":
                await self._send_message("This preprint was already reviewed.")
                return {"status": "already_reviewed", "draft_id": draft_id}
        state = {"id": draft_id, "status": "approved", "approved_at": time.time(), "via": "telegram"}
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2))
        await self._send_message(f"✅ Approved: {draft_id}. Publish with: `blast social publish --id {draft_id}`")
        return {"status": "approved", "draft_id": draft_id}

    async def _handle_reject(self, draft_id: str, callback_id: str, chat_id: str) -> dict[str, Any]:
        import json
        import time
        from pathlib import Path
        state_path = Path.home() / ".c4reqber" / "drafts" / draft_id / "draft_state.json"
        state = {"id": draft_id, "status": "rejected", "rejected_at": time.time(), "via": "telegram"}
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2))
        await self._send_message(f"❌ Rejected: {draft_id}")
        return {"status": "rejected", "draft_id": draft_id}

    async def _handle_edit_request(self, draft_id: str, callback_id: str, chat_id: str) -> dict[str, Any]:
        self._edit_sessions[chat_id] = {"draft_id": draft_id, "state": "awaiting_changes", "started_at": time.time()}
        await self._send_message(
            "📝 Describe the changes you want:\n\n"
            "Examples:\n"
            "• 'Shorten abstract to 150 words'\n"
            "• 'Change title to: New Title'\n"
            "• 'Add keyword: glymphatic system'\n"
            "• 'Remove section 3'\n\n"
            "Send your request as a reply."
        )
        return {"status": "awaiting_changes", "draft_id": draft_id}

    # ── LLM-Assisted Editing ───────────────────────────────────────

    async def process_edit_message(self, chat_id: str, message_text: str) -> str:
        """Receive a text message and apply LLM-assisted edits to a draft."""
        session = self._edit_sessions.get(chat_id)
        if not session:
            return "No active edit session. Start with 📝 Changes button."

        draft_id = session["draft_id"]
        draft_dir = Path.home() / ".c4reqber" / "drafts" / draft_id
        md_file = draft_dir / "dissertation.md"
        if not md_file.exists():
            del self._edit_sessions[chat_id]
            return f"Draft {draft_id} not found."

        content = md_file.read_text(encoding="utf-8")
        prompt = (
            f"You are editing a scientific preprint. Apply the following change request "
            f"to the document text. Return ONLY the full edited document.\n\n"
            f"CHANGE REQUEST: {message_text}\n\n"
            f"CURRENT DOCUMENT ({len(content)} chars):\n{content[:8000]}"
        )

        # Call LLM via ProviderRouter
        try:
            from src.llm.router import ProviderRouter
            router = ProviderRouter()
            response = await router.generate("proof_generation", prompt)
            new_content = getattr(response, "content", str(response)) if hasattr(response, "content") else str(response)

            md_file.write_text(new_content, encoding="utf-8")

            from src.social.i18n_templates import detect_language, format_post
            lang = detect_language()
            await self._send_message(
                format_post(lang, "review_request", title=draft_id, words=str(len(new_content.split()))) +
                f"\n\nChanges applied:\n_{message_text[:200]}_\n\n"
                "[✅ Approve] [📝 More Changes] [❌ Reject]"
            )
            return "Changes applied successfully."
        except Exception as e:
            return f"LLM edit failed: {e}"
