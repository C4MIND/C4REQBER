from __future__ import annotations

import asyncio
import atexit
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx


logger = logging.getLogger(__name__)

_SESSION: httpx.Client | None = None


def _get_session() -> httpx.Client:
    global _SESSION
    if _SESSION is None:
        _SESSION = httpx.Client(
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            timeout=httpx.Timeout(30),
        )
    return _SESSION


def _close_session() -> None:
    global _SESSION
    if _SESSION is not None:
        _SESSION.close()
        _SESSION = None


atexit.register(_close_session)


class ProviderExhaustedError(RuntimeError):
    """Raised when all LLM providers have been exhausted."""

    def __init__(self, attempted: list[str], errors: list[str] | None = None) -> None:
        self.attempted = attempted
        self.errors = errors or []
        detail = "; ".join(self.errors[:3]) if self.errors else "no details available"
        super().__init__(f"All LLM providers failed after trying: {attempted}. Errors: {detail}")


class LLMProviderRouter:
    """Unified LLM router (internal strategy). Prefer ``src.llm.get_gateway().chat``.

    Free-first: OpenCode Zen → Groq → NIM → LM Studio → OR.
    """

    @staticmethod
    def _preferred_model() -> str:
        env = os.environ.get("C4_LLM_MODEL", "").strip()
        if env:
            return env
        try:
            from src.llm.model_assignment import get_model_for_phase

            assigned = get_model_for_phase("F") or get_model_for_phase("D")
            if assigned:
                return assigned
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)
        return "deepseek-v4-flash-free"

    PROVIDER_ORDER = ["opencode", "groq", "nvidia", "lmstudio", "openrouter", "deepseek"]
    if os.getenv("C4_LOCAL_LLM_FIRST", "").lower() in ("1", "true", "yes"):
        PROVIDER_ORDER = ["lmstudio", "opencode", "groq", "nvidia", "openrouter", "deepseek"]

    @staticmethod
    def _get_key(name: str) -> str:
        key = os.getenv(name, "")
        if key and not key.startswith("YOUR_") and not key.startswith("sk-YOUR"):
            return key
        try:
            env_path = Path(__file__).parent.parent.parent.parent / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    line = line.strip()
                    if line.startswith(f"{name}="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("YOUR_") and not val.startswith("sk-YOUR"):
                            return val
        except (OSError, ValueError):
            pass
        return ""

    @staticmethod
    async def chat(
        messages, system_prompt="", temperature=0.3, max_tokens=800, json_mode=False
    ) -> str:
        """Chat via free-first provider chain (sync_provider_chain)."""
        messages = LLMProviderRouter._guard_messages(messages)
        prompt_parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            if role == "system" and not system_prompt:
                system_prompt = content
            elif role == "user":
                prompt_parts.append(content)
            elif role == "assistant":
                prompt_parts.append(f"[assistant]: {content}")
        prompt = "\n".join(prompt_parts) if prompt_parts else str(messages)
        preferred = LLMProviderRouter._preferred_model()
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None,
                lambda: __import__(
                    "src.llm.sync_provider_chain", fromlist=["generate_with_fallback"]
                ).generate_with_fallback(
                    prompt,
                    system_prompt=system_prompt or None,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    preferred_model=preferred,
                ),
            )
        except RuntimeError as e:
            raise ProviderExhaustedError(
                ["opencode", "groq", "nvidia", "lmstudio"], [str(e)]
            ) from e

    @staticmethod
    async def _chat_safe(
        messages, system_prompt="", temperature=0.3, max_tokens=800, json_mode=False
    ) -> str | None:
        return await LLMProviderRouter.chat(
            messages, system_prompt, temperature, max_tokens, json_mode
        )

    @staticmethod
    async def chat_json(
        messages, system_prompt="", temperature=0.3, max_tokens=800
    ) -> dict[str, Any]:
        """Chat json."""
        text = await LLMProviderRouter.chat(
            messages, system_prompt, temperature, max_tokens, json_mode=True
        )
        if not text:
            raise RuntimeError("LLM returned empty response")
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"raw": text[:500]}

    @staticmethod
    def _guard_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            from src.security.guardian import Guardian

            guardian = Guardian()
            cleaned: list[dict[str, Any]] = []
            for msg in messages:
                content = msg.get("content", "")
                if not isinstance(content, str):
                    cleaned.append(msg)
                    continue
                scan = guardian.full_scan(content)
                if not scan.clean and scan.severity in {"high", "critical"}:
                    raise RuntimeError("Prompt rejected by guardian")
                cleaned.append(msg)
            return cleaned
        except RuntimeError:
            raise
        except Exception as e:
            logger.exception("Guardian scan failed — blocking request for safety")
            raise RuntimeError(f"Guardian scan unavailable: {e}") from e


__all__ = ["LLMProviderRouter", "_get_session", "_close_session"]
