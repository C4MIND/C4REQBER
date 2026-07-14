# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Shared utility functions consolidated from duplicated implementations across the project."""
from __future__ import annotations

import math
import re


def normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function (Abramowitz & Stegun 26.2.17)."""
    if z < -8:
        return 0.0
    if z > 8:
        return 1.0
    t = 1.0 / (1.0 + 0.2316419 * abs(z))
    d = 0.3989422804014327 * math.exp(-z * z / 2.0)
    poly = ((((1.330274429 * t - 1.821255978) * t + 1.781477937) * t - 0.356563782) * t + 0.319381530) * t
    prob = 1.0 - d * poly
    return prob if z >= 0 else 1.0 - prob


def extract_doi(text: str) -> str | None:
    """Extract DOI from text string. Returns None if not found."""
    doi_re = re.compile(r"\b10\.\d{4,}/[^\s\"']+")
    match = doi_re.search(text)
    return match.group(0).rstrip(".,;:") if match else None
