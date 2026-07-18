#!/usr/bin/env python3
"""Fast probe: one request per OpenCode/OR/NIM model. No secrets printed."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Load env
for _line in (ROOT / "scripts" / "load_kilo_env.sh").read_text().splitlines():
    pass  # shell only

# Manual load
for env_file in (
    Path.home() / ".kilo" / ".env",
    Path.home() / ".kilo" / "secrets" / "api_keys_working.env",
    ROOT / ".env.dontredact",
):
    if env_file.is_file():
        for raw in env_file.read_text().splitlines():
            if "=" in raw and not raw.strip().startswith("#"):
                k, v = raw.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


PROMPT = "Reply exactly: OK"
TIMEOUT = 25.0

OPENCODE_MODELS = [
    "deepseek-v4-flash-free",
    "nemotron-3-ultra-free",
    "qwen3.6-plus-free",
    "mimo-v2.5-free",
    "north-mini-code-free",
    "big-pickle",
    "minimax-m3-free",
]

OR_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen3-235b-a22b:free",
]

NIM_MODELS = [
    "nvidia/nemotron-3-nano-30b-a3b",
    "meta/llama-3.1-8b-instruct",
]


def _keys(prefix: str, n: int = 8) -> list[str]:
    out = []
    for i in range(1, n + 1):
        v = os.environ.get(f"{prefix}_{i}", "")
        if v and v not in out:
            out.append(v)
    p = os.environ.get(prefix.replace("_1", ""), "")
    if p and p not in out:
        out.insert(0, p)
    return out


def probe(url: str, key: str, model: str, headers: dict | None = None) -> tuple[bool, int, str]:
    h = {"Content-Type": "application/json", **(headers or {})}
    if key:
        h["Authorization"] = f"Bearer {key}"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 8,
        "temperature": 0,
    }
    t0 = time.monotonic()
    try:
        r = httpx.post(url, headers=h, json=body, timeout=TIMEOUT)
        ms = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return False, ms, f"HTTP{r.status_code}"
        c = r.json()["choices"][0]["message"]["content"]
        return bool(c and c.strip()), ms, (c or "")[:30]
    except Exception as e:
        return False, int((time.monotonic() - t0) * 1000), type(e).__name__


def main() -> None:
    zen_base = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    zen_hdr = {"HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"}
    oc_keys = _keys("OPENCODE_API_KEY", 6)

    print("=== OpenCode Zen ===")
    winners_oc: dict[str, tuple[int, str]] = {}
    for model in OPENCODE_MODELS:
        for ki, key in enumerate(oc_keys):
            ok, ms, det = probe(f"{zen_base}/chat/completions", key, model, zen_hdr)
            print(f"  {'OK' if ok else 'FAIL':4} {model:<28} key#{ki + 1} {ms:>5}ms  {det}")
            if ok and model not in winners_oc:
                winners_oc[model] = (ms, f"key#{ki + 1}")
                break

    or_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("KILO_OPENROUTER_API_KEY", "")
    or_hdr = zen_hdr
    print("\n=== OpenRouter ===")
    winners_or: dict[str, int] = {}
    for model in OR_MODELS:
        ok, ms, det = probe("https://openrouter.ai/api/v1/chat/completions", or_key, model, or_hdr)
        print(f"  {'OK' if ok else 'FAIL':4} {model:<42} {ms:>5}ms  {det}")
        if ok:
            winners_or[model] = ms

    nv_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_API_KEY_KILO", "")
    nv_base = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
    print("\n=== NVIDIA NIM ===")
    for model in NIM_MODELS:
        ok, ms, det = probe(f"{nv_base}/chat/completions", nv_key, model)
        print(f"  {'OK' if ok else 'FAIL':4} {model:<42} {ms:>5}ms  {det}")

    groq_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY_KILO", "")
    print("\n=== Groq ===")
    for model in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
        ok, ms, det = probe("https://api.groq.com/openai/v1/chat/completions", groq_key, model)
        print(f"  {'OK' if ok else 'FAIL':4} {model:<42} {ms:>5}ms  {det}")

    lm = os.environ.get("LM_STUDIO_URL", "http://localhost:1234").rstrip("/")
    try:
        r = httpx.get(f"{lm}/v1/models", timeout=3)
        models = [m["id"] for m in r.json().get("data", [])]
        print("\n=== LM Studio ===")
        for mid in models[:3]:
            ok, ms, det = probe(f"{lm}/v1/chat/completions", "", mid)
            print(f"  {'OK' if ok else 'FAIL':4} {mid:<42} {ms:>5}ms  {det}")
    except Exception as e:
        print(f"\n=== LM Studio: {e} ===")

    print(f"\nOpenCode winners: {len(winners_oc)}/{len(OPENCODE_MODELS)}")
    for m, (ms, k) in winners_oc.items():
        print(f"  {m} ({ms}ms via {k})")


if __name__ == "__main__":
    main()
