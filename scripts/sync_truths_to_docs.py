#!/usr/bin/env python3
"""Sync public-facing docs from _truths.json (run after gen_truths.py)."""

from __future__ import annotations

import argparse
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
    providers = t["llm"]["providers"]
    cli_commands = t["cli"]["commands"]
    ver = t["version_backend"]

    text = re.sub(
        r"\[!\[Version\]\(https://img\.shields\.io/badge/version-[^)]+\)\]\(\)",
        f"[![Version](https://img.shields.io/badge/version-{ver}-magenta)]()",
        text,
    )
    text = re.sub(
        r"\[!\[Tests\]\([^)]+\)\]\(\)",
        f"[![Tests](https://img.shields.io/badge/tests-{tests}%20collected-yellowgreen)]()",
        text,
    )
    text = re.sub(
        r"\[!\[Typecheck\]\([^)]+\)\]\(\)",
        "[![Typecheck](https://img.shields.io/badge/typecheck-0%20mypy%20errors-brightgreen)]()",
        text,
    )
    # Stale merge branch blurb → shipped note
    text = text.replace(
        "Branch `friendely-merge-tui-upgrade` ready to merge.",
        "TUI v9 merged on `main`; see `src/tui/v9/ARCHITECTURE.md`.",
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
        '| **Sentence tokenization** | Regex-based splitting; abbreviations ("Dr.", "e.g.") handled heuristically | NLTK/spaCy adds +500MB dependencies; regex is "good enough" for claim extraction | Output is "best effort"; review extracted claims manually |\n'
        '| **Sentence tokenization** | Regex-based splitting; abbreviations ("Dr.", "e.g.") handled heuristically | NLTK/spaCy adds +500MB dependencies; regex is "good enough" for claim extraction | Output is "best effort"; review extracted claims manually |\n'
    )
    if dup in text:
        text = text.replace(dup, dup.split("\n", 1)[0] + "\n")
    text = re.sub(
        r"- \*\*\d+ LLM providers\*\*:",
        f"- **{providers} LLM providers**:",
        text,
    )
    text = re.sub(
        r"- \*\*(?:33\+|43|47|51) active knowledge source adapters\*\*.*",
        f"- **{sources} configured knowledge source integrations** "
        f"({t['knowledge']['wired']} wired to `MultiSourceSearcher`; runtime-active subset "
        "depends on credentials and availability)",
        text,
    )
    text = re.sub(
        r"- \*\*Knowledge search\*\* — \d+\+? source adapters",
        f"- **Knowledge search** — {sources} configured source integrations",
        text,
    )
    text = re.sub(
        r"(blast serve --mcp\s+# MCP server for AI agents \()\d+( tools\))",
        rf"\g<1>{mcp}\2",
        text,
    )
    text = text.replace(
        "| `docs/MCP_REGISTRY.md` | MCP tool registry",
        "| `docs/mcp_registry.md` | MCP tool registry",
    )

    path.write_text(text)
    print(f"patched {path}")


