"""Async LLM Client.

Non-blocking multi-provider LLM interface.
"""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from src.config import get_key
from src.llm.cache import AsyncLLMCache, hash_prompt


# Try to import httpx for async support
try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore
    print("⚠️  httpx not installed. Async LLM client unavailable.")


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: dict[str, int]
    latency_ms: float = 0.0
    raw_response: dict | None = None  # type: ignore[type-arg]


class AsyncLLMClient:
    """
    Async LLM client for non-blocking API calls.

    Supports concurrent requests for batch processing.
    """

    DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct"

    # Models optimized for different tasks
    MODELS = {
        "hypothesis": "anthropic/claude-sonnet-4.6",
        "falsifiability": "openai/gpt-4o",
        "synthesis": "anthropic/claude-sonnet-4.6",
        "cheap": "openai/gpt-4o-mini",
    }

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 60.0,
        cache: AsyncLLMCache | None = None,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required for async LLM client. Install: pip install httpx")

        # Prefer central ~/.c4reqber (get_key) + env override
        self.api_key = api_key or get_key("openrouter") or os.getenv("OPENAI_API_KEY", "")
        custom_base = os.getenv("OPENAI_BASE_URL", "")
        self.base_url = custom_base if custom_base else "https://openrouter.ai/api/v1"
        self.referer = "https://c4reqber.org"
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._cache = cache or AsyncLLMCache()

    async def __aenter__(self) -> Any:
        """Async context manager entry."""
        await self._init_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _init_client(self) -> None:
        """Initialize or reset httpx client."""
        await self.close()
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.referer,
                "X-Title": "C4Reqber",
            },
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _record_metric(self, model: str, status: str, duration: float) -> None:
        """Audit 2026-06-22 H-8 Tier 1: best-effort Prometheus increment.

        AsyncLLMClient is itself a router (used by LLMGateway facade), so
        we instrument at this layer rather than the per-call layer.
        """
        try:
            from src.api.routers.metrics import LLM_CALLS, LLM_LATENCY

            LLM_CALLS.labels(provider="async_client", model=model or "unknown", status=status).inc()
            LLM_LATENCY.labels(provider="async_client", model=model or "unknown").observe(duration)
        except Exception as _exc:
            logger.debug("metrics increment failed: %s", _exc)

    def _record_cost(self, model: str, input_tokens: int, output_tokens: int) -> None:
        try:
            from src.llm.cost_tracker import (
                COST_TABLE,
                CostEntry,
                CostTracker,
                _normalize_model,
            )

            price_key = _normalize_model(model)
            if price_key not in COST_TABLE:
                return
            rates = COST_TABLE[price_key]
            cost = (input_tokens / 1_000_000) * rates["input"] + (
                output_tokens / 1_000_000
            ) * rates["output"]
            CostTracker.add(
                CostEntry(
                    provider="async_client",
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=0.0,
                    cost_usd=cost,
                )
            )
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        """
        Generate text using LLM (async).

        Args:
            prompt: User prompt
            model: Model identifier
            temperature: 0-1 (0=deterministic, 1=creative)
            max_tokens: Maximum response length
            system_prompt: System instructions
            response_format: "json" or None

        Returns:
            LLMResponse with content and metadata
        """
        # ── Guardrail: prompt injection scan ──────────────────────────
        try:
            from src.security.guardian import Guardian

            guardian = Guardian()
            scan = guardian.full_scan(prompt, code=None)
            if system_prompt:
                scan_sys = guardian.full_scan(system_prompt, code=None)
                if scan_sys.severity in {"high", "critical"}:
                    raise RuntimeError("System prompt rejected by guardian")
            if scan.severity in {"high", "critical"}:
                raise RuntimeError("Prompt rejected by guardian")
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError("Prompt safety scan failed; refusing to call the LLM") from exc

        # ── Cache check ───────────────────────────────────────────────
        prompt_hash = hash_prompt(prompt + (system_prompt or "") + (model or self.DEFAULT_MODEL))
        cached = await self._cache.get(prompt_hash)
        if cached is not None:
            return LLMResponse(
                content=cached,
                model=model or self.DEFAULT_MODEL,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "cached": True},
                latency_ms=0.0,
            )

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable."
            )

        await self._init_client()

        model = model or self.DEFAULT_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            data["response_format"] = {"type": "json_object"}

        import time

        max_retries = 2
        last_error: Exception | None = None

        for attempt in range(max_retries):
            start_time = time.time()
            await self._init_client()

            try:
                response = await self._client.post(  # type: ignore[union-attr]
                    f"{self.base_url}/chat/completions",
                    json=data,
                )
                response.raise_for_status()
                break  # success — exit retry loop
            except httpx.HTTPStatusError as e:
                # Audit 2026-06-22 H-8 Tier 1: record retry error metric
                self._record_metric(model, "error_retry", time.time() - start_time)
                last_error = e
                status = e.response.status_code
                last_error = e
                status = e.response.status_code
                await self.close()
                if attempt == max_retries - 1 or status in (400, 401, 402, 403, 404):
                    raise RuntimeError(f"LLM API error: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))
            except httpx.HTTPError as e:
                self._record_metric(model, "error_retry", time.time() - start_time)
                last_error = e
                await self.close()
                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM API error: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))
            except RuntimeError:
                raise
            except Exception as e:
                self._record_metric(model, "error_retry", time.time() - start_time)
                last_error = e
                await self.close()
                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM request failed: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))
        else:
            raise RuntimeError(
                f"LLM API error after {max_retries} retries: {last_error}"
            ) from last_error

        # Audit 2026-06-22 H-8 Tier 1: instrument at this layer (the
        # router itself). The actual httpx call has already happened
        # inside the retry loop above.
        model_name = str(data.get("model", model))
        self._record_metric(model_name, "success", time.time() - start_time)

        try:
            result = response.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM API returned invalid JSON: {e}") from e

        # Cost tracking (audit H-8 Tier 1)
        usage = result.get("usage") or {}
        in_tok = int(usage.get("prompt_tokens", 0) or 0)
        out_tok = int(usage.get("completion_tokens", 0) or 0)
        if in_tok or out_tok:
            self._record_cost(model_name, in_tok, out_tok)

        latency_ms = (time.time() - start_time) * 1000

        choices = result.get("choices")
        if not choices or not isinstance(choices, list):
            raise RuntimeError(f"LLM API returned no choices: {result.get('error', result)}")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "") or message.get("reasoning_content", "")
        if not content:
            raise RuntimeError(f"LLM API returned empty content: {result.get('error', result)}")

        # ── Cache save ──────────────────────────────────────────
        await self._cache.set(prompt_hash, content)

        return LLMResponse(
            content=content,
            model=result.get("model", model),
            usage=result.get("usage", {}),
            latency_ms=latency_ms,
            raw_response=result,
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured JSON response (async).

        Args:
            prompt: User prompt
            schema: JSON schema for validation
            model: Model identifier

        Returns:
            Parsed JSON object
        """
        system_prompt = f"""You must respond with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with JSON, no markdown formatting, no explanations."""

        response = await self.generate(
            prompt=prompt,
            model=model or self.MODELS["falsifiability"],
            system_prompt=system_prompt,
            temperature=0.3,
            response_format="json",
        )

        try:
            return json.loads(response.content)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())  # type: ignore[no-any-return]

    async def generate_batch(
        self,
        prompts: list[str],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_concurrent: int = 5,
    ) -> list[LLMResponse]:
        """
        Generate multiple responses concurrently.
        Individual failures return error responses instead of failing the entire batch.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_limit(prompt: str) -> LLMResponse:
            async with semaphore:
                try:
                    return await self.generate(
                        prompt=prompt,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except (ConnectionError, TimeoutError, RuntimeError) as e:
                    return LLMResponse(
                        content=f"Batch error: {str(e)[:120]}",
                        model=model or "error",
                        usage={"prompt_tokens": 0, "completion_tokens": 0},
                        latency_ms=0.0,
                    )

        tasks = [generate_with_limit(p) for p in prompts]
        return await asyncio.gather(*tasks)

    async def test_connection(self) -> bool:
        """Test API connectivity."""
        try:
            response = await self.generate(
                prompt="Respond with 'C4Reqber connected'",
                max_tokens=10,
                temperature=0,
            )
            return "C4Reqber" in response.content
        except (ConnectionError, TimeoutError, RuntimeError):
            return False


# ═══════════════════════════════════════════════════════════════════
# SYNC-TO-ASYNC BRIDGE
# ═══════════════════════════════════════════════════════════════════


def run_async(coro: Any) -> Any:
    """Run an async coroutine from sync code.

    Safe for nested calls: detects running loop and uses run_coroutine_threadsafe.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop running — safe to use asyncio.run
        return asyncio.run(coro)

    if loop.is_running():
        # Already inside an async context — schedule and wait
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(32, (os.cpu_count() or 1) + 4)
        ) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    return loop.run_until_complete(coro)


# Convenience function for simple async generation
async def async_generate(
    prompt: str, model: str | None = None, api_key: str | None = None, **kwargs: Any
) -> LLMResponse:
    """
    One-shot async generation.

    Usage:
        response = await async_generate("Your prompt here")
    """
    async with AsyncLLMClient(api_key=api_key) as client:
        return await client.generate(prompt, model=model, **kwargs)  # type: ignore[no-any-return]
