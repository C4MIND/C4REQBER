# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging

import httpx


logger = logging.getLogger(__name__)

LOCAL_ENDPOINTS = [
    "http://localhost:1234/v1",   # LM Studio
    "http://localhost:11434/v1",   # Ollama
]


async def try_local_llm(prompt: str, max_tokens: int = 1200) -> str:
    """Generate via local LLM (LM Studio or Ollama)."""
    for endpoint in LOCAL_ENDPOINTS:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{endpoint}/chat/completions",
                    json={
                        "model": "local-model",
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "messages": [
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("Local LLM succeeded via %s", endpoint)
                return content
        except Exception as e:
            logger.debug("Local LLM endpoint %s failed: %s", endpoint, e)
            continue
    raise RuntimeError("No local LLM endpoint available")
