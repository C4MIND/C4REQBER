# Технический Whitepaper c4reqber

**Версия:** backend 5.6.0 · TUI v9.13.0 · **июль 2026**  
**Авторы:** c4reqber Contributors (AGPL-3.0)  
**Источник метрик:** `_truths.json` (обновление: `python3 scripts/gen_truths.py`)

> **English version:** [WHITEPAPER.md](WHITEPAPER.md)

---

## Краткое резюме

**c4reqber** — терминальный когнитивный экзоскелет для AI-агентов и исследователей. Превращает запросы на естественном языке в **артефакты с жёсткими гейтами** — диссертации, статьи, whitepaper, blueprint, код и отчёты верификации — с опорой на:

- навигацию **C4-META** в Z₃³ (27 когнитивных состояний, 6 операторов, Теорема 11)
- **51 источник знаний** (литература + данные/биология)
- **38 мостов симуляции** (GPU, CPU, облачная делегация)
- **9 реальных бэкендов формальной верификации** (Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy)
- **21 MCP-инструмент** для интеграции агентов
- **TUI v9** — кокпит discovery с overlay возможностей (Ctrl+Shift+C)

Этот документ — **whitepaper реализации** production-кодовой базы. Формальная теория C4-META — в отдельном репозитории [adaptive-topology](https://gitlab.com/cognitive-functors/Adaptive-topology) (~3600 строк Agda).

---

## Содержание

1. [Постановка задачи](#1-постановка-задачи)
2. [Когнитивный слой C4-META](#2-когнитивный-слой-c4-meta)
3. [Архитектура (7 слоёв)](#3-архитектура-7-слоёв)
4. [Пайплайн discovery](#4-пайплайн-discovery)
5. [Верификация (9 бэкендов)](#5-верификация-9-бэкендов)
6. [Симуляция (38 движков)](#6-симуляция-38-движков)
7. [Получение знаний](#7-получение-знаний)
8. [Агент и MCP](#8-агент-и-mcp)
9. [TUI v9 Cockpit](#9-tui-v9-cockpit)
10. [Безопасность и quality gates](#10-безопасность-и-quality-gates)
11. [Метрики и честный статус](#11-метрики-и-честный-статус)
12. [Ссылки](#12-ссылки)

---

## 1. Постановка задачи

Типичные ассистенты научного discovery:

1. **Галлюцинируют цитаты** — вымышленные теории и статьи
2. **Пропускают фальсификацию** — нет Popper-гейтов, нет формальных проверок
3. **Симуляция опциональна** — нет awareness возможностей машины
4. **Верификация — заглушки** — не machine-checked proofs

c4reqber закрывает все четыре пункта **единым контрактом пайплайна**: каждый `blast turbo` / `blast solve` проходит поиск литературы, gap analysis, гипотезы, симуляцию, **гибридную верификацию**, генерацию диссертации и взвешенные quality gates.

**Эпистемическая оговорка:** выход пайплайна — **исследовательские предложения** с вычислительным pre-screening, а не рецензируемые публикации без эмпирической валидации.

---

## 2. Когнитивный слой C4-META

### Пространство состояний Z₃³

| Ось | Значения | Смысл |
|-----|----------|-------|
| T (Время) | 0, 1, 2 | Временная рамка |
| S (Масштаб) | 0, 1, 2 | Гранулярность |
| A (Агентность) | 0, 1, 2 | Позиция наблюдателя |

**27 состояний** = 3³. **6 операторов:** T, T_INV, S, S_INV, A, A_INV.

### Теорема 11 (исправленная)

- **Неориентированный диаметр:** 3
- **Ориентированный прямой диаметр:** 6

Проверено brute-force в production-движке; формальное доказательство — в theory repo.

### Сдвиги наблюдателя (O₀ → O₁ → O₂)

Мета-когнитивная рефлексия в `PipelineExecutor`:

- **O₀→O₁:** диагностика слепых зон после синтеза
- **O₁→O₂:** мета-рефлексия при стагнации
- Альтернативные C4-состояния из инсайтов O₂

---

## 3. Архитектура (7 слоёв)

```
Слой 0: CLI / blast — solve, turbo, flash, turbofactory, tui, serve --mcp
Слой 1: API — FastAPI v8, SSE, WebSocket, JWT + CSRF
Слой 2: Пайплайны — HILDiscoveryPipeline, UniversalSolvePipeline
Слой 3: Ядро — C4, TRIZ (40 принципов), 7 метамоделей, 28 плагинов
Слой 4: Когнитив — causal, Bayesian, discovery, litintel
Слой 5: Знания + симуляция — orchestrator.py, 38 мостов
Слой 6: Верификация — HybridVerifier, 9 бэкендов, MathDetector A/B/C
```

**Output profiles:** `detect_format()` выбирает формат выхода и передаёт `preferred_backends` в Phase E.

---

## 4. Пайплайн discovery

### HILDiscoveryPipeline (turbo) — 12 фаз

| Фаза | Название | Ключевые модули |
|------|----------|-----------------|
| A | Framing | SystemAnalyzer, C4 |
| B | Knowledge | MultiSourceSearcher (51 источник) |
| C | Gap analysis | GapMiner |
| D | Hypotheses | LLM + TRIZ + 20 плагинов |
| E | Simulation + Verification | PatternRunnerV2, HybridVerifier |
| F | Dissertation | quality gate ≥600 слов |
| G | Quality control | 8 взвешенных гейтов |

**Жёсткие гейты:** AlreadyShiftedDetector, NoveltyValidator (итеративно).

### Форматы выхода (авто-детект)

| Формат | Назначение | Профиль верификации |
|--------|------------|---------------------|
| Dissertation | парадигма, thesis | lean4, coq, dafny, z3, cvc5, tla, alloy |
| Article | журнальная статья | z3, cvc5, dafny, hoare |
| Whitepaper | архитектура | z3, cvc5, tla, alloy |
| Blueprint | спецификация API | dafny, z3, cvc5, tla |
| Code | реализация | dafny, z3, hoare |
| Verification report | только формальное | все 9 бэкендов |

---

## 5. Верификация (9 бэкендов)

**0 guard-stubs.** Реальные клиенты при установленном внешнем инструменте.

```
Lean4 → Coq → Dafny → Agda → Z3/CVC5 → Hoare → TLA+ → Alloy → Haskell
```

### Стратегия HybridVerifier

1. Автовыбор бэкенда по ключевым словам + `preferred_backends` профиля
2. Fast path: встроенный SMT/TLA/Alloy код (без LLM)
3. LLM → компиляция → retry по ошибкам (max 3)
4. Fallback на Z3 при таймауте

### TLA+

- TLC требует **ограниченное** пространство состояний
- `TLAClient` отклоняет неограниченные счётчики Naturals **до** запуска TLC
- Всегда `-modelcheck -depth 10`; таймаут 120 с
- Подробнее: [docs/VERIFICATION_BACKENDS.md](docs/VERIFICATION_BACKENDS.md)

---

## 6. Симуляция (38 движков)

**38 мостов** — `GET /v8/simulations/capabilities`:

| Уровень | Примеры |
|---------|---------|
| Fast | Newton, TorchSim, JaxSim, Taichi |
| Slow | OpenMM, GROMACS, OpenFOAM, PySCF |
| Cloud | vast.ai, NVIDIA Brev |

TUI **Ctrl+Shift+C** — статус per-platform + install hints.

**101+ паттернов** через `PatternRunnerV2`.

---

## 7. Получение знаний

**51 источник** через `orchestrator.py`: arXiv, PubMed, Crossref, Semantic Scholar, OpenAlex, PubChem, ChEMBL, STRING, …

Circuit breaker, semantic dedup, domain boost, ChromaDB cache.

---

## 8. Агент и MCP

### MCP (`blast serve --mcp`)

**21 инструмент** с JSON Schema: `c4_solve`, `c4_verify`, `c4_simulate`, `blast_turbo`, …

Реестр: `docs/mcp_registry.md`.

### Главный агент

Pydantic AI, 11 skills, ChromaDB memory, `/preprint`.

---

## 9. TUI v9 Cockpit

Go Bubble Tea v2 · **~21k LOC** · i18n 7 языков (198 ключей)

| Функция | Клавиша |
|---------|---------|
| Capabilities overlay | Ctrl+Shift+C |
| Command palette | `:` |
| Debug overlay | Ctrl+Shift+D |

**132 golden snapshots** на 6 terminal fixtures.

---

## 10. Безопасность и quality gates

Round 5 audit: **0 CRITICAL / 0 HIGH** в scope.

- Prompt injection: 19 паттернов, fail-closed
- CSRF: Bearer bypass для API-клиентов
- Subprocess: без shell injection

**Тесты:** 9 861+ collected · mypy baseline: 0 (regression-gated).

---

## 11. Метрики и честный статус

| Метрика | Значение |
|---------|----------|
| Python LOC | ~226k |
| Тестов collected | 9 887+ |
| MCP tools | 21 |
| Бэкендов верификации (real) | 9 |
| Guard-stubs | 0 |
| Движков симуляции | 38 |
| Источников знаний | 51 |

### Ограничения

- WASM: wasmtime при установке, иначе stub
- Симуляции: внешняя установка per engine
- TLA+: только bounded models
- LLM proofs: зависит от домена

---

## 12. Ссылки

| Ресурс | Ссылка |
|--------|--------|
| Репозиторий | GitLab: `cognitive-functors/turbo-cdi` |
| Установка | [docs/INSTALL.md](docs/INSTALL.md) |
| Архитектура | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Верификация | [docs/VERIFICATION_BACKENDS.md](docs/VERIFICATION_BACKENDS.md) |
| MCP | [docs/mcp_registry.md](docs/mcp_registry.md) |
| Теория C4 (Agda) | [adaptive-topology](https://gitlab.com/cognitive-functors/Adaptive-topology/-/tree/main/formal-proofs) |
| Контекст агентов | [AGENTS.md](AGENTS.md) |

**Цитирование:** Selyutin I., Kovalev N.I. (2026). *c4reqber: Cognitive Exoskeleton for AI Agents.* AGPL-3.0.

---

*Синхронизация метрик: `python3 scripts/sync_truths_to_docs.py`*
