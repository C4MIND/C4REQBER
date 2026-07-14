"""Variant detection based on hostname"""
from __future__ import annotations

import os
from typing import Any


def detect_variant() -> str:
    """Detect variant from environment or hostname"""
    env = os.environ.get("C4REQBER_VARIANT", "")
    if env and env in {"invent", "engineering", "business", "science"}:
        return env

    hostname = os.environ.get("HOSTNAME", "")
    if "eng" in hostname or "engineering" in hostname:
        return "engineering"
    elif "biz" in hostname or "business" in hostname:
        return "business"
    elif "sci" in hostname or "science" in hostname:
        return "science"

    return "invent"  # Default

def get_variant_config(variant: str | None = None) -> dict[str, Any]:
    """Get variant config."""
    from src.config.variants import VARIANTS_CONFIG
    if variant is None:
        variant = detect_variant()
    return VARIANTS_CONFIG.get(variant, VARIANTS_CONFIG["invent"])  # type: ignore[return-value]
