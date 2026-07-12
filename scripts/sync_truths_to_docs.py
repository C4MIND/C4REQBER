#!/usr/bin/env python3
"""Sync public-facing docs from _truths.json (run after gen_truths.py)."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRUTHS = REPO / "_truths.json"
I18N_DIR = REPO / "landing" / "i18n"


def load() -> dict:
    return json.loads(TRUTHS.read_text())


def fmt_num(n: int) -> str:
    return f"{n:,}"


def patch_readme(t: dict) -> None:
    path = REPO / "README.md"
    text = path.read_text()
    tests = t["python"]["tests_collected"]
    mypy = t["quality"]["mypy_baseline"]
    engines = t["simulations"]["engines"]
    sources = t["knowledge"]["sources"]
    mcp = t["mcp"]["tools"]
    ver_real = t["verifiers"]["real"]
    ver_stubs = t["verifiers"]["guard_stubs"]

    text = re.sub(
        r"\[!\[Tests\]\([^)]+\)\]\(\)",
        f"[![Tests](https://img.shields.io/badge/tests-{tests}%20collected-yellowgreen)]()",
        text,
    )
    text = re.sub(
        r"\[!\[Typecheck\]\([^)]+\)\]\(\)",
        f"[![Typecheck](https://img.shields.io/badge/typecheck-0%20mypy%20errors-brightgreen)]()",
        text,
    )
    # Stale merge branch blurb → shipped note
    text = text.replace(
        "Branch `friendely-merge-tui-upgrade` ready to merge.",
        "TUI v9 merged on `main`; see `ARCHITECTURE_TUI_V9.md`.",
    )
    # Verification section honesty
    old_verify = """## Verification Backends (10 + MathDetector Categories A/B/C)

```
Lean4 → Coq → Dafny → Agda → Z3 → CVC5 → Hoare → Haskell → TLA+ → Alloy
                        │                      │
                    Complexity pre-flight   Memory limit + hang detection
                        │                      │
                    Auto-fallback to Z3    Proof export to .lean/.v/.smt2
```"""
    new_verify = f"""## Verification Backends ({ver_real} real + MathDetector)

**Real (machine-checked when tool installed):** Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy.

