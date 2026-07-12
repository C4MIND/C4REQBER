#!/usr/bin/env python3
"""Generate complete landing/i18n/ja.json from en.json + existing JA + translation overrides."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "landing" / "i18n"
JP_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]")

KEEP_EN_VALUES = {
    "pip install c4reqber",
    "NOT_SHIFTED",
    "SHIFTED",
    "ALREADY_SHIFTED",
}

# Load batch translations from companion file
TRANSLATIONS_PATH = Path(__file__).parent / "ja_translations.json"


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_good(existing: dict[str, str], en: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in existing.items():
        if key in en and value != en[key] and JP_RE.search(value):
            out[key] = value
    return out


def main() -> None:
    en = load_json(I18N / "en.json")
    existing = load_json(I18N / "ja.json")
    translations = load_json(TRANSLATIONS_PATH)

    merged = merge_good(existing, en)
    merged.update(translations)

    # Fallback: use English for keys intentionally identical (brands, badges, CLI)
    for key, en_val in en.items():
        if key not in merged:
            merged[key] = en_val

    missing = [k for k in en if k not in merged]
    if missing:
        raise SystemExit(f"Missing {len(missing)} translations: {missing[:20]}...")

    extra = set(merged) - set(en)
    if extra:
        raise SystemExit(f"Extra keys not in en.json: {sorted(extra)[:10]}")

    out = {k: merged[k] for k in sorted(en)}
    (I18N / "ja.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    untranslated = [
        k
        for k in en
        if out[k] == en[k]
        and k
        not in {
            "hero_cta_primary",
            "hero_install",
            "hero_cta_secondary",
            "gitlab_badge",
            "gal_tab_markdown",
            "gal_tab_json",
            "home_paradigm_badge_shifted",
            "home_paradigm_badge_shift",
            "home_paradigm_badge_not_shifted",
            "home_mcp_c4_export_desc",
            "home_mcp_blast_solve_desc",
            "api_tier_pro",
            "api_tier_enterprise",
            "api_sdk_title",
            "breadcrumb_api",
            "doc_faq_title",
            "gpu_cat_cfd",
            "gpu_cat_mlmd",
            "mcpdoc_claude_title",
            "hw_gpu",
            "comp_wasm",
            "comp_os",
            "c4_os2",
            "roadmap_v56",
            "roadmap_v57",
            "gs_mcp_verify",
            "gs_mcp_export",
            "splash_easter_2",
            "feat_verify_desc",
            "ref_notice",
        }
        and en[k] != ""
    ]
    print(f"Wrote {len(out)} keys to {I18N / 'ja.json'}")
    print(f"Untranslated (excl KEEP_EN, empty): {len(untranslated)}")
    if untranslated:
        print("Still English:", untranslated[:15], "..." if len(untranslated) > 15 else "")


if __name__ == "__main__":
    main()
