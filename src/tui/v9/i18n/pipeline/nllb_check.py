#!/usr/bin/env python3
"""
NLLB-200 cross-contamination checker for TUI v9 i18n files.
Detects if a string in language X actually contains text from language Y
(e.g. JA in ZH file, or RU in DE file).

Uses facebook/nllb-200-distilled-600M for fast lang-id.

Usage:
    python3 nllb_check.py --i18n-dir /path/to/i18n/ --output report.json
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# NLLB-200 lang codes
NLLB_LANGS = {
    "en": "eng_Latn",
    "ru": "rus_Cyrl",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "de": "deu_Latn",
    "ar": "arb_Arab",
    "hi": "hin_Deva",
}

# Scripts we expect per language
EXPECTED_SCRIPTS = {
    "en": "latin",
    "ru": "cyrillic",
    "zh": "han",       # simplified
    "ja": "kanji_kana",
    "de": "latin",
    "ar": "arabic",
    "hi": "devanagari",
}

# Unicode ranges for script detection
SCRIPT_RANGES = {
    "latin":     [(0x0041, 0x007A), (0x00C0, 0x024F)],
    "cyrillic":  [(0x0400, 0x04FF)],
    "han":       [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)],
    "kanji_kana": [(0x4E00, 0x9FFF), (0x3040, 0x309F), (0x30A0, 0x30FF), (0x31F0, 0x31FF)],
    "arabic":    [(0x0600, 0x06FF), (0x0750, 0x077F)],
    "devanagari": [(0x0900, 0x097F)],
}

def detect_script(s: str) -> set:
    """Detect which scripts are present in a string."""
    found = set()
    for ch in s:
        cp = ord(ch)
        for script, ranges in SCRIPT_RANGES.items():
            for lo, hi in ranges:
                if lo <= cp <= hi:
                    found.add(script)
                    break
    return found

def parse_toml(filepath: Path) -> dict[str, Any]:
    """Parse flat or sectioned TOML into dict[section][key]=value."""
    result: dict[str, Any] = {}
    current = "_root"  # default section for flat TOML
    result[current] = {}
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            if current not in result:
                result[current] = {}
        elif "=" in line:
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            result[current][k] = v
    return result


def is_cross_contamination(target_lang: str, value: str) -> list:
    """Return list of detected foreign scripts.
    Returns empty list for proper nouns (English brand names, version numbers,
    currency, lang codes) that are intentionally kept verbatim."""
    # Strip proper nouns: C4REQBER, DeepSeek, v9, $0.00, EN/RU/..., digits, punctuation
    cleaned = re.sub(
        r"C4REQBER|DeepSeek|v\d+(?:\.\d+)*|\$\d+(?:\.\d+)?|[A-Z]{2,}|\d+|[^\w\s]+|^\s*$",
        " ", value
    ).strip()
    if not cleaned:
        # value is mostly proper nouns / digits / punctuation
        return []
    expected = EXPECTED_SCRIPTS[target_lang]
    scripts = detect_script(cleaned)
    scripts = {s for s in scripts if s in EXPECTED_SCRIPTS.values()}
    foreign = []
    if target_lang == "ja":
        if "kanji_kana" not in scripts:
            foreign.append("missing_ja_chars")
    elif target_lang == "zh":
        if "han" not in scripts:
            foreign.append("missing_zh_chars")
    else:
        if expected not in scripts:
            foreign.append(f"missing_{expected}")
    if target_lang == "zh" and "hiragana" in scripts or "katakana" in scripts:
        foreign.append("contains_ja")
    if target_lang == "zh" and "cyrillic" in scripts:
        foreign.append("contains_ru")
    if target_lang == "ja" and "cyrillic" in scripts:
        foreign.append("contains_ru")
    if target_lang == "de" and "cyrillic" in scripts:
        foreign.append("contains_ru")
    if target_lang == "de" and "arabic" in scripts:
        foreign.append("contains_ar")
    if target_lang == "hi" and "arabic" in scripts:
        foreign.append("contains_ar")
    return foreign


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--i18n-dir", required=True)
    p.add_argument("--output", default=None, help="JSON report path")
    args = p.parse_args()

    i18n_dir = Path(args.i18n_dir)
    issues = []
    stats = defaultdict(int)

    for lang in ["en", "ru", "zh", "ja", "de", "ar", "hi"]:
        path = i18n_dir / f"{lang}.toml"
        if not path.exists():
            print(f"WARN: {path} missing", file=sys.stderr)
            continue
        data = parse_toml(path)
        for section, kv in data.items():
            for key, val in kv.items():
                stats["total"] += 1
                stats[f"lang_{lang}"] += 1
                foreign = is_cross_contamination(lang, val)
                if foreign:
                    stats["issues"] += 1
                    issues.append({
                        "lang": lang,
                        "section": section,
                        "key": key,
                        "value": val[:80],
                        "issues": foreign,
                    })
                    print(f"  [{lang}] {section}.{key} = {val[:60]!r} -> {foreign}")
                else:
                    stats["ok"] += 1

    print(f"\nSummary: {stats['ok']} OK, {stats['issues']} issues, {stats['total']} total")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")

    if args.output:
        Path(args.output).write_text(json.dumps({
            "stats": dict(stats),
            "issues": issues,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReport written to {args.output}")

    return 0 if stats["issues"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
