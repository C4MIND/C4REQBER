"""Local LLM Client — Unified client with remote routing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.llm.local.client import LocalLLMClient
from src.llm.local.core import LocalProvider


@dataclass
class UnifiedResponse:
    """Normalized LLM response regardless of provider."""

    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0


class UnifiedLLMClient:
    """Unified client for remote and local LLMs."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 60.0,
        prefer_local: bool = False,
        local_provider: str | None = None,
    ) -> None:
        from src.llm.async_client import AsyncLLMClient

        self.prefer_local = prefer_local
        self.remote = AsyncLLMClient(api_key=api_key, timeout=timeout)
        self.local = LocalLLMClient(timeout=timeout)

        if local_provider:
            self.local.preferred_provider = LocalProvider(local_provider)

    def _normalize(self, response: Any, provider: str) -> UnifiedResponse:
        """Normalize any provider response to UnifiedResponse."""
        if isinstance(response, UnifiedResponse):
            return response
        if hasattr(response, "content"):
            return UnifiedResponse(
                content=response.content,
                model=getattr(response, "model", "unknown"),
                provider=provider,
                usage=getattr(response, "usage", {}),
                latency_ms=getattr(response, "latency_ms", 0.0),
            )
        # Normalize dict-like responses
        return UnifiedResponse(
            content=str(response),
            model="unknown",
            provider=provider,
        )

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> UnifiedResponse:
        """Generate with provider routing."""

        if self.prefer_local:
            resp = await self.local.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            return self._normalize(resp, "local")

        resp = await self.remote.generate(  # type: ignore[assignment]
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )
        return self._normalize(resp, "remote")

    async def generate_batch(
        self, prompts: list[str], **kwargs: Any
    ) -> list[UnifiedResponse]:
        """Batch generate with provider routing."""
        if self.prefer_local:
            responses = await self.local.generate_batch(prompts, **kwargs)
            return [self._normalize(r, "local") for r in responses]

        responses = await self.remote.generate_batch(prompts, **kwargs)  # type: ignore[assignment]
        return [self._normalize(r, "remote") for r in responses]

    async def close(self) -> None:
        """Close."""
        await self.remote.close()
        await self.local.close()

    async def health_check(self) -> dict[str, Any]:
        """Check all providers."""
        remote_ok = False
        try:
            remote_ok = await self.remote.test_connection()
        except (ConnectionError, OSError, RuntimeError):
            pass

        local_status = await self.local.health_check()

        return {
            "remote": {"available": remote_ok, "provider": "openrouter"},
            "local": local_status,
            "prefer_local": self.prefer_local,
        }
