"""
TUI: Local LLM Detection
Detects local LLM servers (Ollama, LM Studio, TextGen, LocalAI).
"""
from __future__ import annotations

import httpx


LOCAL_MODELS = {
    "ollama": "http://localhost:11434",
    "lmstudio": "http://localhost:1234",
    "textgen": "http://localhost:5000",
    "localai": "http://localhost:8080",
}


def detect_local_llm() -> str | None:
    """Detect which local LLM server is running."""
    try:
        for name, url in LOCAL_MODELS.items():
            try:
                endpoint = url + ("/api/tags" if name == "ollama" else "/v1/models")
                httpx.get(endpoint, timeout=1)
                return name
            except httpx.HTTPError:
                pass
    except ImportError:
        pass
    return None
