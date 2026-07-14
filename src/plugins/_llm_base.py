"""
Shared LLM-powered plugin base. All cognitive plugins use this for real reasoning.
"""
from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def _llm_reason(prompt: str, system: str = "You are a rigorous analytical reasoning engine. Be specific, concrete, and evidence-based.", max_tokens: int = 800, temperature: float = 0.4) -> str:
    """Call LLM for plugin reasoning. Graceful fallback if unavailable."""
    try:
        import os

        import httpx
        key = os.environ.get("OPENROUTER_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))
        if not key:
            logger.warning("Plugin LLM call skipped: no API key configured")
            return ""
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber Plugin"},
            json={"model": "openai/gpt-4o-mini", "max_tokens": max_tokens, "temperature": temperature, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Plugin LLM unavailable: %s — using fallback reasoning", e)
        return ""


def plugin_fallback(reason: str) -> str:
    """Transparent fallback marker when LLM is unavailable."""
    return f"[LLM unavailable — heuristic reasoning] {reason}"
