"""Ollama and LM Studio local providers."""

from __future__ import annotations

from typing import Any

from src.llm.config import LLMProvider
from src.llm.providers.base import BaseLLMClient


class LocalLLMClient(BaseLLMClient):
    """Ollama / LM Studio client (delegates to local_client module)."""

    def __init__(self, provider: LLMProvider = LLMProvider.OLLAMA, timeout: float = 60.0) -> None:
        super().__init__(provider, api_key=None, timeout=timeout)
        self._local = None

    async def generate(
        self, prompt: Any, model: Any=None, temperature: Any=0.7, max_tokens: Any=2000, system_prompt: Any=None, response_format: Any=None
    ) -> Any:
        """Generate."""
        if self._local is None:
            from src.llm.local_client import LocalLLMClient as RealLocalClient

            self._local = RealLocalClient()  # type: ignore[assignment]
        return await self._local.generate(  # type: ignore[attr-defined]
            prompt, model, temperature, max_tokens, system_prompt, response_format
        )

    async def close(self) -> None:
        if self._local:
            await self._local.close()  # type: ignore[unreachable]