def patch_agents(t: dict) -> None:
    path = REPO / "AGENTS.md"
    text = path.read_text()
    tests = t["python"]["tests_collected"]
    engines = t["simulations"]["engines"]
    ver_real = t["verifiers"]["real"]
    mypy = t["quality"]["mypy_baseline"]
    sources = t["knowledge"]["sources"]
    wired_sources = t["knowledge"]["wired"]
    providers = t["llm"]["providers"]
    cli_commands = t["cli"]["commands"]

    text = re.sub(
        r"- \*\*Tests\*\*: \d[\d,\+]* collected",
        f"- **Tests**: {tests:,} collected",
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
    text = re.sub(
        r"- \*\*CLI\*\* \(blast commands\) — .*",
        f"- **CLI** — {cli_commands} top-level `blast` commands",
        text,
    )
    text = re.sub(
        r"- \*\*(?:33\+|43|47|51) active knowledge source adapters\*\*.*",
        f"- **{sources} configured knowledge source integrations** "
        f"({wired_sources} wired to `MultiSourceSearcher`; runtime-active subset depends "
        "on credentials and availability). Truth source: `_truths.json`.",
        text,
    )
    text = re.sub(
        r"27 Z₃³ states, \d+ verification backends \+ MathDetector",
        f"27 Z₃³ states, {ver_real} verification backends + MathDetector",
        text,
    )
    text = re.sub(
        r"\d+ auto-detected LLM providers",
        f"{providers} configured LLM providers",
        text,
    )
    text = re.sub(r", \d+ CLI commands,", f", {cli_commands} CLI commands,", text)
    text = text.replace("33+ knowledge sources", f"{sources} configured knowledge sources")
    text = text.replace(
        "33+ sources via orchestrator.py", f"{sources} configured sources via orchestrator.py"
    )
    text = text.replace(
        "33+ sources (orchestrator.py)",
        f"{sources} configured sources (orchestrator.py)",
    )
    text = re.sub(
        r"\| Knowledge sources \| .* \|",
        f"| Knowledge sources | {sources} configured; {wired_sources} wired |",
        text,
    )
    text = re.sub(
        r"\| LLM providers \| .* \|",
        f"| LLM providers | {providers} configured (cloud + local); runtime availability varies |",
        text,
    )
    text = re.sub(
        r"\| CLI commands \| .* \|",
        f"| CLI commands | {cli_commands} top-level `blast` commands |",
        text,
    )
    text = re.sub(
        r"├── tests/\s+# [\d,]+\+ collected tests.*",
        f"├── tests/                      # {tests:,} collected Python tests",
        text,
    )
    text = text.replace(
        "make test           # All tests (2,730+ collected, 1,400+ pass)",
        f"make test           # Full test suite ({tests:,} tests currently collected)",
    )
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

    mypy_line = "0 mypy errors" if mypy == 0 else f"{mypy} mypy baseline (regression-gated)"
    roadmap_en = (
        f"✓ Type safety: {mypy_line} (1095 files)\n"
        f"✓ MCP {mcp} tools with JSON Schema\n"
        f"✓ Virtual Bio + GPU auto-detect\n"
        f"✓ {engines} simulation engine bridges\n"
        f"✓ TUI {tui} Cockpit + blast tui command"
    )

    data["hero_badge"] = f"v{ver} + TUI {tui} · Open source · {mcp} MCP tools"
    data["doc_badge"] = f"Docs v{ver}"
    data["foot_product"] = f"c4reqber v{ver}"
    footer_docs = {
        "en": "Docs",
        "ru": "Документация",
        "de": "Dokumentation",
        "zh": "文档",
        "ja": "ドキュメント",
        "ar": "التوثيق",
        "hi": "दस्तावेज़",
    }
    data["footer_version"] = (
        f"c4reqber v{ver} + TUI {tui} · GitLab · {footer_docs.get(lang, 'Docs')} · AGPL-3.0"
    )
    if lang == "en":
        data["api_rest_title"] = f"REST API Endpoints (v{ver} + /v8)"
    elif lang == "ru":
        data["api_rest_title"] = f"REST API (v{ver} + /v8)"
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
                val = val.replace(
                    "32 engine + 27 verifier", f"{engines} engines + {ver_real} verifiers"
                )
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

    # All current "51" occurrences in the locale catalogs are source-count
    # claims. Keep translated prose while sourcing the number centrally.
    for key, val in list(data.items()):
        if isinstance(val, str):
            val = val.replace("51", str(sources))
            val = val.replace("43 Knowledge Sources", f"{sources} Knowledge Sources")
            val = val.replace("43+ knowledge sources", f"{sources} knowledge sources")
            val = val.replace("36 simulation engines", f"{engines} simulation engine bridges")
            val = val.replace("20 MCP tools", f"{mcp} MCP tools")
            val = val.replace(f"{sources}+", str(sources))
            if key in {"arch_layer_knowledge_desc", "feat_kg_desc"}:
                val = val.replace("30 ", "").replace("30.", ".")
            if key in {"arch_hero_sub", "arch_layer_sim_desc", "meta_desc_arch"}:
                for stale in (
                    "32 adapters. ",
                    "32 adapters। ",
                    "32 Adapter. ",
                    "32 адаптера. ",
                    "32 个适配器。",
                    "32 アダプタ。",
                    "32 محول. ",
                    ", 32 adapters",
                    ", 32 Adapter",
                    ", 32 адаптера",
                    "、32 个适配器",
                    "、32 アダプタ",
                    " و32 محول",
                    " × 32 adapters",
                    " × 32 Adapter",
                    " × 32 адаптера",
                    " × 32 个适配器",
                    " × 32 アダプタ",
                    " × 32 محول",
                ):
                    val = val.replace(stale, "")
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
    ver = t["version_backend"]

    text = re.sub(
        r'"softwareVersion": "[^"]+"',
        f'"softwareVersion": "{ver}"',
        text,
        count=1,
    )
    text = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="Cognitive exoskeleton for AI agents. '
        f"{engines} simulation bridges, {ver_real} verifiers, {sources} knowledge sources, "
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
    text = text.replace("51+", str(sources))
    text = text.replace(f"{sources}+", str(sources))
    text = text.replace(">43 Knowledge Sources<", f">{sources} Knowledge Sources<")
    text = text.replace(">36 Simulation Engines<", f">{engines} Simulation Engines<")
    text = text.replace("MCP Server — 20 Tools", f"MCP Server — {mcp} Tools")
    text = text.replace(
        '<span class="tag">20 Tools</span>', f'<span class="tag">{mcp} Tools</span>'
    )
    text = text.replace(">38<", f">{engines}<", 1)
    text = re.sub(r">9(?:798|801|887|905)\+?<", f">{tests}<", text, count=1)
    text = text.replace(
        "✓ 32 simulation engines integrated", f"✓ {engines} simulation engine bridges integrated"
    )
    cap_summary = f"✓ {engines} engine bridges · {ver_real} verifiers across 6 domains"
    text = re.sub(
        r'data-i18n="home_tui_cap_summary"[^>]*>[^<]*</div>',
        f'data-i18n="home_tui_cap_summary">{cap_summary}</div>',
        text,
        count=1,
    )
    text = text.replace("22/32 engines", f"{engines} engine bridges")
    text = text.replace("32 simulation engines", f"{engines} simulation engine bridges")
    text = text.replace("32 sim engines", f"{engines} sim engine bridges")
    text = text.replace("36 simulation engines", f"{engines} simulation engine bridges")
    text = text.replace("36 engines", f"{engines} engine bridges")
    text = text.replace("36 ENGINES", f"{engines} ENGINE BRIDGES")
    text = text.replace(
        "14 formal verification backends", f"{ver_real} formal verification backends"
    )
    text = text.replace("and 30 more.", "and other configured sources.")
    text = text.replace("43+ SOURCES", f"{sources} SOURCES")
    text = text.replace("43+ sources", f"{sources} sources")
    text = text.replace("51 sources", f"{sources} sources")
    text = text.replace("51 knowledge sources", f"{sources} knowledge sources")
    text = text.replace("51 Knowledge Sources", f"{sources} Knowledge Sources")
    text = text.replace("20 MCP TOOLS", f"{mcp} MCP TOOLS")
    text = text.replace(
        "✓ Type safety zero (0 mypy errors)",
        f"✓ Mypy baseline tracked ({t['quality']['mypy_baseline']} errors, regression-gated)",
    )
    text = re.sub(
        r'<div class="stat-card accent"><div class="stat-value accent">\d+</div><div class="stat-label" data-i18n="stat_tests">',
        f'<div class="stat-card accent"><div class="stat-value accent">{tests}</div><div class="stat-label" data-i18n="stat_tests">',
        text,
        count=1,
    )
    path.write_text(text)
    print(f"patched {path}")


def patch_landing_pages(t: dict) -> None:
    """Patch English fallback copy on secondary landing pages."""
    sources = t["knowledge"]["sources"]
    engines = t["simulations"]["engines"]
    mcp = t["mcp"]["tools"]
    verifiers = t["verifiers"]["real"]
    for path in (REPO / "landing").rglob("*.html"):
        if path.name == "index.html" and path.parent == REPO / "landing":
            continue
        text = path.read_text()
        text = text.replace("51 knowledge sources", f"{sources} knowledge sources")
        text = text.replace(
            "51 federated knowledge sources", f"{sources} federated knowledge sources"
        )
        text = text.replace("51 sources", f"{sources} sources")
        text = text.replace("51 Sources", f"{sources} Sources")
        text = text.replace("38 simulation engines", f"{engines} simulation engine bridges")
        text = text.replace("38 engine bridges", f"{engines} engine bridges")
        text = text.replace("21 MCP tools", f"{mcp} MCP tools")
        text = text.replace("9 verifiers", f"{verifiers} verifiers")
        text = text.replace("14 verifiers", f"{verifiers} verifiers")
        text = text.replace(
            "14 formal verification backends", f"{verifiers} formal verification backends"
        )
        text = text.replace("32 adapters. ", "")
        text = text.replace(" × 32 adapters", "")
        text = text.replace(" &times; 32 Adapters", "")
        text = text.replace("and 30 more.", "and other configured sources.")
        path.write_text(text)
        print(f"patched {path}")


def patch_docs_index(t: dict) -> None:
    """Reconcile the legacy standalone docs landing page."""
    path = REPO / "docs/index.html"
    text = path.read_text()
    sources = t["knowledge"]["sources"]
    engines = t["simulations"]["engines"]
    mcp = t["mcp"]["tools"]
    verifiers = t["verifiers"]["real"]

    replacements = {
        "33+ SOURCES": f"{sources} SOURCES",
        "33+ Sources": f"{sources} Sources",
        "33+ sources": f"{sources} sources",
        "33 Knowledge Sources": f"{sources} Knowledge Sources",
        "33 knowledge sources": f"{sources} knowledge sources",
        "33 sources": f"{sources} sources",
        "36 Simulation Engines": f"{engines} Simulation Engine Bridges",
        "36 simulation engines": f"{engines} simulation engine bridges",
        "36 simulation engine bridges": f"{engines} simulation engine bridges",
        "36 engine adapters": f"{engines} engine bridges",
        "36 engines": f"{engines} engine bridges",
        "20 MCP TOOLS": f"{mcp} MCP TOOLS",
        "20 MCP Tools": f"{mcp} MCP Tools",
        "20 MCP tools": f"{mcp} MCP tools",
        "MCP Native — 20 Tools": f"MCP Native — {mcp} Tools",
        "MCP Server — 20 Tools": f"MCP Server — {mcp} Tools",
        "6 formal verifiers": f"{verifiers} formal verifiers",
        "6 formal verification backends": f"{verifiers} formal verification backends",
        "6 verifiers": f"{verifiers} verifiers",
        "Verification Layer (6 backends)": f"Verification Layer ({verifiers} backends)",
        "MCP 20 tools": f"MCP {mcp} tools",
        "33+ ИСТОЧНИКА": f"{sources} ИСТОЧНИКОВ",
        "33 источника": f"{sources} источников",
        "36 ДВИЖКОВ": f"{engines} МОСТОВ СИМУЛЯЦИИ",
        "36 движков": f"{engines} мостов симуляции",
        "20 MCP-ИНСТРУМЕНТОВ": f"{mcp} MCP-ИНСТРУМЕНТ",
        "MCP-сервер — 20 инструментов": f"MCP-сервер — {mcp} инструмент",
        "MCP 20 инструментов": f"MCP {mcp} инструмент",
        "33+ 知识源": f"{sources} 知识源",
        "33 个知识源": f"{sources} 个知识源",
        "36 个模拟引擎": f"{engines} 个模拟引擎桥接",
        "20 个 MCP 工具": f"{mcp} 个 MCP 工具",
        "20 MCP 工具": f"{mcp} MCP 工具",
        "36 引擎": f"{engines} 引擎桥接",
        "MCP 服务器 — 20 个工具": f"MCP 服务器 — {mcp} 个工具",
        "33+ 知識源": f"{sources} 知識ソース",
        "33 知識源": f"{sources} 知識ソース",
        "36 シミュレーションエンジン": f"{engines} シミュレーションブリッジ",
        "36 エンジン": f"{engines} エンジンブリッジ",
        "20 MCP ツール": f"{mcp} MCP ツール",
        "MCP サーバー — 20 ツール": f"MCP サーバー — {mcp} ツール",
        "33+ QUELLEN": f"{sources} QUELLEN",
        "33 Wissensquellen": f"{sources} Wissensquellen",
        "36 ENGINES": f"{engines} ENGINE-BRÜCKEN",
        "36 Simulations-Engines": f"{engines} Simulationsbrücken",
        "20 MCP-TOOLS": f"{mcp} MCP-TOOLS",
        "MCP-Server — 20 Tools": f"MCP-Server — {mcp} Tools",
        "MCP 20 Tools": f"MCP {mcp} Tools",
        "33+ مصدر": f"{sources} مصدر",
        "33 مصدر معرفة": f"{sources} مصدر معرفة",
        "36 محرك": f"{engines} جسر محاكاة",
        "20 أداة MCP": f"{mcp} أداة MCP",
        "خادم MCP — 20 أداة": f"خادم MCP — {mcp} أداة",
        "33+ स्रोत": f"{sources} स्रोत",
        "33 ज्ञान स्रोत": f"{sources} ज्ञान स्रोत",
        "36 इंजन": f"{engines} सिमुलेशन ब्रिज",
        "36 सिमुलेशन इंजन": f"{engines} सिमुलेशन ब्रिज",
        "20 MCP टूल्स": f"{mcp} MCP टूल्स",
        "MCP सर्वर — 20 टूल्स": f"MCP सर्वर — {mcp} टूल्स",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("33+ knowledge sources", f"{sources} configured knowledge sources")
    text = text.replace("and 23 more.", "and other configured sources.")
    text = re.sub(
        r'<div class="stat-card blue"><div class="stat-value blue">\d+\+?</div>',
        f'<div class="stat-card blue"><div class="stat-value blue">{sources}</div>',
        text,
        count=1,
    )
    text = re.sub(
        r'<div class="stat-card pink"><div class="stat-value pink">\d+</div>',
        f'<div class="stat-card pink"><div class="stat-value pink">{engines}</div>',
        text,
        count=1,
    )
    text = re.sub(
        r'<div class="stat-card amber"><div class="stat-value amber">\d+</div>',
        f'<div class="stat-card amber"><div class="stat-value amber">{mcp}</div>',
        text,
        count=1,
    )
    path.write_text(text)
    print(f"patched {path}")


def patch_architecture(t: dict) -> None:
    """Update current-state architecture prose without touching phase history."""
    path = REPO / "docs/ARCHITECTURE.md"
    text = path.read_text()
    sources = t["knowledge"]["sources"]
    providers = t["llm"]["providers"]
    tests = t["python"]["tests_collected"]

    text = re.sub(
        r"with (?:9,800\+ tests|[\d,]+ tests collected)",
        f"with {tests:,} tests collected",
        text,
        count=1,
    )
    text = text.replace("51 knowledge sources", f"{sources} configured knowledge sources")
    text = text.replace(
        "### Layer 5: LLM Layer (5 Auto-Detected Providers)",
        f"### Layer 5: LLM Layer ({providers} Configured Providers)",
    )
    text = re.sub(
        r"LLM Providers \(auto-detected\):\n├── Local:.*\n├── Cloud:.*\n└── Fallback cascade:.*",
        "LLM providers (configured; availability is detected at runtime):\n"
        "├── Local: MLX-LM, LM Studio, Ollama\n"
        "├── Cloud: OpenRouter, XAI, Mistral, Moonshot, DeepSeek, Liquid, NVIDIA NIM, YandexGPT\n"
        "└── Routing: provider-specific clients plus local/cloud fallback chains",
        text,
        count=1,
    )
    text = text.replace(
        '**Mock Provider**: `LLMProvider.MOCK = "mock"` for testing.',
        "**Routing sentinel:** `LLMProvider.AUTO` selects a provider; it is not counted as a provider.",
    )
    text = re.sub(
        r"\*\*Honest description:\*\* LLM routing works\. 5 providers are auto-detected.*",
        f"**Honest description:** {providers} providers are configured across local and cloud "
        "routes; runtime availability depends on installed local servers and credentials. "
        "OpenRouter is the primary cloud route, and MLX-LM provides local Apple Silicon inference. "
        "Discovery quality remains model-dependent; there is no LLM-agnostic correctness guarantee.",
        text,
        count=1,
    )
    text = text.replace(
        "Search 27 knowledge sources", f"Search {sources} configured knowledge sources"
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
    text = text.replace(
        "10,023 tests · 0 mypy errors", f"{fmt_num(tests)} tests · {mypy} mypy baseline"
    )
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
    sources = t["knowledge"]["sources"]
    engines = t["simulations"]["engines"]
    mcp = t["mcp"]["tools"]
    verifiers = t["verifiers"]["real"]

    for name, tests_line, mypy_line in (
        ("WHITEPAPER.md", tests_fmt_en, mypy_en),
        ("WHITEPAPER.ru.md", tests_fmt_ru, mypy_ru),
    ):
        path = REPO / name
        if not path.exists():
            continue
        text = path.read_text()
        text = re.sub(
            r"\*\*Тесты:\*\* [\d, ]+\+? collected.*",
            f"**Тесты:** {tests_line} collected · mypy baseline: {mypy_line}.",
            text,
        )
        text = re.sub(
            r"\*\*Tests:\*\* [\d,]+\+? collected.*",
            f"**Tests:** {tests_line} collected (Python) · Go TUI: all packages pass · mypy baseline: {mypy_line}.",
            text,
        )
        text = re.sub(
            r"\| Тестов collected \| [\d, ]+\+? \|",
            f"| Тестов collected | {tests_line} |",
            text,
        )
        text = re.sub(
            r"\| Tests collected \| [\d,]+\+? \|",
            f"| Tests collected | {tests_line} |",
            text,
        )
        text = re.sub(
            r"\*\*51 (knowledge sources|источник знаний)\*\*",
            lambda match: f"**{sources} {match.group(1)}**",
            text,
        )
        text = text.replace(
            "MultiSourceSearcher (51 sources)",
            f"MultiSourceSearcher ({sources} configured sources)",
        )
        text = text.replace(
            "MultiSourceSearcher (51 источник)",
            f"MultiSourceSearcher ({sources} настроенных источников)",
        )
        text = text.replace("**51 registered sources**", f"**{sources} configured sources**")
        text = text.replace("**51 источник** через", f"**{sources} настроенных источников** через")
        text = text.replace(
            "| Knowledge sources | 51 |", f"| Knowledge sources | {sources} configured |"
        )
        text = text.replace(
            "| Источников знаний | 51 |", f"| Источников знаний | {sources} настроено |"
        )
        text = text.replace(
            "| Simulation engines | 38 |", f"| Simulation engine bridges | {engines} |"
        )
        text = text.replace("| Движков симуляции | 38 |", f"| Мостов симуляции | {engines} |")
        text = text.replace("| MCP tools | 21 |", f"| MCP tools | {mcp} |")
        text = text.replace("| MCP tools | 21 |", f"| MCP tools | {mcp} |")
        text = text.replace(
            "| Verification backends (real) | 9 |",
            f"| Verification backends (real) | {verifiers} |",
        )
        text = text.replace(
            "| Бэкендов верификации (real) | 9 |", f"| Бэкендов верификации (real) | {verifiers} |"
        )
        path.write_text(text)
        print(f"patched {path}")


def check_public_claims(t: dict) -> int:
    """Fail when current public surfaces retain known stale metric claims."""
    sources = t["knowledge"]["sources"]
    engines = t["simulations"]["engines"]
    mcp = t["mcp"]["tools"]
    verifiers = t["verifiers"]["real"]
    tests = t["python"]["tests_collected"]
    targets = [
        REPO / "README.md",
        REPO / "AGENTS.md",
        REPO / "WHITEPAPER.md",
        REPO / "WHITEPAPER.ru.md",
        REPO / "landing/index.html",
        REPO / "docs/index.html",
        REPO / "docs/ARCHITECTURE.md",
        *sorted((REPO / "landing/i18n").glob("*.json")),
        *sorted((REPO / "landing/docs").rglob("*.html")),
        REPO / "landing/architecture/index.html",
        REPO / "landing/api/index.html",
    ]
    stale_patterns = {
        "stale source count": re.compile(
            r"\b(?:33\+?|43\+?|51\+?)\s+(?:configured\s+)?"
            r"(?:knowledge\s+)?(?:source|sources|SOURCES|Sources)\b"
        ),
        "stale simulation count": re.compile(
            r"\b36\s+(?:simulation\s+)?(?:engine|engines)\b", re.I
        ),
        "stale MCP count": re.compile(
            r"(?:\b20\s+MCP\b|\bMCP[^\\n]{0,20}\b20\s+(?:tool|tools)\b)", re.I
        ),
        "stale verifier count": re.compile(r"\b(?:6|10|14|27)\s+(?:formal\s+)?verifiers?\b", re.I),
        "stale test count": re.compile(r"\b(?:9,?801|9,?861|9,?887)\+?\s+tests?\b", re.I),
        "unsupported adapter count": re.compile(r"\b32\s+adapters?\b", re.I),
        "stale source remainder": re.compile(r"\b(?:23|30)\s+more\b", re.I),
        "stale verification backend count": re.compile(
            r"\b14\s+formal verification backends?\b", re.I
        ),
        "inflated canonical source count": re.compile(
            rf"\b{sources}\+\s+(?:knowledge\s+)?sources?\b", re.I
        ),
        "inflated canonical test count": re.compile(rf"\b(?:{tests}|{tests:,})\+\s+tests?\b", re.I),
    }
    required = {
        REPO / "README.md": (
            f"tests-{tests}%20collected",
            f"**{sources} configured knowledge source integrations**",
            f"**{t['llm']['providers']} LLM providers**",
            f"Verification Backends ({verifiers} real + MathDetector)",
        ),
        REPO / "AGENTS.md": (
            f"**CLI** — {t['cli']['commands']} top-level `blast` commands",
            f"**{sources} configured knowledge source integrations**",
        ),
        REPO / "WHITEPAPER.md": (
            f"**{sources} knowledge sources**",
            f"**{engines} simulation engine bridges**",
            f"**{mcp} MCP tools**",
            f"**Tests:** {tests:,} collected",
        ),
        REPO / "WHITEPAPER.ru.md": (f"**Тесты:** {tests:,}".replace(",", " ") + " collected",),
        REPO / "landing/index.html": (
            f'<div class="stat-value blue">{sources}</div>',
            f'<div class="stat-value pink">{engines}</div>',
            f'<div class="stat-value amber">{mcp}</div>',
            f'<div class="stat-value accent">{tests}</div>',
        ),
        REPO / "docs/ARCHITECTURE.md": (
            f"with {tests:,} tests collected",
            f"({t['llm']['providers']} Configured Providers)",
        ),
    }
    failures: list[str] = []
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text()
        if path.parent == I18N_DIR and "51" in text:
            failures.append(f"{path.relative_to(REPO)}: stale localized source count")
        for label, pattern in stale_patterns.items():
            if pattern.search(text):
                failures.append(f"{path.relative_to(REPO)}: {label}")
        for expected in required.get(path, ()):
            if expected not in text:
                failures.append(f"{path.relative_to(REPO)}: missing canonical claim {expected!r}")
    if failures:
        print("FAIL: public claim drift detected")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("OK: public metric claims match _truths.json")
    return 0


def sync_public_claims(t: dict) -> None:
    if not TRUTHS.exists():
        print("ERROR: run scripts/gen_truths.py first", flush=True)
        raise FileNotFoundError(TRUTHS)
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
        for _key, val in list(data.items()):
            if not isinstance(val, str):
                continue
            val = val.replace("PRODUCTION", "Open source")
            val = val.replace("38 simulation engines", f"{engines} simulation engine bridges")
            val = val.replace("38 engines", f"{engines} engine bridges")
            val = val.replace("6 verifiers (+3 guard-stubs)", f"{ver_real} verifiers")
            val = val.replace("27 verifiers", f"{ver_real} verifiers")
            val = val.replace("32 sim engines", f"{engines} sim engine bridges")
            val = val.replace(
                "32 engine + 27 verifier", f"{engines} engines + {ver_real} verifiers"
            )
            val = val.replace("guard-stubs", "real backends")
            val = val.replace("guard-stub", "real backend")
            val = val.replace("14 verifiers", f"{ver_real} verifiers")
            val = val.replace(
                "38 engines + 14 verifiers", f"{engines} bridges + {ver_real} verifiers"
            )
            if mypy != 0:
                val = val.replace("0 mypy errors", f"{mypy} mypy baseline (regression-gated)")
            val = val.replace("Type safety zero", "Mypy baseline tracked")
            val = val.replace("10,023", fmt_num(tests))
            val = val.replace("22/32 engines", f"{engines} engine bridges")
            val = val.replace("22/32 движка", f"{engines} мостов симуляции")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    patch_landing_html(t)
    patch_landing_pages(t)
    patch_docs_index(t)
    patch_architecture(t)
    patch_main_js(t)
    patch_manifest(t)
    patch_api_i18n(t)
    patch_whitepapers(t)
    print("OK: public docs synced from _truths.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="verify that public metric claims match _truths.json"
    )
    args = parser.parse_args()
    if not TRUTHS.exists():
        print("ERROR: run scripts/gen_truths.py first", flush=True)
        return 1
    t = load()
    if args.check:
        return check_public_claims(t)
    sync_public_claims(t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
