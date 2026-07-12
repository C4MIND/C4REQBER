#!/usr/bin/env python3
"""Sync landing i18n files: ensure every locale has all keys from en.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "landing" / "i18n"
LANGS = ["en", "ru", "zh", "ja", "de", "ar", "hi"]

# Keys intentionally identical to English (brands, commands, badges)
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
    path = I18N / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def save(name: str, data: dict[str, str]) -> None:
    path = I18N / f"{name}.json"
    ordered = {k: data[k] for k in sorted(data)}
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_all() -> int:
    en = load("en")
    errors = 0
    for lang in LANGS:
        if lang == "en":
            continue
        cur = load(lang) if (I18N / f"{lang}.json").exists() else {}
        out: dict[str, str] = {}
        missing = []
        same_en = []
        for key, en_val in en.items():
            if key in cur:
                out[key] = cur[key]
            else:
                out[key] = en_val
                missing.append(key)
            if lang != "en" and out[key] == en_val and key not in KEEP_EN:
                same_en.append(key)
        save(lang, out)
        print(f"{lang}: keys={len(out)} missing_added={len(missing)} still_en={len(same_en)}")
        if same_en:
            errors += len(same_en)
    return errors


def report() -> None:
    en = load("en")
    print(f"en keys: {len(en)}")
    for lang in LANGS:
        if lang == "en":
            continue
        cur = load(lang)
        missing = [k for k in en if k not in cur]
        same = [k for k in en if k in cur and cur[k] == en[k] and k not in KEEP_EN]
        print(f"  {lang}: total={len(cur)} missing={len(missing)} untranslated={len(same)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "report":
        report()
    else:
        remaining = sync_all()
        print(f"untranslated total (excl KEEP_EN): {remaining}")
        sys.exit(1 if remaining else 0)
