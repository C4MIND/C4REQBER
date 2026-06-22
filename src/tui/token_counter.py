# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import sys
from typing import Optional


try:
    import tiktoken

    _TOKEN_ENC = tiktoken.get_encoding("cl100k_base")
    HAS_TIKTOKEN = True
except ImportError:
    _TOKEN_ENC = None
    HAS_TIKTOKEN = False


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken or fallback."""
    if HAS_TIKTOKEN and _TOKEN_ENC is not None:
        return len(_TOKEN_ENC.encode(text))
    return len(text) // 4
