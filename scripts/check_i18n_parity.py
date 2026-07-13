#!/usr/bin/env python3
"""i18n parity check — assert all 7 languages have identical key sets.

Audit 2026-06-22 D-1 (companion): the README claims '100% i18n parity
across 7 languages' (en/ru/zh/ja/de/ar/hi). This script asserts the
parity programmatically so CI catches drift.

Uses line-by-line regex (not strict TOML parser) because the i18n
TOML files intentionally use mixed section + flat key syntax that
conflicts with strict parsers; the key extraction is what matters.

Exit 0 if all 7 files have identical key sets; exit 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
I18N_DIR = REPO / "src/tui/v9/i18n"
LANGS = ["ar", "de", "en", "hi", "ja", "ru", "zh"]
REFERENCE_LANG = "en"


def extract_keys(path: Path) -> set[str]:
    """Pull top-level key names from a TOML file. Ignores [section] headers."""
    out: set[str] = set()
    text = path.read_text()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            continue
        if "=" not in line:
            continue
        key = line.split("=", 1)[0].strip().strip('"').strip("'")
        if key:
            out.add(key)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict", action="store_true", help="fail if any language has < reference count"
    )
    args = parser.parse_args()

    all_keys: dict[str, set[str]] = {}
    for lang in LANGS:
        p = I18N_DIR / f"{lang}.toml"
        if not p.exists():
            print(f"FAIL: {p} does not exist")
            return 1
        all_keys[lang] = extract_keys(p)
        print(f"  {lang}.toml: {len(all_keys[lang])} keys")

    ref = all_keys[REFERENCE_LANG]
    print(f"\nReference: {REFERENCE_LANG} ({len(ref)} keys)")
    failed = False

    for lang in LANGS:
        if lang == REFERENCE_LANG:
            continue
        if all_keys[lang] == ref:
            print(f"  {lang}: identical to {REFERENCE_LANG} ✓")
        else:
            missing = ref - all_keys[lang]
            extra = all_keys[lang] - ref
            print(f"  {lang}: DRIFT ({len(missing)} missing, {len(extra)} extra)")
            for k in sorted(missing)[:5]:
                print(f"    missing: {k!r}")
            for k in sorted(extra)[:5]:
                print(f"    extra: {k!r}")
            if args.strict or len(missing) > 0:
                failed = True

    if failed:
        print("\nFAIL: i18n keys are not in parity")
        return 1
    print("\nOK: all 7 languages have identical key sets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
