"""LLMGateway — the single sanctioned entry point for LLM calls.

Preferred entry::

    from src.llm import get_gateway
    text = await get_gateway().chat([...])
    text = get_gateway().generate_sync(prompt)

Internal strategies (do not import in new code):
  * generate_for_stage → ProviderRouter
  * generate           → AsyncLLMClient
  * chat / chat_json   → LLMProviderRouter → sync_provider_chain
  * generate_sync      → sync_provider_chain.generate_with_fallback
"""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol, runtime_checkable


logger = logging.getLogger(__name__)


def _record_llm_call(provider: str, model: str, status: str, duration: float) -> None:
    """Best-effort Prometheus increment. Never raises (observability must not crash callers)."""
    try:
        from src.api.routers.metrics import (
            LLM_CALLS,
            LLM_LATENCY,
        )

        LLM_CALLS.labels(
            provider=provider or "unknown", model=model or "unknown", status=status
        ).inc()
        LLM_LATENCY.labels(provider=provider or "unknown", model=model or "unknown").observe(
            duration
        )
    except Exception as exc:  # pragma: no cover - metrics are best-effort
        logger.debug("metrics increment failed: %s", exc)


@runtime_checkable
class LLMGateway(Protocol):
    """The single entry contract. Implementations delegate to provider strategies."""

    async def generate_for_stage(
        self,
        stage: str | None = None,
        prompt: str = "",
        system_prompt: str | None = None,
        use_retry: bool = True,
        stage_name: str | None = None,
    ) -> Any: ...

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
        phase: str | None = None,
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
        stage: str | None = None,
        prompt: str = "",
        system_prompt: str | None = None,
        use_retry: bool = True,
        stage_name: str | None = None,
    ) -> Any:
        resolved_stage = stage or stage_name or "default"
        _ = stage_name
        t0 = time.monotonic()
        provider = "stage_router"
        model = resolved_stage
        try:
            result = await self._router().generate(
                resolved_stage, prompt, system_prompt=system_prompt, use_retry=use_retry
            )
            _record_llm_call(provider, model, "success", time.monotonic() - t0)
            return result
        except Exception:
            _record_llm_call(provider, model, "error", time.monotonic() - t0)
            raise

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
        phase: str | None = None,
    ) -> Any:
        t0 = time.monotonic()
        provider = "async_client"
        try:
            result = await self._client().generate(
                prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                response_format=response_format,
                phase=phase,
            )
            _record_llm_call(provider, model or "default", "success", time.monotonic() - t0)
            return result
        except Exception:
            _record_llm_call(provider, model or "default", "error", time.monotonic() - t0)
            raise

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        from src.llm.providers.unified import LLMProviderRouter

        t0 = time.monotonic()
        provider = "provider_router"
        try:
            result = await LLMProviderRouter.chat(
                messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
            _record_llm_call(provider, "chat", "success", time.monotonic() - t0)
            return result
        except Exception:
            _record_llm_call(provider, "chat", "error", time.monotonic() - t0)
            raise

    async def chat_json(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> dict[str, Any]:
        from src.llm.providers.unified import LLMProviderRouter

        t0 = time.monotonic()
        provider = "provider_router"
        try:
            result = await LLMProviderRouter.chat_json(
                messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            _record_llm_call(provider, "chat_json", "success", time.monotonic() - t0)
            return result
        except Exception:
            _record_llm_call(provider, "chat_json", "error", time.monotonic() - t0)
            raise

    def generate_sync(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        preferred_model: str | None = None,
    ) -> str:
        """Synchronous multi-provider generate (sync_provider_chain under the hood)."""
        from src.llm.sync_provider_chain import generate_with_fallback

        t0 = time.monotonic()
        try:
            result = generate_with_fallback(
                prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                preferred_model=preferred_model,
            )
            _record_llm_call(
                "sync_chain", preferred_model or "auto", "success", time.monotonic() - t0
            )
            return result
        except Exception:
            _record_llm_call(
                "sync_chain", preferred_model or "auto", "error", time.monotonic() - t0
            )
            raise

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


def generate_with_fallback(
    prompt: str,
    *,
    system_prompt: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    preferred_model: str | None = None,
) -> str:
    """Public sync generate — thin alias of ``get_gateway().generate_sync``."""
    return get_gateway().generate_sync(
        prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        preferred_model=preferred_model,
    )
