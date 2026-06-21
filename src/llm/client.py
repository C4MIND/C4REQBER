"""LLM Client.

Multi-provider LLM interface (OpenRouter, Claude, local)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from src.config import get_key


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: dict[str, int]
    raw_response: dict | None = None  # type: ignore[type-arg]


class LLMClient:
    """
    Universal LLM client supporting multiple providers.

    Priority:
    1. OpenRouter (multi-model access)
    2. Claude Direct (Anthropic)
    3. Local models (ollama, llama.cpp)
    """

    DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct"

    # Models optimized for different tasks
    MODELS = {
        "hypothesis": "anthropic/claude-sonnet-4.6",  # Best for scientific reasoning
        "falsifiability": "openai/gpt-4o",  # Good at structured criteria
        "synthesis": "anthropic/claude-sonnet-4.6",  # Coherent synthesis
        "cheap": "openai/gpt-4o-mini",  # Cost-effective
    }

    def __init__(self, api_key: str | None = None) -> None:
        # Prefer central config (~/.c4reqber) with env override
        self.api_key = api_key or get_key("openrouter") or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.referer = "https://c4reqber.org"  # Required by OpenRouter

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        """
        Generate text using LLM.

        Args:
            prompt: User prompt
            model: Model identifier (default: claude-sonnet-4.6)
            temperature: 0-1 (0=deterministic, 1=creative)
            max_tokens: Maximum response length
            system_prompt: System instructions
            response_format: "json" or None

        Returns:
            LLMResponse with content and metadata
        """
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. "
                "Set OPENROUTER_API_KEY environment variable."
            )

        model = model or self.DEFAULT_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            data["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.referer,
            "X-Title": "C4Reqber",
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())

                return LLMResponse(
                    content=result["choices"][0]["message"]["content"],
                    model=result.get("model", model),
                    usage=result.get("usage", {}),
                    raw_response=result,
                )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"LLM API error: {e.code} - {error_body}") from e
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            raise RuntimeError(f"LLM request failed: {e}") from e

    def generate_structured(
        self, prompt: str, schema: dict[str, Any], model: str | None = None
    ) -> dict[str, Any]:
        """
        Generate structured JSON response.

        Args:
            prompt: User prompt
            schema: JSON schema for validation
            model: Model identifier

        Returns:
            Parsed JSON object
        """
        system_prompt = f"""You must respond with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with JSON, no markdown formatting, no explanations."""

        response = self.generate(
            prompt=prompt,
            model=model or self.MODELS["falsifiability"],
            system_prompt=system_prompt,
            temperature=0.3,  # More deterministic for structured output
            response_format="json",
        )

        try:
            return json.loads(response.content)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())  # type: ignore[no-any-return]

    def test_connection(self) -> bool:
        """Test API connectivity."""
        try:
            response = self.generate(
                prompt="Respond with 'C4Reqber connected'",
                max_tokens=10,
                temperature=0,
            )
            return "C4Reqber" in response.content
        except (ConnectionError, TimeoutError, OSError, ValueError):
            return False


# MockLLMClient intentionally omitted — use real providers only in production.
        # For testing, register a test provider explicitly.
