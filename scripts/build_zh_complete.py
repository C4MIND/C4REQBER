#!/usr/bin/env python3
"""Build complete landing/i18n/zh.json from en.json + existing overrides + translations."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "landing" / "i18n"

KEEP_EN = {
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
}


def load(name: str) -> dict[str, str]:
    return json.loads((I18N / f"{name}.json").read_text(encoding="utf-8"))


def main() -> None:
    en = load("en")
    existing_zh = load("zh") if (I18N / "zh.json").exists() else {}
    translations = json.loads(
        (Path(__file__).parent / "zh_translations.json").read_text(encoding="utf-8")
    )

    out: dict[str, str] = {}
    for key in en:
        if key in existing_zh and existing_zh[key] != en[key]:
            out[key] = existing_zh[key]
        elif key in KEEP_EN:
            out[key] = en[key]
        elif key in translations:
            out[key] = translations[key]
        else:
            raise KeyError(f"Missing translation for key: {key}")

    ordered = {k: out[k] for k in sorted(out)}
    (I18N / "zh.json").write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    untranslated = [k for k in en if out[k] == en[k] and k not in KEEP_EN and en[k] != ""]
    print(f"keys: {len(ordered)}")
    print(f"untranslated (excl KEEP_EN, empty): {len(untranslated)}")
    if untranslated:
        print("still english:", untranslated[:20], "..." if len(untranslated) > 20 else "")


if __name__ == "__main__":
    main()
