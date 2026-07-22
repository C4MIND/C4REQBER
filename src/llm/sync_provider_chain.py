"""Synchronous multi-provider LLM chain — free-first, rotates on failure."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from src.config import get_key
from src.config.paths import OPENCODE_ZEN_FREE_MODELS, opencode_api_keys
from src.llm.errors import RateLimited


logger = logging.getLogger(__name__)

_LOCAL_PROVIDERS = frozenset({"lm_studio", "ollama", "mlx"})
# R9: cap rotation depth so 429 storms do not burn every free-tier key.
MAX_ROTATION_DEPTH = int(os.environ.get("C4_LLM_MAX_ROTATIONS", "8"))


def _parse_retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After", "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _reorder_local_first(chain: list[_ProviderSpec]) -> list[_ProviderSpec]:
    """Prefer LM Studio / Ollama / MLX when C4_LOCAL_LLM_FIRST or after 429."""
    local = [p for p in chain if p.name in _LOCAL_PROVIDERS]
    if not local:
        return chain
    rest = [p for p in chain if p.name not in _LOCAL_PROVIDERS]
    return local + rest


@dataclass(frozen=True)
class _ProviderSpec:
    name: str
    url: str
    model: str
    api_key: str
    extra_headers: dict[str, str]


def _key(name: str, env_var: str) -> str:
    return get_key(name) or os.environ.get(env_var, "")


def _nvidia_key() -> str:
    for env_var in ("NVIDIA_API_KEY_KILO", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY"):
        val = os.environ.get(env_var, "")
        if val:
            return val
    return _key("nvidia", "NVIDIA_API_KEY")


def _groq_key() -> str:
    for env_var in ("GROQ_API_KEY_KILO", "GROQ_API_KEY_HERMES", "GROQ_API_KEY"):
        val = os.environ.get(env_var, "")
        if val:
            return val
    return _key("groq", "GROQ_API_KEY")


def _lm_studio_url() -> str:
    for raw in (
        os.environ.get("LM_STUDIO_URL_LOCAL"),
        "http://127.0.0.1:1234",
        os.environ.get("LM_STUDIO_URL"),
        "http://localhost:1234",
    ):
        if not raw:
            continue
        url = raw.rstrip("/")
        if "docker.internal" in url:
            continue
        try:
            r = httpx.get(f"{url}/v1/models", timeout=2.0)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return "http://127.0.0.1:1234"


def _lm_studio_model(models: list[str]) -> str:
    preferred = os.environ.get("LM_STUDIO_MODEL", "")
    if preferred and preferred in models:
        return preferred
    for candidate in ("qwen2.5-14b-instruct", "qwen2.5-7b-instruct"):
        if candidate in models:
            return candidate
    return models[0] if models else "local-model"


def _build_chain() -> list[_ProviderSpec]:
    chain: list[_ProviderSpec] = []

    # 1) OpenCode Zen — free cloud (6 keys × priority models)
    zen_base = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    zen_headers = {"HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"}
    zen_models = list(OPENCODE_ZEN_FREE_MODELS)
    preferred = os.environ.get("C4_LLM_MODEL", "")
    if preferred and preferred in zen_models:
        zen_models = [preferred] + [m for m in zen_models if m != preferred]
    for zen_key in opencode_api_keys():
        for model in zen_models:
            chain.append(
                _ProviderSpec(
                    "opencode_zen",
                    f"{zen_base}/chat/completions",
                    model,
                    zen_key,
                    zen_headers,
                )
            )

    # 2) Groq — fast free-tier cloud
    groq_key = _groq_key()
    if groq_key:
        for model in (
            os.environ.get("GROQ_MODEL_DEFAULT", "llama-3.3-70b-versatile"),
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

    # 3) NVIDIA NIM (KILO key — dontredact NVIDIA_API_KEY often 403)
    nv_key = _nvidia_key()
    if nv_key:
        nv_base = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip(
            "/"
        )
        for model in ("nvidia/nemotron-3-nano-30b-a3b", "meta/llama-3.1-8b-instruct"):
            chain.append(
                _ProviderSpec(
                    "nvidia_nim",
                    f"{nv_base}/chat/completions",
                    model,
                    nv_key,
                    {},
                )
            )

    # 4) LM Studio local (14B preferred over 7B)
    lm_url = _lm_studio_url()
    try:
        r = httpx.get(f"{lm_url}/v1/models", timeout=2.0)
        if r.status_code == 200:
            models = [m.get("id", "") for m in r.json().get("data", [])]
            model = _lm_studio_model(models)
            chain.append(_ProviderSpec("lm_studio", f"{lm_url}/v1/chat/completions", model, "", {}))
    except Exception:
        logger.debug("LM Studio probe skipped", exc_info=True)

    # 5) Ollama local
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
        logger.debug("Ollama probe skipped", exc_info=True)

    or_key = _key("openrouter", "OPENROUTER_API_KEY") or os.environ.get(
        "KILO_OPENROUTER_API_KEY", ""
    )
    if or_key:
        or_headers = {"HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"}
        for model in (
            "qwen/qwen-2.5-72b-instruct",
            "meta-llama/llama-3.3-70b-instruct:free",
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

    ds_key = _key("deepseek", "DEEPSEEK_API_KEY")
    if ds_key:
        ds_model = (
            os.environ.get("DEEPSEEK_MODEL") or os.environ.get("C4_LLM_MODEL") or "deepseek-chat"
        )
        # Prefer assigned phase-F model when it looks like a DeepSeek id
        try:
            from src.llm.model_assignment import get_model_for_phase

            assigned = get_model_for_phase("F")
            if assigned and "deepseek" in assigned.lower():
                ds_model = assigned.split("/")[-1] if "/" in assigned else assigned
        except Exception:
            logger.debug("DeepSeek model assignment probe failed", exc_info=True)
        chain.append(
            _ProviderSpec(
                "deepseek",
                "https://api.deepseek.com/v1/chat/completions",
                ds_model,
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
            logger.debug("MLX probe skipped", exc_info=True)

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
        pref = preferred_model.strip()
        # Prefer exact model match; also force OpenRouter entry with preferred id.
        matched = [p for p in chain if p.model == pref or pref in p.model]
        rest = [p for p in chain if p not in matched]
        or_key = _key("openrouter", "OPENROUTER_API_KEY") or os.environ.get(
            "KILO_OPENROUTER_API_KEY", ""
        )
        if or_key and pref and not any(p.model == pref and p.name == "openrouter" for p in matched):
            or_headers = {"HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"}
            matched.insert(
                0,
                _ProviderSpec(
                    "openrouter",
                    "https://openrouter.ai/api/v1/chat/completions",
                    pref,
                    or_key,
                    or_headers,
                ),
            )
        chain = matched + rest

    if os.getenv("C4_LOCAL_LLM_FIRST", "").lower() in ("1", "true", "yes"):
        chain = _reorder_local_first(chain)

    errors: list[str] = []
    last_retry_after: float | None = None
    last_rate_provider = ""
    saw_429 = False
    attempts = 0

    with httpx.Client(timeout=120.0) as client:
        idx = 0
        while idx < len(chain):
            if attempts >= MAX_ROTATION_DEPTH:
                logger.warning(
                    "LLM rotation cap reached (%d); stopping to avoid key burn",
                    MAX_ROTATION_DEPTH,
                )
                break
            spec = chain[idx]
            idx += 1
            attempts += 1
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
                if resp.status_code == 429:
                    saw_429 = True
                    last_retry_after = _parse_retry_after(resp) or last_retry_after
                    last_rate_provider = spec.name
                    err = f"{spec.name}/{spec.model}: HTTP 429"
                    errors.append(err)
                    logger.warning("LLM rate limited: %s", err)
                    # After first 429, prefer local providers for remaining attempts.
                    if idx < len(chain):
                        chain = chain[:idx] + _reorder_local_first(chain[idx:])
                    continue
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if content and content.strip():
                    logger.info("LLM ok via %s / %s", spec.name, spec.model)
                    return content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    saw_429 = True
                    last_retry_after = _parse_retry_after(e.response) or last_retry_after
                    last_rate_provider = spec.name
                    err = f"{spec.name}/{spec.model}: HTTP 429"
                    errors.append(err)
                    logger.warning("LLM rate limited: %s", err)
                    if idx < len(chain):
                        chain = chain[:idx] + _reorder_local_first(chain[idx:])
                    continue
                err = f"{spec.name}/{spec.model}: HTTP {e.response.status_code}"
                errors.append(err)
                logger.warning("LLM provider failed: %s", err)
            except Exception as e:
                err = f"{spec.name}/{spec.model}: {type(e).__name__}"
                errors.append(err)
                logger.warning("LLM provider failed: %s", err)

    if saw_429:
        raise RateLimited(
            f"all providers rate-limited after {attempts} attempt(s)",
            retry_after=last_retry_after,
            provider=last_rate_provider or "openrouter",
        )

    raise RuntimeError(f"All LLM providers failed: {'; '.join(errors[:4])}")
