"""Base LLM client."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from src.llm.config import LLMProvider, get_base_url


logger = logging.getLogger(__name__)


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: dict[str, int]
    latency_ms: float = 0.0
    provider: str = "unknown"
    raw_response: dict | None = None  # type: ignore[type-arg]


class BaseLLMClient:
    """Base class for all LLM clients."""

    def __init__(self, provider: LLMProvider, api_key: str | None = None, timeout: float = 60.0) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install: pip install httpx")
        self.provider = provider
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = get_base_url(provider)
        self._client: httpx.AsyncClient | None = None

    async def _init_client(self) -> None:
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            # Provider-specific headers
            if self.provider == LLMProvider.OPENROUTER:
                headers["HTTP-Referer"] = "https://c4reqber.org"
                headers["X-Title"] = "C4Reqber"
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
                verify=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
            )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        raise NotImplementedError

    async def generate_batch(
        self,
        prompts: list[str],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> list[LLMResponse]:
        return [
            await self.generate(
                prompt=p,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            for p in prompts
        ]

    def _build_messages(self, prompt: str, system_prompt: str | None = None) -> list[dict]:  # type: ignore[type-arg]
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def guarded_post(
        self,
        url: str,
        json_body: dict[str, Any],
        model_name: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Wrapper around self._client.post with Prometheus metrics + cost tracking.

        Audit 2026-06-22 H-8 Tier 1: every BaseLLMClient subclass should call
        this instead of self._client.post() directly. Gives consistent
        observability across all 6 provider implementations.
        """
        await self._init_client()
        if self._client is None:
            raise RuntimeError("HTTP client not initialized")
        t0 = time.monotonic()
        try:
            response = await self._client.post(
                url,
                json=json_body,
                timeout=httpx.Timeout(timeout or self.timeout),
            )
            response.raise_for_status()
            data = response.json()
            # Metrics + cost tracking
            self._record_metric(model_name, "success", time.monotonic() - t0)
            usage = data.get("usage") or {}
            in_tok = int(usage.get("prompt_tokens", 0) or 0)
            out_tok = int(usage.get("completion_tokens", 0) or 0)
            if in_tok or out_tok:
                self._record_cost(model_name, in_tok, out_tok)
            return data
        except Exception as exc:
            self._record_metric(model_name, "error", time.monotonic() - t0)
            from src.security.credential_guard import redact_credentials
            logger.warning(
                "%s call failed for model=%s: %s",
                self.provider.value,
                redact_credentials(model_name),
                redact_credentials(str(exc)),
            )
            raise

    def _record_metric(self, model: str, status: str, duration: float) -> None:
        """Best-effort Prometheus increment. Never raises."""
        try:
            from src.api.routers.metrics import LLM_CALLS, LLM_LATENCY
            LLM_CALLS.labels(
                provider=self.provider.value, model=model or "unknown", status=status
            ).inc()
            LLM_LATENCY.labels(
                provider=self.provider.value, model=model or "unknown"
            ).observe(duration)
        except Exception as exc:
            logger.debug("metrics increment failed: %s", exc)

    def _record_cost(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Best-effort cost tracking. Never raises."""
        try:
            from src.llm.cost_tracker import COST_TABLE, CostEntry, _normalize_model
            price_key = _normalize_model(model)
            if price_key not in COST_TABLE:
                return
            rates = COST_TABLE[price_key]
            cost = (input_tokens / 1_000_000) * rates["input"] + (output_tokens / 1_000_000) * rates["output"]
            from src.llm.cost_tracker import CostTracker
            CostTracker.add(CostEntry(
                provider=self.provider.value,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=0.0,
                cost_usd=cost,
            ))
        except Exception as exc:
            logger.debug("cost tracking failed: %s", exc)

    def _parse_openai_response(self, result: dict[str, Any], model: str, latency_ms: float) -> LLMResponse:
        """Parse standard OpenAI-compatible response."""
        choices = result.get("choices")
        if not choices or not isinstance(choices, list):
            raise RuntimeError(f"LLM API returned no choices: {result.get('error', result)}")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "")
        if not content:
            raise RuntimeError(f"LLM API returned empty content: {result.get('error', result)}")

        return LLMResponse(
            content=content,
            model=result.get("model", model),
            usage=result.get("usage", {}),
            latency_ms=latency_ms,
            provider=self.provider.value,
            raw_response=result,
        )
