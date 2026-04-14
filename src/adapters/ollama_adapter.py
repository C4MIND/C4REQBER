"""
TURBO-CDI: Ollama Adapter
Local LLM support via Ollama
"""

import json
import urllib.request
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


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

    # Recommended models for TURBO-CDI
    RECOMMENDED_MODELS = {
        "reasoning": "qwen2.5:14b",  # Good reasoning, fits in 16GB
        "fast": "qwen2.5:7b",  # Fast, good for prototyping
        "powerful": "llama3.1:70b",  # If you have the VRAM
        "code": "codellama:34b",  # For code-heavy hypotheses
        "small": "phi3:medium",  # For low-end machines
    }

    def __init__(self, base_url: str = DEFAULT_URL):
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def list_models(self) -> List[OllamaModel]:
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

        except Exception as e:
            print(f"Failed to list models: {e}")
            return []

    def generate(
        self,
        prompt: str,
        model: str = "qwen2.5:14b",
        system: Optional[str] = None,
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
                return result.get("response", "")

        except Exception as e:
            return f"[Ollama Error: {e}]"

    def generate_structured(
        self, prompt: str, schema: Dict[str, Any], model: str = "qwen2.5:14b", **kwargs
    ) -> Dict[str, Any]:
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

            return json.loads(text.strip())
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
                return result.get("status") == "success"
        except Exception as e:
            print(f"Failed to pull model: {e}")
            return False

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
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
    3. Mock (fallback)
    """

    def __init__(
        self,
        openrouter_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        prefer_local: bool = False,
    ):
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
                import sys
                import os

                sys.path.insert(
                    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                from llm.client import LLMClient

                self.openrouter = LLMClient(openrouter_key)

        # Select active provider
        if prefer_local and self.ollama_available:
            self.active = "ollama"
        elif self.openrouter:
            self.active = "openrouter"
        elif self.ollama_available:
            self.active = "ollama"
        else:
            try:
                from ..llm.client import MockLLMClient

                self.openrouter = MockLLMClient()
            except ImportError:
                import sys
                import os

                sys.path.insert(
                    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                from llm.client import MockLLMClient

                self.openrouter = MockLLMClient()
            self.active = "mock"

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using active provider."""
        if self.active == "ollama":
            model = kwargs.pop("model", "qwen2.5:14b")
            return self.ollama.generate(prompt, model=model, **kwargs)
        else:
            return self.openrouter.generate(prompt, **kwargs)

    def generate_structured(self, prompt: str, schema: Dict, **kwargs) -> Dict:
        """Generate structured response."""
        if self.active == "ollama":
            model = kwargs.pop("model", "qwen2.5:14b")
            return self.ollama.generate_structured(
                prompt, schema, model=model, **kwargs
            )
        else:
            return self.openrouter.generate_structured(prompt, schema, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        return {
            "active_provider": self.active,
            "ollama_available": self.ollama_available,
            "openrouter_available": self.openrouter is not None,
            "prefer_local": self.prefer_local,
        }
