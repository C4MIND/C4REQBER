"""Async LLM Client.

Non-blocking multi-provider LLM interface.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

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
        "hypothesis": "anthropic/claude-3.5-sonnet",
        "falsifiability": "openai/gpt-4o",
        "synthesis": "anthropic/claude-3.5-sonnet",
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

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY", "")
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
        except Exception:
            pass

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
                last_error = e
                status = e.response.status_code
                await self.close()
                if attempt == max_retries - 1 or status in (400, 401, 402, 403, 404):
                    raise RuntimeError(f"LLM API error: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))
            except httpx.HTTPError as e:
                last_error = e
                await self.close()
                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM API error: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))
            except RuntimeError:
                raise
            except Exception as e:
                last_error = e
                await self.close()
                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM request failed: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))
        else:
            raise RuntimeError(f"LLM API error after {max_retries} retries: {last_error}") from last_error

        try:
            result = response.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM API returned invalid JSON: {e}") from e

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

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, (os.cpu_count() or 1) + 4)) as executor:
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
