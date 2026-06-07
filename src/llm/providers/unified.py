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
    """Unified LLM router. Priority: DeepSeek → OpenRouter → LM Studio (local)."""

    DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL = "deepseek-v4-flash"

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_MODEL = "deepseek/deepseek-chat"

    LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"

    PROVIDER_ORDER = ["deepseek", "openrouter", "lmstudio"]

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
    async def chat(messages, system_prompt="", temperature=0.3, max_tokens=800, json_mode=False) -> str:
        """Chat."""
        messages = LLMProviderRouter._guard_messages(messages)
        attempted_providers: list[str] = []
        provider_errors: list[str] = []
        for provider in LLMProviderRouter.PROVIDER_ORDER:
            attempted_providers.append(provider)
            try:
                method = getattr(LLMProviderRouter, f"_try_{provider}")
                result = await method(messages, system_prompt, temperature, max_tokens, json_mode)
                if result:
                    logger.info("LLM provider '%s' responded successfully", provider)
                    return result
            except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
                logger.debug("%s failed: %s", provider, e)
                provider_errors.append(f"{provider}: {e}")
        raise ProviderExhaustedError(attempted_providers, provider_errors)

    @staticmethod
    async def _chat_safe(messages, system_prompt="", temperature=0.3, max_tokens=800, json_mode=False) -> str | None:
        return await LLMProviderRouter.chat(messages, system_prompt, temperature, max_tokens, json_mode)

    @staticmethod
    async def chat_json(messages, system_prompt="", temperature=0.3, max_tokens=800) -> dict[str, Any]:
        """Chat json."""
        text = await LLMProviderRouter.chat(messages, system_prompt, temperature, max_tokens, json_mode=True)
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

    @staticmethod
    async def _try_deepseek(messages, system_prompt, temperature, max_tokens, json_mode) -> str:
        key = LLMProviderRouter._get_key("DEEPSEEK_API_KEY")
        if not key:
            return ""
        full_msgs = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_msgs.extend(messages)
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, LLMProviderRouter._call_openai_sync,
            LLMProviderRouter.DEEPSEEK_URL, key, LLMProviderRouter.DEEPSEEK_MODEL,
            full_msgs, temperature, max_tokens, extra, 30
        )

    @staticmethod
    async def _try_openrouter(messages, system_prompt, temperature, max_tokens, json_mode) -> str:
        key = LLMProviderRouter._get_key("OPENROUTER_API_KEY")
        if not key:
            return ""
        full_msgs = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_msgs.extend(messages)
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, LLMProviderRouter._call_openai_sync,
            LLMProviderRouter.OPENROUTER_URL, key, LLMProviderRouter.OPENROUTER_MODEL,
            full_msgs, temperature, max_tokens, extra, 30
        )

    @staticmethod
    async def _try_lmstudio(messages, system_prompt, temperature, max_tokens, json_mode) -> str:
        full_msgs = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_msgs.extend(messages)
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, LLMProviderRouter._call_openai_sync,
            LLMProviderRouter.LMSTUDIO_URL, "lm-studio", "",
            full_msgs, temperature, max_tokens, extra, 30
        )

    @staticmethod
    def _call_openai_sync(url, key, model, messages, temperature, max_tokens, extra, timeout) -> str:
        headers = {"Content-Type": "application/json"}
        if key and key != "lm-studio":
            headers["Authorization"] = f"Bearer {key}"
        payload: dict[str, Any] = {
            "model": model or "", "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens, **extra
        }
        try:
            session = _get_session()
            r = session.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code != 200:
                logger.warning("%s HTTP %d: %s", url[:40], r.status_code, r.text[:150])
                return ""
            data = r.json()
            if "choices" not in data or not data["choices"]:
                return ""
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, httpx.TimeoutException, json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning("%s error: %s — %s", url[:40], type(e).__name__, e)
            return ""
        except Exception as e:
            logger.exception("%s unexpected error: %s", url[:40], e)
            return ""


__all__ = ["LLMProviderRouter", "_get_session", "_close_session"]
