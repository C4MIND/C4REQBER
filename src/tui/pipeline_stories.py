"""
TUI: Pipeline Stories
Story messages for each pipeline step in each mode.
"""
from __future__ import annotations


PIPELINE_STORIES = {
    "discover": [
        ("C4 Navigation", "27 состояний. Ваш путь: origin → insight. ≤6 шагов."),
        ("TRIZ Analysis", "Противоречие разрешено. Принцип №7 «Вложенность»..."),
        ("Knowledge Search", "28 источников опрошены через orchestrator. 74 статьи."),
        ("GAP_ANALYSIS", "ABC GapAnalyzer: 18 пробелов. Один никем не исследован."),
        ("QUALITY_GATE", "RedundantGates: проверка на избыточность пройдена."),
        ("REALITY_CHECK", "Observer: мета-когнитивный фрейминг. Q≈0.87."),
        ("CROSS_DOMAIN_TRANSFER", "DiscoveryMemory: структурный изоморфизм из другой области."),
        ("Hypothesis", "Гипотеза сформулирована. SCSTSG. Модель готова."),
        ("PLUGIN_EXECUTION", "20 когнитивных плагинов. SWOT + Red Team + SCAMPER."),
        ("SIMULATION", "101+ паттернов. Newton Physics в mlx-env."),
        ("FORMAL_VERIFICATION", "FinalVerifier: Lean4 + Coq + Dafny. Теорема верна."),
        ("Blueprint", "Манифест + аксиоматика. Готово к публикации."),
    ],
    "invent": [
        ("C4 Navigation", "Состояние: analysis(1,1,0). Готовность к изобретению."),
        ("TRIZ Analysis", "Противоречие: эффективность vs сложность. Принцип №24 активирован."),
        ("Knowledge Search", "Поиск аналогов. 28 источников через orchestrator. 41 патент."),
        ("GAP_ANALYSIS", "Патентный пробел обнаружен. Никто не комбинировал A и B."),
        ("QUALITY_GATE", "Проверка на новизну: PASS. Избыточность не обнаружена."),
        ("REALITY_CHECK", "Observer: мета-когнитивная проверка концепции пройдена."),
        ("CROSS_DOMAIN_TRANSFER", "Изоморфизм: биологическая мембрана ≡ селективный фильтр."),
        ("Hypothesis", "Концепция изобретения: Multi-Layer Selective Membrane."),
        ("PLUGIN_EXECUTION", "SWOT + SCAMPER + Morphological. 12 плагинов активно."),
        ("SIMULATION", "Молекулярная динамика. Newton Physics. 10000 атомов."),
        ("FORMAL_VERIFICATION", "Структурная целостность: Lean4 подтверждена."),
        ("Blueprint", "SVG + CAD спецификация. Готово к прототипированию."),
    ],
    "transform": [
        ("C4 Navigation", "Turbo-режим. 27 когнитивных состояний. 25 агентов."),
        ("TRIZ Analysis", "40×40 матрица. Парадигмальное противоречие обнаружено."),
        ("Knowledge Search", "Масштабный поиск. 28 источников. 215+ статей."),
        ("GAP_ANALYSIS", "47 пробелов. 12 противоречий. 3 парадигмальные аномалии."),
        ("QUALITY_GATE", "RedundantGates: избыточность 0. Парадигмальный сдвиг возможен."),
        ("REALITY_CHECK", "Observer: мета-фрейминг. Уже сдвинут? Проверка..."),
        ("CROSS_DOMAIN_TRANSFER", "DiscoveryMemory: 8 кросс-доменных изоморфизмов."),
        ("Hypothesis", "Теоретическая модель: Unified Framework of..."),
        ("PLUGIN_EXECUTION", "20 плагинов. Delphi + OODA + Six Hats."),
        ("SIMULATION", "25 параллельных симуляций. 5 физических движков."),
        ("FORMAL_VERIFICATION", "FinalVerifier: Lean4 + Coq + Dafny. Тройная проверка."),
        ("Blueprint", "Диссертация 7 глав. 40+ страниц."),
    ],
}

STEP_TO_C4 = [
    (0,0,0), (0,0,1), (0,1,0), (0,1,1), (0,2,0), (0,2,1),
    (1,0,0), (1,0,1), (1,1,0), (1,1,1), (1,2,0), (2,1,2),
]

STEP_ICONS = [
    "🧠", "💡", "📚", "🔍", "🔗", "🔬",
    "⚡", "✅", "🎯", "🧬", "🔄", "📝",
]