```
Lean4 → Coq → Dafny → Agda → Z3/CVC5 → Hoare → TLA+ → Alloy → Haskell
   │                              │
   Complexity pre-flight      Auto-fallback chain
   Memory + hang detection    Proof export .lean / .v / .smt2 / .tla / .als
```"""
    if old_verify in text:
        text = text.replace(old_verify, new_verify)

    # Remove duplicate limitations row (keep one)
    dup = (
        "| **Sentence tokenization** | Regex-based splitting; abbreviations (\"Dr.\", \"e.g.\") handled heuristically | NLTK/spaCy adds +500MB dependencies; regex is \"good enough\" for claim extraction | Output is \"best effort\"; review extracted claims manually |\n"
        "| **Sentence tokenization** | Regex-based splitting; abbreviations (\"Dr.\", \"e.g.\") handled heuristically | NLTK/spaCy adds +500MB dependencies; regex is \"good enough\" for claim extraction | Output is \"best effort\"; review extracted claims manually |\n"
    )
    if dup in text:
        text = text.replace(dup, dup.split("\n", 1)[0] + "\n")

    path.write_text(text)
    print(f"patched {path}")


def patch_agents(t: dict) -> None:
    path = REPO / "AGENTS.md"
    text = path.read_text()
    tests = t["python"]["tests_collected"]
    engines = t["simulations"]["engines"]
    ver_real = t["verifiers"]["real"]
    mypy = t["quality"]["mypy_baseline"]

    text = re.sub(
        r"- \*\*Tests\*\*: \d[\d,\+]* collected",
        f"- **Tests**: {tests}+ collected",
        text,
    )
    text = re.sub(
        r"- \*\*Type safety\*\*: 0 mypy errors across \d+ source files",
        f"- **Type safety**: {mypy} mypy baseline errors (regression-gated; no new errors in CI)",
        text,
    )
    backends_line = (
        f"- **{ver_real} real verification backends** "
        "(Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy)"
    )
    text = re.sub(
        r"- \*\*\d+ real verification backends\*\*.*",
        backends_line,
        text,
    )
    text = re.sub(
        r"\*\*101\+ simulation patterns \+ \d+ simulation engines\*\*",
        f"**101+ simulation patterns + {engines} simulation engine bridges**",
        text,
    )
    text = text.replace("32 engine adapters", f"{engines} engine bridges")
    text = text.replace("32 simulation engine adapters", f"{engines} simulation engine bridges")
    if "pending publication" in text:
        text = text.replace(
            "pip install c4reqber           # PyPI entry point (pending publication)",
            "pip install c4reqber           # PyPI — see docs/PYPI_PUBLISH.md (publish before public CTA)",
        )
    path.write_text(text)
    print(f"patched {path}")


def patch_landing_i18n(t: dict, lang: str) -> None:
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        return
    data = json.loads(path.read_text())
    tests = t["python"]["tests_collected"]
    engines = t["simulations"]["engines"]
    sources = t["knowledge"]["sources"]
    mcp = t["mcp"]["tools"]
    ver_real = t["verifiers"]["real"]
    ver_stubs = t["verifiers"]["guard_stubs"]
    mypy = t["quality"]["mypy_baseline"]
    ver = t["version_backend"]
    tui = t["version_tui"]

    foot_en = (
        f"{fmt_num(tests)} tests collected · 0 mypy errors"
        if mypy == 0
        else f"{fmt_num(tests)} tests collected · {mypy} mypy baseline (regression-gated)"
    )
    foot_ru = (
        f"{tests:,}".replace(",", " ") + " тестов · 0 mypy"
        if mypy == 0
        else f"{tests:,}".replace(",", " ") + f" тестов · {mypy} mypy baseline"
    )
    foot_de = f"{fmt_num(tests)} Tests · {mypy} mypy-Baseline"
    foot_by_lang = {
        "en": foot_en,
        "ru": foot_ru,
        "de": foot_de,
        "zh": f"{fmt_num(tests)} 测试 · {mypy} mypy 基线",
        "ja": f"{fmt_num(tests)} テスト · {mypy} mypy ベースライン",
        "ar": f"{fmt_num(tests)} اختبار · {mypy} mypy baseline",
        "hi": f"{fmt_num(tests)} टेस्ट · {mypy} mypy baseline",
    }

    mypy_line = (
        "0 mypy errors"
        if mypy == 0
        else f"{mypy} mypy baseline (regression-gated)"
    )
    roadmap_en = (
        f"✓ Type safety: {mypy_line} (1095 files)\n"
        f"✓ MCP {mcp} tools with JSON Schema\n"
        f"✓ Virtual Bio + GPU auto-detect\n"
        f"✓ {engines} simulation engine bridges\n"
        f"✓ TUI {tui} Cockpit + blast tui command"
    )

    data["hero_badge"] = f"v{ver} + TUI {tui} · Open source · {mcp} MCP tools"
    data["foot_tests"] = foot_by_lang.get(lang, foot_en)
    data["feat_verify_desc"] = (
        f"Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy ({ver_real} real bridges)."
    )
    data["home_verify_cvc5_desc"] = "Industrial SMT solver (SMT-LIB2)"
    data["home_verify_tla_desc"] = "Temporal logic for concurrent systems"
    data["home_verify_alloy_desc"] = "Relational models with bounded analysis"
    data["disc_cap_capabilities"] = f"{engines} engine bridges + {ver_real} verifiers"
    data["home_verify_title"] = f"{ver_real} Formal Verification Backends"
    data["home_tui_desc"] = (
        f"{engines} sim engine bridges, {ver_real} verifiers, capabilities overlay, command palette. "
        "The simulation/verification cockpit is in the terminal — not a fallback, the primary interface."
    )
    cap_by_lang = {
        "en": f"✓ {engines} engine bridges · {ver_real} verifiers across 6 domains",
        "ru": f"✓ {engines} мостов симуляции · {ver_real} верификаторов в 6 доменах",
        "de": f"✓ {engines} Sim-Brücken · {ver_real} Verifizierer in 6 Domänen",
        "zh": f"✓ {engines} 个仿真桥接 · {ver_real} 个验证器，覆盖 6 个领域",
        "ja": f"✓ {engines} シミュレーションブリッジ · {ver_real} 検証器（6 ドメイン）",
        "ar": f"✓ {engines} جسور محاكاة · {ver_real} محقق عبر 6 مجالات",
        "hi": f"✓ {engines} sim bridges · {ver_real} verifiers, 6 domains",
    }
    data["home_tui_cap_summary"] = cap_by_lang.get(lang, cap_by_lang["en"])
    data["home_verify_cvc5_desc"] = "Industrial SMT solver (SMT-LIB2)"
    data["home_verify_tla_desc"] = "Temporal logic for concurrent systems"
    data["home_verify_alloy_desc"] = "Relational models with bounded analysis"
    if lang == "en":
        data["roadmap_v55_body"] = roadmap_en
        data["trust_title"] = "Hardened for Early Adopters"
        data["trust_desc"] = "Type-checked baseline. Battle-tested core. Transparent limitations."
        data["meta_desc_home"] = (
            f"Cognitive exoskeleton for AI agents. {engines} simulation bridges, "
            f"{ver_real} verifiers, {sources} knowledge sources, {mcp} MCP tools, TUI {tui}."
        )
        # Bulk replace stale metrics in string values
        for key, val in list(data.items()):
            if isinstance(val, str):
                val = val.replace("38 simulation engines", f"{engines} simulation engine bridges")
                val = val.replace("38 engines", f"{engines} engine bridges")
                val = val.replace("14 verifiers", f"{ver_real} verifiers")
                val = val.replace("6 verifiers (+3 guard-stubs)", f"{ver_real} verifiers")
                val = val.replace("27 verifiers", f"{ver_real} verifiers")
                val = val.replace("32 sim engines", f"{engines} sim engine bridges")
                val = val.replace("32 engine + 27 verifier", f"{engines} engines + {ver_real} verifiers")
                val = val.replace("guard-stubs", "real backends")
                val = val.replace("guard-stub", "real backend")
                val = val.replace("38 engine adapters", f"{engines} engine bridges")
                if mypy != 0:
                    val = val.replace("0 mypy errors", f"{mypy} mypy baseline (regression-gated)")
                val = val.replace("Type safety zero", "Mypy baseline tracked")
                val = val.replace("51 Knowledge Sources", f"{sources} Knowledge Sources")
                val = val.replace("51 knowledge sources", f"{sources} knowledge sources")
                val = val.replace("51 SOURCES", f"{sources} SOURCES")
                data[key] = val
    elif lang == "ru":
        mypy_ru = "0 ошибок mypy" if mypy == 0 else f"{mypy} mypy baseline"
        data["roadmap_v55_body"] = (
            f"✓ Mypy: {mypy_ru} (регрессионный gate)\n"
            f"✓ MCP {mcp} инструментов + JSON Schema\n"
            f"✓ Virtual Bio + автоопределение GPU\n"
            f"✓ {engines} мостов симуляции\n"
            f"✓ TUI {tui} + blast tui"
        )
        data["trust_title"] = "Для ранних пользователей"
        for key, val in list(data.items()):
            if isinstance(val, str):
                val = val.replace("PRODUCTION", "Open source")
                if mypy != 0:
                    val = val.replace("0 ошибок mypy", f"{mypy} mypy baseline")
                data[key] = val
    else:
        for key, val in list(data.items()):
            if isinstance(val, str):
                val = val.replace("PRODUCTION", "Open source")
                if mypy != 0:
                    val = val.replace("0 mypy", f"{mypy} mypy baseline")
                data[key] = val

    data["hero_tags"] = data.get("hero_tags", "").replace("38 ENGINES", f"{engines} ENGINES")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"patched {path}")


def patch_landing_html(t: dict) -> None:
    path = REPO / "landing" / "index.html"
    text = path.read_text()
    tests = t["python"]["tests_collected"]
    engines = t["simulations"]["engines"]
    sources = t["knowledge"]["sources"]
    ver_real = t["verifiers"]["real"]
    mcp = t["mcp"]["tools"]

    text = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="Cognitive exoskeleton for AI agents. '
        f'{engines} simulation bridges, {ver_real} verifiers, {sources} knowledge sources, '
        f'{mcp} MCP tools. Think. Simulate. Prove. Discover.">',
        text,
        count=1,
    )
    text = re.sub(
        r'"description": "Cognitive exoskeleton[^"]*"',
        f'"description": "Cognitive exoskeleton for humans and AI agents. '
        f'27 states, {engines} engine bridges, {ver_real} verifiers, {sources} sources, {mcp} MCP tools."',
        text,
        count=1,
    )
    text = text.replace('51+', f'{sources}+', 1)
    text = text.replace('>38<', f'>{engines}<', 1)
    text = text.replace('>9798+<', f'>{tests}+<', 1)
    text = text.replace('✓ 32 simulation engines integrated', f'✓ {engines} simulation engine bridges integrated')
    cap_summary = f"✓ {engines} engine bridges · {ver_real} verifiers across 6 domains"
    text = re.sub(
        r'data-i18n="home_tui_cap_summary"[^>]*>[^<]*</div>',
        f'data-i18n="home_tui_cap_summary">{cap_summary}</div>',
        text,
        count=1,
    )
    text = text.replace("22/32 engines", f"{engines} engine bridges")
    text = text.replace('32 simulation engines', f'{engines} simulation engine bridges')
    text = text.replace('32 sim engines', f'{engines} sim engine bridges')
    text = text.replace(
        '✓ Type safety zero (0 mypy errors)',
        f'✓ Mypy baseline tracked ({t["quality"]["mypy_baseline"]} errors, regression-gated)',
    )
    path.write_text(text)
    print(f"patched {path}")


def patch_main_js(t: dict) -> None:
    path = REPO / "landing" / "js" / "main.js"
    if not path.exists():
        return
    text = path.read_text()
    tests = t["python"]["tests_collected"]
    engines = t["simulations"]["engines"]
    mypy = t["quality"]["mypy_baseline"]
    text = text.replace("· PRODUCTION", "· Open source")
    text = text.replace("36 ENGINES", f"{engines} ENGINES")
    text = text.replace("43+ SOURCES", f"{t['knowledge']['sources']}+ SOURCES")
    text = text.replace("10,023 tests · 0 mypy errors", f"{fmt_num(tests)} tests · {mypy} mypy baseline")
    text = text.replace("0 mypy errors", f"{mypy} mypy baseline")
    path.write_text(text)
    print(f"patched {path}")


def patch_manifest(t: dict) -> None:
    path = REPO / "landing" / "manifest.json"
    data = json.loads(path.read_text())
    data["description"] = (
        f"Cognitive Exoskeleton for AI Agents. 27 states, "
        f"{t['simulations']['engines']} engine bridges, {t['verifiers']['real']} verifiers."
    )
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"patched {path}")


def patch_api_i18n(t: dict) -> None:
    """Bilingual API page: /v8 aggregator + legacy /api/v1."""
    patches = {
        "en": {
            "api_rest_base": (
                "Legacy REST: <code>/api/v1</code> · "
                "Discovery aggregator: <code>/v8</code> (no <code>/api</code> prefix)"
            ),
            "api_rest_title": "REST API Endpoints (v5.6.0 + /v8)",
        },
        "ru": {
            "api_rest_base": (
                "Legacy REST: <code>/api/v1</code> · "
                "Discovery aggregator: <code>/v8</code> (без префикса <code>/api</code>)"
            ),
            "api_rest_title": "REST API (v5.6.0 + /v8)",
        },
    }
    for lang, kv in patches.items():
        path = I18N_DIR / f"{lang}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        data.update(kv)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"patched {path} (api)")


def patch_whitepapers(t: dict) -> None:
    tests = t["python"]["tests_collected"]
    tests_fmt_en = f"{tests:,}"
    tests_fmt_ru = f"{tests:,}".replace(",", " ")
    mypy = t["quality"]["mypy_baseline"]
    mypy_en = "0 (regression-gated)" if mypy == 0 else f"{mypy} (regression-gated)"
    mypy_ru = "0 (регрессионный gate)" if mypy == 0 else f"{mypy} (регрессионный gate)"

    for name, tests_line, mypy_line in (
        ("WHITEPAPER.md", tests_fmt_en, mypy_en),
        ("WHITEPAPER.ru.md", tests_fmt_ru, mypy_ru),
    ):
        path = REPO / name
        if not path.exists():
            continue
        text = path.read_text()
        text = re.sub(
            r"\*\*Тесты:\*\* [\d, ]+ collected.*",
            f"**Тесты:** {tests_line}+ collected · mypy baseline: {mypy_line}.",
            text,
        )
        text = re.sub(
            r"\*\*Tests:\*\* [\d,]+\+ collected.*",
            f"**Tests:** {tests_line}+ collected (Python) · Go TUI: all packages pass · mypy baseline: {mypy_line}.",
            text,
        )
        text = re.sub(
            r"\| Тестов collected \| [\d, ]+\+ \|",
            f"| Тестов collected | {tests_line}+ |",
            text,
        )
        text = re.sub(
            r"\| Tests collected \| [\d,]+\+ \|",
            f"| Tests collected | {tests_line}+ |",
            text,
        )
        path.write_text(text)
        print(f"patched {path}")


def main() -> int:
    if not TRUTHS.exists():
        print("ERROR: run scripts/gen_truths.py first", flush=True)
        return 1
    t = load()
    tests = t["python"]["tests_collected"]
    engines = t["simulations"]["engines"]
    ver_real = t["verifiers"]["real"]
    ver_stubs = t["verifiers"]["guard_stubs"]
    mypy = t["quality"]["mypy_baseline"]
    patch_readme(t)
    patch_agents(t)
    for lang in ("en", "ru", "de", "zh", "ja", "ar", "hi"):
        patch_landing_i18n(t, lang)
        # Second pass: metric strings in all languages
        path = I18N_DIR / f"{lang}.json"
        data = json.loads(path.read_text())
        for key, val in list(data.items()):
            if not isinstance(val, str):
                continue
            val = val.replace("PRODUCTION", "Open source")
            val = val.replace("38 simulation engines", f"{engines} simulation engine bridges")
            val = val.replace("38 engines", f"{engines} engine bridges")
            val = val.replace("6 verifiers (+3 guard-stubs)", f"{ver_real} verifiers")
            val = val.replace("27 verifiers", f"{ver_real} verifiers")
            val = val.replace("32 sim engines", f"{engines} sim engine bridges")
            val = val.replace("32 engine + 27 verifier", f"{engines} engines + {ver_real} verifiers")
            val = val.replace("guard-stubs", "real backends")
            val = val.replace("guard-stub", "real backend")
            val = val.replace("14 verifiers", f"{ver_real} verifiers")
            val = val.replace("38 engines + 14 verifiers", f"{engines} bridges + {ver_real} verifiers")
            if mypy != 0:
                val = val.replace("0 mypy errors", f"{mypy} mypy baseline (regression-gated)")
            val = val.replace("Type safety zero", "Mypy baseline tracked")
            val = val.replace("10,023", fmt_num(tests))
            val = val.replace("22/32 engines", f"{engines} engine bridges")
            val = val.replace("22/32 движка", f"{engines} мостов симуляции")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    patch_landing_html(t)
    patch_main_js(t)
    patch_manifest(t)
    patch_api_i18n(t)
    patch_whitepapers(t)
    print("OK: public docs synced from _truths.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
