"""LLMGateway — the single sanctioned entry point for LLM calls (P2-A).

This is the **equivalence-preserving facade** (REWORK_PLAN.md → P2-A track A1).
It does NOT change behavior: each method is a transparent pass-through to the
existing implementation, with the same signature and defaults, so callers
migrated onto the gateway behave byte-for-byte as before (proven by the
characterization tests in tests/llm/test_gateway_characterization.py).

The three call styles are kept distinct on purpose — they are genuinely
different (stage-routed vs prompt+params vs message-list), and unifying them or
applying cross-cutting concerns (guardian/cost/cache) to all of them is a
*behavior change* deferred to track A2.

  * generate_for_stage(...) → ProviderRouter (stage→PRESETS, retry, stats)
  * generate(...)           → AsyncLLMClient (DEFAULT_MODEL, response cache)
  * chat(...)               → LLMProviderRouter (guardian + provider fallback)
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMGateway(Protocol):
    """The single entry contract. Implementations delegate to provider strategies."""

    async def generate_for_stage(
        self,
        stage: str,
        prompt: str,
        system_prompt: str | None = None,
        use_retry: bool = True,
    ) -> Any: ...

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> Any: ...

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str: ...

    async def chat_json(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> dict[str, Any]: ...


class DefaultGateway:
    """Default LLMGateway: a transparent facade over the existing strategies.

    Strategies are constructed lazily and reused. They can be injected (tests,
    or a caller that needs a specific ProviderRouter preset — e.g. the solve
    pipeline uses ProviderPreset.C4REQBER): pass the pre-built router/client in.
    """

    def __init__(self, *, provider_router: Any = None, async_client: Any = None) -> None:
        self._provider_router = provider_router
        self._async_client = async_client

    def _router(self) -> Any:
        if self._provider_router is None:
            from src.llm.router import ProviderRouter

            self._provider_router = ProviderRouter()
        return self._provider_router

    def _client(self) -> Any:
        if self._async_client is None:
            from src.llm.async_client import AsyncLLMClient

            self._async_client = AsyncLLMClient()
        return self._async_client

    async def generate_for_stage(
        self,
        stage: str,
        prompt: str,
        system_prompt: str | None = None,
        use_retry: bool = True,
    ) -> Any:
        return await self._router().generate(
            stage, prompt, system_prompt=system_prompt, use_retry=use_retry
        )

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> Any:
        return await self._client().generate(
            prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            response_format=response_format,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        from src.llm.providers.unified import LLMProviderRouter

        return await LLMProviderRouter.chat(
            messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

    async def chat_json(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> dict[str, Any]:
        from src.llm.providers.unified import LLMProviderRouter

        return await LLMProviderRouter.chat_json(
            messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def close(self) -> None:
        """Best-effort cleanup of any constructed strategies."""
        if self._provider_router is not None and hasattr(self._provider_router, "close_all"):
            await self._provider_router.close_all()
        if self._async_client is not None and hasattr(self._async_client, "close"):
            await self._async_client.close()


_default_gateway: DefaultGateway | None = None


def get_gateway() -> DefaultGateway:
    """Process-wide default gateway singleton (lazy)."""
    global _default_gateway
    if _default_gateway is None:
        _default_gateway = DefaultGateway()
    return _default_gateway
