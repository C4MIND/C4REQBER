"""OpenRouter provider."""

from __future__ import annotations

import os
import time
from typing import Any

from src.llm.config import LLMProvider, get_default_model
from src.llm.providers.base import BaseLLMClient


class OpenRouterClient(BaseLLMClient):
    """OpenRouter client."""

    def __init__(self, api_key: str | None = None, timeout: float = 60.0) -> None:
        super().__init__(LLMProvider.OPENROUTER, api_key, timeout)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    async def generate(
        self, prompt: Any, model: Any=None, temperature: Any=0.7, max_tokens: Any=2000, system_prompt: Any=None, response_format: Any=None
    ) -> Any:
        """Generate."""
        await self._init_client()
        model = model or get_default_model(LLMProvider.OPENROUTER)
        messages = self._build_messages(prompt, system_prompt)
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        start = time.time()
        response = await self._client.post(f"{self.base_url}/chat/completions", json=data)  # type: ignore[union-attr]
        response.raise_for_status()
        result = response.json()
        latency_ms = (time.time() - start) * 1000
        return self._parse_openai_response(result, model, latency_ms)
