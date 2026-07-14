from __future__ import annotations

from utils.translation import detect_language, translate


class TestDetectLanguage:
    def test_cyrillic_returns_ru(self):
        assert detect_language("привет мир") == "ru"

    def test_cjk_returns_zh(self):
        assert detect_language("量子力学") == "zh"

    def test_arabic_returns_ar(self):
        assert detect_language("السلام عليكم") == "ar"

    def test_english_returns_en(self):
        assert detect_language("quantum entanglement") == "en"

    def test_hiragana_returns_ja(self):
        assert detect_language("こんにちは量子") == "ja"

    def test_german_umlaut_returns_de(self):
        assert detect_language("Straße und Bücher") == "de"

    def test_devanagari_returns_hi(self):
        assert detect_language("नमस्ते दुनिया") == "hi"


class TestTranslate:
    def test_same_language_noop(self):
        result = translate("hello world", target_lang="en", source_lang="en")
        assert result == "hello world"

    def test_same_language_auto_detected_noop(self):
        result = translate("hello world", target_lang="en")
        assert result == "hello world"

    def test_empty_text_returns_empty(self):
        assert translate("", target_lang="ru") == ""
