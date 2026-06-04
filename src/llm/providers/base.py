"""Base LLM client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.llm.config import LLMProvider, get_base_url


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
