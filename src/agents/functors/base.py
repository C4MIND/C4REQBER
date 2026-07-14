from __future__ import annotations


"""Base functor agent class with LLM integration."""
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.llm.async_client import AsyncLLMClient


class FunctorAgent(ABC):
    """Abstract base class for all functor agents."""

    symbol: str = "?"
    name_ru: str = ""
    name_en: str = ""
    c4_state: tuple[int, int, int] = (0, 0, 0)
    phase: str = "дивергенция"

    def __init__(self, llm_client: AsyncLLMClient | None = None) -> None:
        from src.llm.router import ProviderRouter
        self.llm_client = llm_client or ProviderRouter()

    @abstractmethod
    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze a problem and return structured insight."""
        ...

    @abstractmethod
    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform input data through the functor's cognitive operation."""
        ...

    async def _llm_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        """Make an async LLM call and return the generated text."""
        response = await self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content

    def _build_result(
        self,
        problem: str,
        insight: str,
        confidence: float = 0.75,
        contradiction: str | None = None,
        novel: bool = True,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a standardized result dict."""
        result: dict[str, Any] = {
            "agent": self.symbol,
            "agent_name": self.name_en,
            "agent_name_ru": self.name_ru,
            "problem": problem,
            "insight": insight,
            "confidence": round(confidence, 3),
            "contradiction": contradiction,
            "novel": novel,
            "c4_state": self.c4_state,
            "phase": self.phase,
        }
        if extra:
            result.update(extra)
        return result
