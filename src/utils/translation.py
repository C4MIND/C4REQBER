# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Translation pipeline — user language → English prompt → pipeline → English result → user language output.

Architecture:
1. User types in their language (ru/zh/ja/de/ar/hi)
2. System detects language, translates prompt to English via cheapest LLM
3. Pipeline runs in English (science works best in EN)
4. Result generated in English
5. Optional: translate result back to user's language

Usage:
    blast translate "проверить гипотезу о квантовой запутанности" --to en
    blast turbo "..." --translate-to ru  # auto-translate final dissertation
"""
from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "de": "German",
    "ar": "Arabic",
    "hi": "Hindi",
    "fr": "French",
    "es": "Spanish",
}


def detect_language(text: str) -> str:
    """Quick language detection via character set + common words."""
    # Cyrillic → ru
    if any(0x0400 <= ord(c) <= 0x04FF for c in text):
        return "ru"
    # CJK → zh/ja
    if any(0x4E00 <= ord(c) <= 0x9FFF for c in text):
        if any(0x3040 <= ord(c) <= 0x309F for c in text):
            return "ja"
        return "zh"
    # Arabic
    if any(0x0600 <= ord(c) <= 0x06FF for c in text):
        return "ar"
    # Devanagari
    if any(0x0900 <= ord(c) <= 0x097F for c in text):
        return "hi"
    # German umlauts
    if any(c in "äöüß" for c in text.lower()):
        return "de"
    return "en"


def translate(text: str, target_lang: str = "en", source_lang: str = "") -> str:
    """Translate text using cheapest LLM."""
    if not text.strip():
        return text

    detected = source_lang or detect_language(text)
    if detected == target_lang:
        return text

    prompt = (
        f"Translate the following text from {LANGUAGE_NAMES.get(detected, detected)} "
        f"to {LANGUAGE_NAMES.get(target_lang, target_lang)}. "
        f"Preserve ALL scientific terminology, equations, and citations exactly. "
        f"Output ONLY the translation, no commentary.\n\n{text}"
    )

    try:
        import os

        import httpx
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            return text

        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": min(len(text) * 2, 8000),
                    "temperature": 0.1,
                },
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]  # type: ignore[no-any-return]
    except Exception as e:
        logger.debug("Translation failed: %s", e)

    return text


def translate_auto(prompt: str) -> str:
    """Auto-detect language → translate to English if needed."""
    detected = detect_language(prompt)
    if detected == "en":
        return prompt
    logger.info("Detected language: %s → translating to English", LANGUAGE_NAMES.get(detected, detected))
    translated = translate(prompt, target_lang="en", source_lang=detected)
    if translated != prompt:
        logger.info("Translated prompt: %s...", translated[:80])
    return translated
