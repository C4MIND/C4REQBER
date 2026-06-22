"""LLM guarded call wrapper — adds observability + safety to raw httpx calls.

Audit 2026-06-22 H-8 (Tier 1 of P2-A): existing 12 raw /chat/completions
sites use httpx.AsyncClient directly, bypassing the LLMGateway facade and
all its cross-cutting concerns (guardian scan, cost tracking, metrics).
The full gateway migration (REWORK_PLAN P2-A track A2) requires an
owner decision on stage→model reconciliation.

In the meantime, this module provides `guarded_chat_completion()` —
a drop-in helper that wraps a raw httpx POST and adds:

  1. Prompt injection scan (via src.security.prompt_sanitizer)
  2. Cost tracking (via src.llm.cost_tracker)
  3. Prometheus metrics (via src.api.routers.metrics)
  4. Credential redaction on errors

Existing sites can adopt this incrementally — replace the httpx.AsyncClient
post block with one call. Sites that remain on raw httpx are still
functional, just without observability/safety.

Usage:
    from src.llm.guarded_call import guarded_chat_completion

    result = await guarded_chat_completion(
        url="https://openrouter.ai/api/v1/chat/completions",
        api_key=or_key,
        model="anthropic/claude-3.5-sonnet",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx


logger = logging.getLogger(__name__)


# Best-effort imports; observability must not crash callers.
def _try_import_sanitizer():
    try:
        from src.security.prompt_sanitizer import SanitizerInput
        return SanitizerInput
    except Exception:
        return None


def _try_import_cost_tracker():
    try:
        from src.llm.cost_tracker import CostTracker, _normalize_model
        return CostTracker, _normalize_model
    except Exception:
        return None, None


def _try_import_metrics():
    try:
        from src.api.routers.metrics import LLM_CALLS, LLM_LATENCY
        return LLM_CALLS, LLM_LATENCY
    except Exception:
        return None, None


def _scan_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize each message's content. Returns sanitized list (or unchanged on import failure)."""
    SanitizerInput = _try_import_sanitizer()
    if SanitizerInput is None:
        return messages
    out = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            try:
                content = SanitizerInput.sanitize_text(content)
            except Exception as exc:
                logger.debug("sanitizer failed: %s", exc)
        out.append({**msg, "content": content})
    return out


def _record_metrics(provider: str, model: str, status: str, duration: float) -> None:
    LLM_CALLS, LLM_LATENCY = _try_import_metrics()
    if LLM_CALLS is None:
        return
    try:
        LLM_CALLS.labels(provider=provider, model=model or "unknown", status=status).inc()
        LLM_LATENCY.labels(provider=provider, model=model or "unknown").observe(duration)
    except Exception as exc:
        logger.debug("metrics increment failed: %s", exc)


def _record_cost(model: str, input_tokens: int, output_tokens: int) -> None:
    CostTracker, normalize = _try_import_cost_tracker()
    if CostTracker is None:
        return
    try:
        price_key = normalize(model)
        from src.llm.cost_tracker import CostEntry, COST_TABLE  # noqa: F401
        cost = 0.0
        if price_key in COST_TABLE:
            input_rate, output_rate = COST_TABLE[price_key]
            cost = (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
        CostTracker.add(CostEntry(
            provider="guarded",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=0.0,
            cost_usd=cost,
        ))
    except Exception as exc:
        logger.debug("cost tracking failed: %s", exc)


def _provider_from_url(url: str) -> str:
    if "openrouter" in url:
        return "openrouter"
    if "anthropic" in url:
        return "anthropic"
    if "openai" in url:
        return "openai"
    if "deepseek" in url:
        return "deepseek"
    if "localhost" in url or "127.0.0.1" in url:
        return "local"
    return "unknown"


async def guarded_chat_completion(
    *,
    url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.3,
    max_tokens: int = 800,
    timeout: float = 60.0,
    extra_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap a raw /chat/completions POST with observability + safety.

    Returns the JSON response on success. Raises httpx.HTTPError on transport
    failure (caller handles as before).
    """
    provider = _provider_from_url(url)
    sanitized = _scan_messages(messages)
    payload: dict[str, Any] = {
        "model": model,
        "messages": sanitized,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_body:
        payload.update(extra_body)

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            _record_metrics(provider, model, "success", time.monotonic() - t0)
            # Record cost if usage block present
            usage = data.get("usage") or {}
            in_tok = int(usage.get("prompt_tokens", 0) or 0)
            out_tok = int(usage.get("completion_tokens", 0) or 0)
            if in_tok or out_tok:
                _record_cost(model, in_tok, out_tok)
            return data
    except httpx.HTTPError as exc:
        _record_metrics(provider, model, "error", time.monotonic() - t0)
        # Redact credentials before logging
        from src.security.credential_guard import redact_credentials
        logger.warning(
            "guarded_chat_completion failed for provider=%s model=%s: %s",
            redact_credentials(provider),
            redact_credentials(model),
            redact_credentials(str(exc)),
        )
        raise


def guarded_chat_completion_sync(
    *,
    url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.3,
    max_tokens: int = 800,
    timeout: float = 20.0,
    extra_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Synchronous variant for non-async call sites (e.g. embeddings).

    Same contract as guarded_chat_completion but uses httpx.Client.
    """
    provider = _provider_from_url(url)
    sanitized = _scan_messages(messages)
    payload: dict[str, Any] = {
        "model": model,
        "messages": sanitized,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_body:
        payload.update(extra_body)

    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            _record_metrics(provider, model, "success", time.monotonic() - t0)
            usage = data.get("usage") or {}
            in_tok = int(usage.get("prompt_tokens", 0) or 0)
            out_tok = int(usage.get("completion_tokens", 0) or 0)
            if in_tok or out_tok:
                _record_cost(model, in_tok, out_tok)
            return data
    except httpx.HTTPError as exc:
        _record_metrics(provider, model, "error", time.monotonic() - t0)
        from src.security.credential_guard import redact_credentials
        logger.warning(
            "guarded_chat_completion_sync failed for provider=%s model=%s: %s",
            redact_credentials(provider),
            redact_credentials(model),
            redact_credentials(str(exc)),
        )
        raise