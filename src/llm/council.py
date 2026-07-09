# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Callable

import httpx


logger = logging.getLogger(__name__)

COUNCIL_BUDGET = os.environ.get("LLM_COUNCIL_BUDGET", "balanced")


def _load_council_models(budget: str) -> list[str]:
    """Load council model list from ~/.c4reqber/models.json or use built-in defaults."""
    try:
        config_path = os.path.expanduser("~/.c4reqber/models.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
            council_cfg = data.get("council", {})
            if budget in council_cfg:
                return council_cfg[budget]
    except Exception as e:
        logger.debug("Council model config load failed: %s", e)
        pass
    return COUNCIL_MODELS.get(budget, COUNCIL_MODELS["balanced"])


COUNCIL_MODELS = {
    "cheap": [
        "deepseek/deepseek-chat",
        "qwen/qwen-2.5-72b-instruct",
        "openai/gpt-4o-mini",
    ],
    "balanced": [
        "anthropic/claude-sonnet-4.6",
        "deepseek/deepseek-r1",
        "qwen/qwen-2.5-72b-instruct",
    ],
    "premium": [
        "anthropic/claude-sonnet-4.6",
        "openai/gpt-4.5-preview",
        "deepseek/deepseek-r1",
    ],
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
LOCAL_ENDPOINTS = [
    "http://localhost:1234/v1",
    "http://localhost:11434/api",
]


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Word-overlap Jaccard similarity proxy."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _text_similarity(text_a: str, text_b: str) -> float:
    """Extended similarity using bigram overlap for better granularity."""
    js = _jaccard_similarity(text_a, text_b)

    bigrams_a = set(zip(text_a.lower().split(), text_a.lower().split()[1:], strict=False))
    bigrams_b = set(zip(text_b.lower().split(), text_b.lower().split()[1:], strict=False))
    if not bigrams_a or not bigrams_b:
        return js
    bg_inter = bigrams_a & bigrams_b
    bg_union = bigrams_a | bigrams_b
    bs = len(bg_inter) / len(bg_union) if bg_union else 0.0
    return 0.4 * js + 0.6 * bs


@dataclass
class CouncilResult:
    """CouncilResult."""
    responses: list[str]
    consensus: str
    confidence: float
    agreement_score: float
    model_used: list[str]


class LLMCouncil:
    """LLMCouncil."""
    def __init__(self, models: list[str] | None = None, min_agreement: float = 0.6, budget: str | None = None):
        self.budget = budget or COUNCIL_BUDGET
        self.models = models or _load_council_models(self.budget)
        self.min_agreement = min_agreement
        self._api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
        self._local_client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def _get_local_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._local_client is None:
                self._local_client = httpx.AsyncClient(timeout=30.0)
            return self._local_client

    async def deliberate(
        self,
        prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
        parser: Callable[[str], Any] | None = None,
    ) -> CouncilResult:
        """Send prompt to all council models, collect responses, compute agreement."""
        if not self._api_key:
            logger.warning("No API key configured for LLMCouncil")
            return CouncilResult(
                responses=[],
                consensus="",
                confidence=0.0,
                agreement_score=0.0,
                model_used=[],
            )

        tasks = [
            self._query_model(model, prompt, max_tokens, temperature)
            for model in self.models
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses: list[str] = []
        model_used: list[str] = []
        for model, result in zip(self.models, results, strict=False):
            if isinstance(result, BaseException):
                logger.warning("Model %s failed: %s", model, result)
                continue
            if result:
                responses.append(result)
                model_used.append(model)

        if not responses:
            return CouncilResult(
                responses=[],
                consensus="",
                confidence=0.0,
                agreement_score=0.0,
                model_used=[],
            )

        agreement = self._compute_agreement(responses)
        consensus = self._merge_responses(responses, parser)
        confidence = min(agreement, 0.95)

        if agreement < self.min_agreement:
            logger.warning(
                "Council agreement %.2f below threshold %.2f; using best response",
                agreement,
                self.min_agreement,
            )

        return CouncilResult(
            responses=responses,
            consensus=consensus,
            confidence=confidence,
            agreement_score=agreement,
            model_used=model_used,
        )

    async def _query_model(
        self, model: str, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Query a single model via OpenRouter."""
        if "sk-or-" in self._api_key:
            url = OPENROUTER_URL
            effective_model = model
        else:
            url = DEEPSEEK_URL
            effective_model = "deepseek-chat"

        try:
            # Audit 2026-06-22 H-8 Tier 1: guard the raw httpx call with
            # src.llm.guarded_call for metrics + sanitization + cost tracking.
            from src.llm.guarded_call import guarded_chat_completion
            data = await guarded_chat_completion(
                url=url,
                api_key=self._api_key,
                model=effective_model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=90.0,
                extra_body={
                    "headers": {
                        # OpenRouter attribution headers — guarded_call
                        # passes Authorization + Content-Type automatically.
                        "HTTP-Referer": "https://c4reqber.org",
                        "X-Title": "C4Reqber",
                    },
                } if "openrouter" in url else None,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a rigorous cross-domain research scientist. Be bold, specific, and precise. Return structured output when requested.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = data["choices"][0]["message"]["content"]
            logger.debug(
                "Model %s responded with %d chars", model, len(content)
            )
            return content
        except Exception as e:
            logger.debug("Model %s API failed: %s", model, e)
            raise RuntimeError(f"Council model failed: {e}") from e

    async def _query_local(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Query local LLM (LM Studio or Ollama)."""
        for endpoint in LOCAL_ENDPOINTS:
            client = await self._get_local_client()
            resp = await client.post(
                f"{endpoint}/chat/completions",
                json={
                    "model": "local-model",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _compute_agreement(self, responses: list[str]) -> float:
        """Compute average pairwise bigram Jaccard similarity."""
        if len(responses) < 2:
            return 1.0

        similarities: list[float] = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                sim = _text_similarity(responses[i], responses[j])
                similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _merge_responses(
        self, responses: list[str], parser: Callable | None
    ) -> str:
        """Pick the response with highest average pairwise similarity to others."""
        if len(responses) == 1:
            return responses[0]

        best_response = responses[0]
        best_score = -1.0

        for candidate in responses:
            total_sim = 0.0
            for other in responses:
                if candidate is not other:
                    total_sim += _text_similarity(candidate, other)
            avg_sim = total_sim / max(len(responses) - 1, 1)
            if avg_sim > best_score:
                best_score = avg_sim
                best_response = candidate

        return best_response


async def council_generate(
    prompt: str,
    max_tokens: int = 1500,
    temperature: float = 0.7,
    models: list[str] | None = None,
) -> CouncilResult:
    """Convenience function: run council on a prompt and return merged result."""
    council = LLMCouncil(models=models)
    return await council.deliberate(prompt, max_tokens=max_tokens, temperature=temperature)
