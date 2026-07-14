"""
C4REQBER: Ollama Adapter
Local LLM support via Ollama
"""
from __future__ import annotations

import asyncio
import json
import logging
import urllib.request
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger("c4reqber.adapters.ollama")


@dataclass
class OllamaModel:
    """Ollama model info."""

    name: str
    size: str
    parameter_size: str
    quantization: str
    format: str
    family: str


class OllamaAdapter:
    """
    Adapter for Ollama local LLM server.

    Requires Ollama to be installed and running:
    https://ollama.com
    """

    DEFAULT_URL = "http://localhost:11434"

    # Recommended models for C4REQBER
    RECOMMENDED_MODELS = {
        "reasoning": "qwen2.5:14b",  # Good reasoning, fits in 16GB
        "fast": "qwen2.5:7b",  # Fast, good for prototyping
        "powerful": "llama3.1:70b",  # If you have the VRAM
        "code": "codellama:34b",  # For code-heavy hypotheses
        "small": "phi3:medium",  # For low-end machines
    }

    def __init__(self, base_url: str = DEFAULT_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200  # type: ignore[no-any-return]
        except (ConnectionError, TimeoutError, OSError):
            return False

    async def async_is_available(self) -> bool:
        """Async check if Ollama server is running."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[OllamaModel]:
        """List available models."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                models = []
                for model in data.get("models", []):
                    models.append(
                        OllamaModel(
                            name=model.get("name", ""),
                            size=self._format_size(model.get("size", 0)),
                            parameter_size=model.get("details", {}).get(
                                "parameter_size", "?"
                            ),
                            quantization=model.get("details", {}).get(
                                "quantization_level", "?"
                            ),
                            format=model.get("details", {}).get("format", "?"),
                            family=model.get("details", {}).get("family", "?"),
                        )
                    )

                return models

        except (ConnectionError, TimeoutError, OSError, ValueError):
            logger.warning("Failed to list Ollama models", exc_info=True)
            return []

    async def async_list_models(self) -> list[OllamaModel]:
        """Async list available models."""
        return await asyncio.to_thread(self.list_models)

    def generate(
        self,
        prompt: str,
        model: str = "qwen2.5:14b",
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: User prompt
            model: Model name
            system: System prompt
            temperature: 0-1
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            data["system"] = system

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode())
                return result.get("response", "")  # type: ignore[no-any-return]

        except (ConnectionError, TimeoutError, OSError, ValueError):
            logger.warning("Ollama generation failed", exc_info=True)
            return "[Ollama Error: generation failed]"

    async def async_generate(
        self,
        prompt: str,
        model: str = "qwen2.5:14b",
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Async wrapper for generate."""
        return await asyncio.to_thread(
            self.generate, prompt, model, system, temperature, max_tokens
        )

    def generate_structured(
        self, prompt: str, schema: dict[str, Any], model: str = "qwen2.5:14b", **kwargs: Any
    ) -> dict[str, Any]:
        """
        Generate structured JSON response.
        """
        system = f"""You must respond with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with JSON, no markdown, no explanations."""

        full_prompt = f"{system}\n\n{prompt}"

        response = self.generate(
            prompt=full_prompt, model=model, temperature=0.3, **kwargs
        )

        try:
            # Try to extract JSON from response
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            return json.loads(text.strip())  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            # Return empty schema-compliant structure
            return {
                k: [] if v.get("type") == "array" else ""
                for k, v in schema.get("properties", {}).items()
            }

    def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        print(f"Pulling model {model}... This may take a while.")

        data = {"name": model, "stream": False}

        req = urllib.request.Request(
            f"{self.base_url}/api/pull",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                result = json.loads(response.read().decode())
                return result.get("status") == "success"  # type: ignore[no-any-return]
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            print(f"Failed to pull model: {e}")
            return False

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024  # type: ignore[assignment]
        return f"{size_bytes:.1f} TB"

    @classmethod
    def recommend_model(cls, vram_gb: int = 16) -> str:
        """Recommend model based on available VRAM."""
        if vram_gb >= 80:
            return cls.RECOMMENDED_MODELS["powerful"]
        elif vram_gb >= 40:
            return "llama3.1:70b-q4_0"  # Quantized 70B
        elif vram_gb >= 24:
            return cls.RECOMMENDED_MODELS["reasoning"]
        elif vram_gb >= 16:
            return "qwen2.5:14b-q4_0"  # Quantized
        elif vram_gb >= 8:
            return cls.RECOMMENDED_MODELS["fast"]
        else:
            return cls.RECOMMENDED_MODELS["small"]


class LLMProvider:
    """
    Unified interface for multiple LLM providers.

    Priority:
    1. OpenRouter (cloud, multi-model)
    2. Ollama (local)
    """

    def __init__(
        self,
        openrouter_key: str | None = None,
        ollama_url: str = "http://localhost:11434",
        prefer_local: bool = False,
    ) -> None:
        self.prefer_local = prefer_local

        # Try Ollama first if preferred
        self.ollama = OllamaAdapter(ollama_url)
        self.ollama_available = self.ollama.is_available()

        # Try OpenRouter
        self.openrouter = None
        if openrouter_key:
            try:
                from ..llm.client import LLMClient

                self.openrouter = LLMClient(openrouter_key)
            except ImportError:
                import os
                import sys

                sys.path.insert(
                    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                from llm.client import LLMClient  # type: ignore[no-redef]

                self.openrouter = LLMClient(openrouter_key)

        # Select active provider — never silently fall back to mock
        if prefer_local and self.ollama_available:
            self.active = "ollama"
        elif self.openrouter:
            self.active = "openrouter"
        elif self.ollama_available:
            self.active = "ollama"
        else:
            self.active = "none"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using active provider. Raises RuntimeError if no provider."""
        if self.active == "ollama":
            model = kwargs.pop("model", "qwen2.5:14b")
            return self.ollama.generate(prompt, model=model, **kwargs)
        elif self.active == "openrouter":
            return self.openrouter.generate(prompt, **kwargs)  # type: ignore[return-value, union-attr]
        else:
            raise RuntimeError(
                "No LLM provider available. Set OPENROUTER_API_KEY or start Ollama."
            )

    def generate_structured(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Generate structured response. Raises RuntimeError if no provider."""
        if self.active == "ollama":
            model = kwargs.pop("model", "qwen2.5:14b")
            return self.ollama.generate_structured(
                prompt, schema, model=model, **kwargs
            )
        elif self.active == "openrouter":
            return self.openrouter.generate_structured(prompt, schema, **kwargs)  # type: ignore[union-attr]
        else:
            raise RuntimeError(
                "No LLM provider available. Set OPENROUTER_API_KEY or start Ollama."
            )

    def get_status(self) -> dict[str, Any]:
        """Get provider status."""
        return {
            "active_provider": self.active,
            "ollama_available": self.ollama_available,
            "openrouter_available": self.openrouter is not None,
            "prefer_local": self.prefer_local,
        }
