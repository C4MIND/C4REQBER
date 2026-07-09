"""Synchronous multi-provider LLM chain — free-first, rotates on failure."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from src.config import get_key
from src.config.paths import OPENCODE_ZEN_FREE_MODELS, opencode_api_keys


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _ProviderSpec:
    name: str
    url: str
    model: str
    api_key: str
    extra_headers: dict[str, str]


def _key(name: str, env_var: str) -> str:
    return get_key(name) or os.environ.get(env_var, "")


def _lm_studio_url() -> str:
    raw = os.environ.get("LM_STUDIO_URL", "http://localhost:1234")
    return raw.rstrip("/")


def _build_chain() -> list[_ProviderSpec]:
    chain: list[_ProviderSpec] = []

    # 1) Ollama local (~4.7GB, best RAM/quality tradeoff)
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    try:
        r = httpx.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=2.0)
        if r.status_code == 200:
            models = [m.get("name", "") for m in r.json().get("models", [])]
            preferred = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
            model = (
                preferred
                if preferred in models
                else (models[0] if models else "qwen2.5:7b-instruct")
            )
            chain.append(
                _ProviderSpec(
                    "ollama", f"{ollama_url.rstrip('/')}/v1/chat/completions", model, "", {}
                )
            )
    except Exception:
        pass

    # 2) OpenCode Zen — free cloud models (~/.kilo: 6 keys × 7 models)
    zen_base = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    zen_headers = {"HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"}
    for zen_key in opencode_api_keys():
        for model in OPENCODE_ZEN_FREE_MODELS:
            chain.append(
                _ProviderSpec(
                    "opencode_zen",
                    f"{zen_base}/chat/completions",
                    model,
                    zen_key,
                    zen_headers,
                )
            )

    # 2b) Groq — fast free-tier cloud
    groq_key = _key("groq", "GROQ_API_KEY")
    if groq_key:
        for model in (
            os.environ.get("GROQ_MODEL_DEFAULT", "llama-3.3-70b-versatile"),
            "qwen-qwq-32b",
            "llama-3.1-8b-instant",
        ):
            chain.append(
                _ProviderSpec(
                    "groq",
                    "https://api.groq.com/openai/v1/chat/completions",
                    model,
                    groq_key,
                    {},
                )
            )

    # 3) LM Studio local (GGUF)
    lm_url = _lm_studio_url()
    try:
        r = httpx.get(f"{lm_url}/v1/models", timeout=2.0)
        if r.status_code == 200:
            models = [m.get("id", "") for m in r.json().get("data", [])]
            model = models[0] if models else "local-model"
            chain.append(_ProviderSpec("lm_studio", f"{lm_url}/v1/chat/completions", model, "", {}))
    except Exception:
        pass

    or_key = _key("openrouter", "OPENROUTER_API_KEY")
    if or_key:
        or_headers = {"HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"}
        # Paid/reliable models first; broken :free ids last.
        for model in (
            "qwen/qwen-2.5-72b-instruct",
            "mistralai/mistral-nemo",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
        ):
            chain.append(
                _ProviderSpec(
                    "openrouter",
                    "https://openrouter.ai/api/v1/chat/completions",
                    model,
                    or_key,
                    or_headers,
                )
            )

    nv_key = _key("nvidia", "NVIDIA_API_KEY")
    if nv_key:
        chain.append(
            _ProviderSpec(
                "nvidia",
                "https://integrate.api.nvidia.com/v1/chat/completions",
                "nvidia/nemotron-3-nano-30b-a3b",
                nv_key,
                {},
            )
        )

    xai_key = _key("xai", "XAI_API_KEY")
    if xai_key:
        chain.append(
            _ProviderSpec(
                "xai",
                "https://api.x.ai/v1/chat/completions",
                "grok-2-1212",
                xai_key,
                {},
            )
        )

    ds_key = _key("deepseek", "DEEPSEEK_API_KEY")
    if ds_key:
        chain.append(
            _ProviderSpec(
                "deepseek",
                "https://api.deepseek.com/v1/chat/completions",
                "deepseek-chat",
                ds_key,
                {},
            )
        )

    # Last resort: MLX (~5.7GB RAM) — only if MLX_SERVER_ENABLED=1
    if os.environ.get("MLX_SERVER_ENABLED", "0") in ("1", "true", "yes"):
        mlx_url = os.environ.get("MLX_SERVER_URL", "http://localhost:8001")
        try:
            r = httpx.get(f"{mlx_url.rstrip('/')}/v1/models", timeout=2.0)
            if r.status_code == 200:
                models = [m.get("id", "") for m in r.json().get("data", [])]
                model = models[0] if models else "mlx-community/Qwen3.5-9B-4bit"
                chain.append(
                    _ProviderSpec(
                        "mlx", f"{mlx_url.rstrip('/')}/v1/chat/completions", model, "", {}
                    )
                )
        except Exception:
            pass

    return chain


def generate_with_fallback(
    prompt: str,
    *,
    system_prompt: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    preferred_model: str | None = None,
) -> str:
    """Try providers in order until one succeeds."""
    system = system_prompt or (
        "You are a rigorous cross-domain research scientist. "
        "Write in academic English. Be bold but evidence-aware."
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    chain = _build_chain()
    if preferred_model:
        chain = sorted(chain, key=lambda p: 0 if p.model == preferred_model else 1)

    errors: list[str] = []
    with httpx.Client(timeout=120.0) as client:
        for spec in chain:
            headers = {"Content-Type": "application/json", **spec.extra_headers}
            if spec.api_key:
                headers["Authorization"] = f"Bearer {spec.api_key}"
            body: dict[str, Any] = {
                "model": spec.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            try:
                resp = client.post(spec.url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if content and content.strip():
                    logger.info("LLM ok via %s / %s", spec.name, spec.model)
                    return content
            except Exception as e:
                err = f"{spec.name}/{spec.model}: {type(e).__name__}"
                errors.append(err)
                logger.warning("LLM provider failed: %s", err)

    return f"[LLM unavailable: all providers failed — {'; '.join(errors[:4])}]"
