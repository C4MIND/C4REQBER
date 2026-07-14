# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

LOCAL_ENDPOINTS = [
    "http://localhost:1234/v1",  # LM Studio
    "http://localhost:11434/v1",  # Ollama
]


async def try_local_llm(prompt: str, max_tokens: int = 1200) -> str:
    """Generate via local LLM (LM Studio or Ollama).

    Audit 2026-06-22 H-8 Tier 1: each endpoint attempt is wrapped in
    guarded_chat_completion for metrics (provider="local") + sanitization.
    Cost is $0 for local providers but token usage is still tracked.
    """
    from src.llm.guarded_call import guarded_chat_completion

    for endpoint in LOCAL_ENDPOINTS:
        try:
            data = await guarded_chat_completion(
                url=f"{endpoint}/chat/completions",
                api_key="not-required",  # Local servers don't need auth
                model="local-model",
                temperature=0.7,
                max_tokens=max_tokens,
                timeout=30.0,
                messages=[{"role": "user", "content": prompt}],
            )
            content = data["choices"][0]["message"]["content"]
            logger.info("Local LLM succeeded via %s", endpoint)
            return content
        except Exception as e:
            logger.debug("Local LLM endpoint %s failed: %s", endpoint, e)
            continue
    raise RuntimeError("No local LLM endpoint available")
