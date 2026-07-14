"""MLX-LM Local LLM Provider — Apple Silicon GPU inference.

Auto-detects M1+ Macs. Loads mlx-lm models lazily.
Returns LLMResponse objects compatible with the LLM routing system.
"""

from __future__ import annotations

import logging
import os
import platform
from typing import Any

from src.llm.providers.base import LLMResponse


logger = logging.getLogger(__name__)

_PROCESSOR = platform.processor().lower()
_IS_APPLE_SILICON = "arm" in _PROCESSOR or "apple" in _PROCESSOR


class MLXProvider:
    """LLM provider for Apple Silicon via mlx-lm.

    Implements generate() returning LLMResponse objects for routing compatibility.
    Models are loaded lazily on first call.
    """

    def __init__(self, model: str | None = None, timeout: float = 120.0) -> None:
        self._model_name: str = model or os.getenv("MLX_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit") or "mlx-community/Qwen2.5-7B-Instruct-4bit"
        self.timeout = timeout
        self._model: Any = None
        self._tokenizer: Any = None

    @property
    def available(self) -> bool:
        return _IS_APPLE_SILICON and self._check_mlx()

    @property
    def model_name(self) -> str:
        return self._model_name

    def _check_mlx(self) -> bool:
        try:
            import mlx.core
            import mlx_lm
            return True
        except ImportError:
            return False

    def _load_model(self) -> bool:
        """Load the mlx-lm model and tokenizer lazily."""
        if self._model is not None:
            return True
        if not self.available:
            return False
        try:
            import mlx_lm

            loaded = mlx_lm.load(self._model_name)
            if isinstance(loaded, tuple) and len(loaded) >= 2:
                self._model = loaded[0]
                self._tokenizer = loaded[1]
            else:
                raise RuntimeError(f"Unexpected mlx_lm.load return: {type(loaded)}")
            return True
        except Exception as e:
            logger.error("Failed to load MLX model %s: %s", self._model_name, e)
            return False

    @staticmethod
    def is_apple_silicon() -> bool:
        return _IS_APPLE_SILICON

    @staticmethod
    def list_local_models() -> list[str]:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        models = []
        if os.path.isdir(cache_dir):
            for entry in os.listdir(cache_dir):
                if entry.startswith("models--"):
                    name = entry.replace("models--", "").replace("--", "/")
                    models.append(name)
        return sorted(models)

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text via mlx-lm. Returns LLMResponse."""
        import time as _time
        t0 = _time.perf_counter()

        effective_model: str = model or self._model_name
        if not self.available:
            return LLMResponse(
                content="",
                model=effective_model,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                latency_ms=0.0,
                provider="mlx",
            )

        if not self._load_model():
            return LLMResponse(
                content="[MLX Error] Failed to load model",
                model=self._model_name,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                latency_ms=0.0,
                provider="mlx",
            )

        try:
            import mlx_lm

            full_prompt = self._build_prompt(prompt, system_prompt)

            response_text = mlx_lm.generate(
                self._model,
                self._tokenizer,
                prompt=full_prompt,
                max_tokens=max_tokens,
                temp=temperature,
                verbose=False,
            )

            elapsed = (_time.perf_counter() - t0) * 1000
            return LLMResponse(
                content=response_text,
                model=self._model_name,
                usage={"prompt_tokens": len(full_prompt) // 4, "completion_tokens": len(response_text) // 4},
                latency_ms=round(elapsed, 1),
                provider="mlx",
            )
        except Exception as e:
            logger.error("MLX generate failed: %s", e)
            return LLMResponse(
                content=f"[MLX Error] {e}",
                model=self._model_name,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                latency_ms=0.0,
                provider="mlx",
            )

    def _build_prompt(self, prompt: str, system_prompt: str | None = None) -> str:
        model_lower = self._model_name.lower()
        if "llama" in model_lower or "mistral" in model_lower:
            parts = []
            if system_prompt:
                parts.append(f"<|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|>")
            parts.append(f"<|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|>")
            parts.append("<|start_header_id|>assistant<|end_header_id|>\n")
            return "\n".join(parts)
        parts = []
        if system_prompt:
            parts.append(f"<|system|>\n{system_prompt}</s>")
        parts.append(f"<|user|>\n{prompt}</s>")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)

    async def test_connection(self) -> dict[str, Any]:
        if not _IS_APPLE_SILICON:
            return {"healthy": False, "error": "Not Apple Silicon"}
        mlx_ok = self._check_mlx()
        models = self.list_local_models() if mlx_ok else []
        return {
            "healthy": mlx_ok,
            "apple_silicon": True,
            "mlx_installed": mlx_ok,
            "local_models": len(models),
            "models": models[:10],
            "active_model": self._model_name if mlx_ok else None,
        }
