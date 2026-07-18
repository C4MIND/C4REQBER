"""
Shared LLM-powered plugin base. Cognitive plugins use this for real reasoning.

Prefer the process LLM gateway (multi-provider) over a single HTTP key path.
When the LLM is unavailable, keep structured plugin output and mark
``llm_backed: False`` + ``status: partial`` — do not stub-empty the feature.
"""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


def _llm_reason(
    prompt: str,
    system: str = (
        "You are a rigorous analytical reasoning engine. Be specific, concrete, and evidence-based."
    ),
    max_tokens: int = 800,
    temperature: float = 0.4,
) -> str:
    """Call LLM for plugin reasoning via gateway, then direct HTTP fallback."""
    # 1) Canonical multi-provider gateway (finishes backends — free + paid chain)
    try:
        from src.llm.gateway import get_gateway

        text = get_gateway().generate_sync(
            prompt,
            system_prompt=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if isinstance(text, str) and text.strip():
            return text.strip()
    except Exception as e:
        logger.debug("Plugin gateway LLM unavailable: %s", e)

    # 2) Direct OpenRouter / DeepSeek if a key is present
    try:
        import os

        import httpx

        key = os.environ.get("OPENROUTER_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))
        if not key:
            logger.warning("Plugin LLM call skipped: no API key / gateway result")
            return ""
        try:
            from src.llm.model_assignment import get_model_for_phase

            model = (
                get_model_for_phase("D")
                or os.environ.get("C4_LLM_MODEL", "")
                or "openai/gpt-4o-mini"
            )
        except Exception:
            model = os.environ.get("C4_LLM_MODEL", "openai/gpt-4o-mini")
        if "/" not in model and not model.startswith("deepseek"):
            model = f"openai/{model}" if model.startswith("gpt-") else model
        url = (
            "https://openrouter.ai/api/v1/chat/completions"
            if key.startswith("sk-or-")
            or "OPENROUTER" in str(os.environ.get("OPENROUTER_API_KEY", ""))
            else "https://api.deepseek.com/v1/chat/completions"
        )
        if "deepseek.com" in url and "/" in model:
            model = "deepseek-chat" if "deepseek" not in model else model.split("/")[-1]
        resp = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://c4reqber.org",
                "X-Title": "C4Reqber Plugin",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        logger.warning("Plugin LLM unavailable: %s — keeping structured partial output", e)
        return ""


def plugin_fallback(reason: str) -> str:
    """Transparent note when LLM is unavailable (content still returned)."""
    return f"[LLM unavailable — continuing with structured output] {reason}"


def finalize_plugin_result(result: dict[str, Any], llm_raw: str) -> dict[str, Any]:
    """Attach positive LLM provenance without emptying the plugin payload.

    - LLM returned usable structured fields → ``llm_backed=True``, ``status=success``
    - LLM text but empty/unparsed structure → ``llm_backed=True``, ``status=partial``
    - LLM missing → ``llm_backed=False``, ``status=partial`` (payload kept)
    """
    out = dict(result)
    backed = bool(llm_raw and str(llm_raw).strip())
    out["llm_backed"] = backed
    if not backed:
        out["status"] = "partial"
        out.setdefault(
            "warnings",
            ["LLM unavailable for this plugin run; structured fields retained"],
        )
        return out

    if _structured_payload_empty(out):
        out["status"] = "partial"
        warnings = list(out.get("warnings") or [])
        warnings.append("LLM returned text but structured fields empty or unparsed")
        out["warnings"] = warnings
    else:
        out["status"] = "success"
    return out


def _structured_payload_empty(payload: dict[str, Any]) -> bool:
    """True when analysis fields are empty lists/dicts (meta keys ignored)."""
    skip = {
        "status",
        "llm_backed",
        "warnings",
        "note",
        "problem",
        "question",
        "situation",
        "challenge",
        "original",
        "executed",
        "total_combinations",
        "parameters",
        "values",
        "raw_excerpt",
    }
    for key, value in payload.items():
        if key in skip:
            continue
        if isinstance(value, list) and value:
            return False
        if isinstance(value, dict) and value:
            return False
        if isinstance(value, str) and value.strip():
            return False
        if isinstance(value, (int, float)) and key not in skip:
            return False
    return True
