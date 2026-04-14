"""
TURBO-CDI: Async LLM Client
Non-blocking multi-provider LLM interface

Uses httpx for async HTTP requests.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio

# Try to import httpx for async support
try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    print("⚠️  httpx not installed. Async LLM client unavailable.")


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: Dict[str, int]
    latency_ms: float = 0.0
    raw_response: Optional[Dict] = None


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

    def __init__(self, api_key: Optional[str] = None, timeout: float = 60.0):
        if not HAS_HTTPX:
            raise ImportError(
                "httpx required for async LLM client. Install: pip install httpx"
            )

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.referer = "https://turbo-cdi.org"
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _init_client(self):
        """Initialize httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self.referer,
                    "X-Title": "TURBO-CDI",
                },
            )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        response_format: Optional[str] = None,
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
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. "
                "Set OPENROUTER_API_KEY environment variable."
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

        start_time = time.time()

        try:
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=data,
            )
            response.raise_for_status()

            result = response.json()
            latency_ms = (time.time() - start_time) * 1000

            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model=result.get("model", model),
                usage=result.get("usage", {}),
                latency_ms=latency_ms,
                raw_response=result,
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"LLM API error: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())

    async def generate_batch(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_concurrent: int = 5,
    ) -> List[LLMResponse]:
        """
        Generate multiple responses concurrently.

        Args:
            prompts: List of prompts
            model: Model to use
            temperature: Temperature setting
            max_tokens: Max tokens per response
            max_concurrent: Max concurrent requests

        Returns:
            List of responses (same order as prompts)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_limit(prompt: str) -> LLMResponse:
            async with semaphore:
                return await self.generate(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

        tasks = [generate_with_limit(p) for p in prompts]
        return await asyncio.gather(*tasks)

    async def test_connection(self) -> bool:
        """Test API connectivity."""
        try:
            response = await self.generate(
                prompt="Respond with 'TURBO-CDI connected'",
                max_tokens=10,
                temperature=0,
            )
            return "TURBO-CDI" in response.content
        except Exception:
            return False


class AsyncMockLLMClient(AsyncLLMClient):
    """Mock async client for testing without API calls."""

    def __init__(self):
        self.api_key = "mock"
        self.timeout = 30.0
        self.base_url = "https://mock.turbo-cdi.org"
        self.referer = "https://turbo-cdi.org"
        self._client = None

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Simulate network delay
        await asyncio.sleep(0.01)
        return LLMResponse(
            content=f"[MOCK] Generated hypothesis for: {prompt[:50]}...",
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            latency_ms=10.0,
        )

    async def generate_structured(self, prompt: str, schema: Dict, **kwargs) -> Dict:
        await asyncio.sleep(0.01)
        result = {}
        for key, value in schema.get("properties", {}).items():
            if value.get("type") == "array":
                result[key] = [f"mock_{key}_item"]
            elif value.get("type") == "string":
                result[key] = f"mock_{key}"
            elif value.get("type") == "number":
                result[key] = 0.5
        return result

    async def close(self):
        pass


# ═══════════════════════════════════════════════════════════════════
# SYNC-TO-ASYNC BRIDGE
# ═══════════════════════════════════════════════════════════════════


def run_async(coro):
    """Run an async coroutine from sync code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a new loop
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No loop running, create one
        return asyncio.run(coro)


# Convenience function for simple async generation
async def async_generate(
    prompt: str, model: Optional[str] = None, api_key: Optional[str] = None, **kwargs
) -> LLMResponse:
    """
    One-shot async generation.

    Usage:
        response = await async_generate("Your prompt here")
    """
    async with AsyncLLMClient(api_key=api_key) as client:
        return await client.generate(prompt, model=model, **kwargs)
