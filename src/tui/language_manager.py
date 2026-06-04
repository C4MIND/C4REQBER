"""
TUI: Language Manager
Language handling for C4TUI.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def make_language_manager(lang: str, LANG_ORDER: list[str], TRANSLATIONS: dict[str, dict[str, str]], LANG_FILE: Path) -> Any:
    """Create a language manager object."""

    class LanguageManager:
        """LanguageManager."""
        def __init__(self, lang: str) -> None:
            self._lang = self._load_lang(lang)
            self._apply_rtl()

        def _load_lang(self, cli_lang: str) -> str:
            if cli_lang and cli_lang in TRANSLATIONS:
                return cli_lang
            if LANG_FILE.exists():
                saved = LANG_FILE.read_text().strip()
                if saved in TRANSLATIONS:
                    return saved
            return "en"

        def _save_lang(self) -> None:
            LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
            LANG_FILE.write_text(self._lang)

        def _cycle_lang(self) -> None:
            idx = LANG_ORDER.index(self._lang) if self._lang in LANG_ORDER else 0
            self._lang = LANG_ORDER[(idx + 1) % len(LANG_ORDER)]
            self._save_lang()
            self._apply_rtl()

        def _apply_rtl(self) -> None:
            from rich.console import Console
            console = Console()
            if self._lang == "ar":
                console.set_rtl(True)  # type: ignore[attr-defined]
            else:
                try:
                    console.set_rtl(False)  # type: ignore[attr-defined]
                except (ImportError, AttributeError, OSError, ValueError):
                    pass

        def t(self, key: str, default: str = "") -> str:
            result = TRANSLATIONS.get(self._lang, TRANSLATIONS["en"]).get(key, key)
            return result if result != key else default or key

        def get_lang(self) -> str:
            return self._lang

        def set_lang(self, lang: str) -> None:
            """Set lang."""
            self._lang = lang
            self._save_lang()
            self._apply_rtl()

    return LanguageManager(lang)
