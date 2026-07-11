#!/usr/bin/env python3
"""Merge landing page i18n keys into all 7 language JSON files."""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
I18N = REPO / "landing" / "i18n"

# Canonical metrics (_truths.json 2026-07-11)
PATCHES: dict[str, dict[str, str]] = {
    "en": {
        "nav_discoveries": "Discoveries",
        "hero_cta_discoveries": "6 verified proposals →",
        "hero_badge": "v5.6.0 + TUI v9.13.0 · PRODUCTION · 21 MCP tools",
        "hero_tags": "Z₃³ · 27 STATES · 6 OPERATORS · 51 SOURCES · 38 ENGINES · 21 MCP · O₀→O₁→O₂ · 23 MPs",
        "hero_cta_secondary": "GitLab",
        "feat_kg": "51 Knowledge Sources",
        "feat_sim": "38 Simulation Engines",
        "stat_tests": "Tests Collected",
        "splash_skip": "Skip →",
        "splash_tagline": "Cognitive exoskeleton for humans and AI agents",
        "splash_motto": "Shift paradigms",
        "disc_badge": "July 2026 · HIL pipeline · Quality A+ 98",
        "disc_title": "Verified outputs",
        "disc_sub": "Six full blast turbo runs — literature search, gap mining, simulation, and gated dissertation prose. Real pipeline artifacts, not marketing copy.",
        "disc_epistemic": "<strong>Epistemic status:</strong> These are <em>research proposals</em> (untested hypotheses + computational pre-screening). They are <strong>not peer-reviewed dissertations</strong>. Every file includes an explicit disclaimer. Validate citations and claims before any use.",
        "disc_stat_proposals": "proposals",
        "disc_stat_words": "words each",
        "disc_stat_sources": "sources / run",
        "disc_stat_placeholders": "LLM placeholders",
        "disc_read": "Read proposal →",
        "disc_video_title": "Mission demo (30s)",
        "disc_gallery_title": "TUI v9 mission snapshots",
        "disc_card_climate": "Marine cloud brightening",
        "disc_card_climate_desc": "Geoengineering research proposal: MCB parameter space, field experiments, polar efficacy hypotheses.",
        "disc_card_fusion": "Compact fusion reactors",
        "disc_card_fusion_desc": "Distributed clean energy pathway: breakthrough physics hypotheses for grid decarbonization by 2040.",
        "disc_card_aging": "Epigenetic aging reversal",
        "disc_card_aging_desc": "Metabolic reprogramming hypotheses with gap-mined falsifiers and simulation-backed framing.",
        "disc_card_amr": "AMR phage–CRISPR cocktail",
        "disc_card_amr_desc": "Engineered phage + CRISPR hypotheses to restore antibiotic efficacy against resistant pathogens.",
        "disc_card_soil": "Soil carbon sequestration",
        "disc_card_soil_desc": "Regenerative agriculture hypotheses for desertification reversal and durable soil carbon pools.",
        "disc_card_plastic": "Ocean plastic bioremediation",
        "disc_card_plastic_desc": "Topic-routed biogeochemistry sim; microbial/enzyme remediation hypotheses v2.",
        "show_title": "Showcase",
        "show_sub": "See c4reqber in action. Real queries, real discoveries, real visualizations.",
        "show_demo_title": "Turbo-CDI Demo",
        "show_step1_title": "Launch the TUI",
        "show_step1_desc": "Open the cockpit — active problems, engine status, and recent discoveries at a glance.",
        "show_step2_title": "Run blast turbo",
        "show_step2_desc": "One command triggers the full HIL pipeline: search, gaps, simulation, verification, dissertation.",
        "show_step3_title": "Review gated output",
        "show_step3_desc": "Quality gates block slop. Only prose that passes word-count and placeholder checks is saved.",
        "show_tui_title": "TUI v9 — The Cockpit",
        "show_tui_sub": 'Golden snapshots from the July 2026 mission · <a href="../discoveries/index.html" style="color:var(--primary)">Full gallery →</a>',
        "show_verified_label": "July 2026",
        "show_verified_title": "Verified pipeline outputs",
        "show_verified_desc": 'Six blast turbo research proposals — literature, gaps, simulation, quality gates. <a href="../discoveries/index.html" style="color:var(--primary)">Full gallery with video →</a>',
        "show_verified_disclaimer": "Hypotheses only — not peer-reviewed. Each file carries an epistemic disclaimer.",
        "show_read": "Read →",
        "breadcrumb_showcase": "Showcase",
        "meta_desc_home": "Cognitive exoskeleton for AI agents and researchers. 38 simulation engines, 14 verifiers, 51 knowledge sources, 21 MCP tools, TUI v9. Think. Simulate. Prove. Discover.",
        "feat_mcp": "MCP Server — 21 Tools",
        "feat_mcp_desc": "Expose full C4REQBER capability to AI agents. JSON Schema compliant. stdio JSON-RPC via blast serve --mcp.",
        "fp_conclusion": "c4reqber solves all four. Formal verification + 38 simulation engines + Z₃³ cognitive topology + real citations + O₀→O₁→O₂ meta-cognitive observer.",
        "github_stars": "GitLab",
        "uc_hard_desc": "Physics, chemistry, biology, materials. TRIZ + 38 simulation engines + formal verification.",
    },
    "ru": {
        "nav_discoveries": "Открытия",
        "hero_cta_discoveries": "6 проверенных предложений →",
        "hero_badge": "v5.6.0 + TUI v9.13.0 · PRODUCTION · 21 MCP-инструмент",
        "hero_tags": "Z₃³ · 27 СОСТОЯНИЙ · 6 ОПЕРАТОРОВ · 51 ИСТОЧНИК · 38 ДВИЖКОВ · 21 MCP · O₀→O₁→O₂ · 23 МП",
        "hero_cta_secondary": "GitLab",
        "feat_kg": "51 источник знаний",
        "feat_sim": "38 движков симуляции",
        "stat_tests": "Собрано тестов",
        "splash_skip": "Пропустить →",
        "splash_tagline": "Когнитивный экзоскелет для людей и AI-агентов",
        "splash_motto": "Сдвиг парадигм",
        "disc_badge": "Июль 2026 · HIL-пайплайн · Качество A+ 98",
        "disc_title": "Проверенные результаты",
        "disc_sub": "Шесть полных прогонов blast turbo — поиск литературы, анализ пробелов, симуляция и текст с quality gate. Реальные артефакты пайплайна, не маркетинг.",
        "disc_epistemic": "<strong>Эпистемический статус:</strong> это <em>исследовательские предложения</em> (непроверенные гипотезы + вычислительный прескрининг). Это <strong>не рецензируемые диссертации</strong>. В каждом файле — явный дисклеймер. Проверяйте цитаты и утверждения перед использованием.",
        "disc_stat_proposals": "предложений",
        "disc_stat_words": "слов каждое",
        "disc_stat_sources": "источников / прогон",
        "disc_stat_placeholders": "заглушек LLM",
        "disc_read": "Читать предложение →",
        "disc_video_title": "Демо миссии (30 с)",
        "disc_gallery_title": "Снимки TUI v9",
        "disc_card_climate": "Морское облачное осветление",
        "disc_card_climate_desc": "Предложение по геоинженерии: параметры MCB, полевые эксперименты, гипотезы полярной эффективности.",
        "disc_card_fusion": "Компактные термоядерные реакторы",
        "disc_card_fusion_desc": "Распределённая чистая энергия: гипотезы прорывной физики для декарбонизации сети к 2040.",
        "disc_card_aging": "Эпигенетическое обращение старения",
        "disc_card_aging_desc": "Гипотезы метаболического перепрограммирования с фальсификаторами и симуляцией.",
        "disc_card_amr": "Коктейль фагов и CRISPR против AMR",
        "disc_card_amr_desc": "Инженерные фаги + CRISPR для восстановления эффективности антибиотиков.",
        "disc_card_soil": "Секвестрация углерода в почве",
        "disc_card_soil_desc": "Регенеративное земледелие: гипотезы по борьбе с опустыниванием и углеродным пулом.",
        "disc_card_plastic": "Биоремедиация океанического пластика",
        "disc_card_plastic_desc": "Биогеохимическая симуляция; гипотезы микробной/ферментативной ремедиации v2.",
        "show_title": "Витрина",
        "show_sub": "c4reqber в действии: реальные запросы, открытия и визуализации.",
        "show_demo_title": "Демо Turbo-CDI",
        "show_step1_title": "Запуск TUI",
        "show_step1_desc": "Откройте кокпит — активные задачи, статус движков и свежие открытия.",
        "show_step2_title": "Запуск blast turbo",
        "show_step2_desc": "Одна команда — полный HIL-пайплайн: поиск, пробелы, симуляция, верификация, текст.",
        "show_step3_title": "Проверка результата",
        "show_step3_desc": "Quality gate отсекает slop. Сохраняется только текст, прошедший проверки.",
        "show_tui_title": "TUI v9 — Кокпит",
        "show_tui_sub": 'Golden-снимки миссии июля 2026 · <a href="../discoveries/index.html" style="color:var(--primary)">Полная галерея →</a>',
        "show_verified_label": "Июль 2026",
        "show_verified_title": "Проверенные результаты пайплайна",
        "show_verified_desc": 'Шесть исследовательских предложений blast turbo. <a href="../discoveries/index.html" style="color:var(--primary)">Галерея с видео →</a>',
        "show_verified_disclaimer": "Только гипотезы — не рецензируемые работы. В каждом файле — дисклеймер.",
        "show_read": "Читать →",
        "breadcrumb_showcase": "Витрина",
        "meta_desc_home": "Когнитивный экзоскелет для AI-агентов и исследователей. 38 движков, 14 верификаторов, 51 источник, 21 MCP, TUI v9.",
        "feat_mcp": "MCP-сервер — 21 инструмент",
        "feat_mcp_desc": "Полный C4REQBER для AI-агентов. JSON Schema, stdio JSON-RPC через blast serve --mcp.",
        "fp_conclusion": "c4reqber закрывает все четыре пробела: формальная верификация + 38 движков симуляции + топология Z₃³ + реальные цитаты + наблюдатель O₀→O₁→O₂.",
        "github_stars": "GitLab",
        "uc_hard_desc": "Физика, химия, биология, материалы. TRIZ + 38 движков симуляции + формальная верификация.",
    },
}

# Other langs: English base + key overrides where we have them in existing files style
FALLBACK_LANGS = ("zh", "ja", "de", "ar", "hi")


def main() -> None:
    en_patch = PATCHES["en"]
    for lang in ["en", "ru", *FALLBACK_LANGS]:
        path = I18N / f"{lang}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        patch = PATCHES.get(lang, en_patch)
        data.update(patch)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"patched {lang}: +{len(patch)} keys")


if __name__ == "__main__":
    main()
