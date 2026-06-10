# TUI v9 «THE COCKPIT» v2 — Полный рефактор + LLM-пайплайн переводов

**Дата:** 2026-06-10
**Версия плана:** v2 (учитывает новые требования по рефактору в новый файл и LLM-пайплайну)
**Скоуп:** новый `src/tui/v9/` параллельно с `src/tui/v8/`. Старый НЕ удаляется.

---

## 0. Изменения относительно v1 плана

| v1 | v2 |
|---|---|
| 3-колоночный layout с 21 экраном-оверлеем | **Single-cockpit feed** (header + scrollable feed + input + footer) |
| Старый TUI v8 рефакторится на месте | **Новый код в `src/tui/v9/`**. v8 нетронут, доступен через `--tui-version v8` |
| i18n через LLM "один раз и готово" | **Многоступенчатый LLM-pipeline** с per-key/segment/stage, multi-pass review, native-speaker spot-check, специальные инструменты для CJK + AR + DE |
| Стартуем с EN+RU | **Стартуем с EN+RU**, остальные 5 — через LLM-пайплайн v1.0, потом human re-pass |
| Бюджет: $200/язык | **Бюджет = $0 (всё через open-source LLM + БД), плюс опционально human-аудит $100-200/язык** |

---

## 1. Главный тезис

> **TUI v9 = single-cockpit "The Cockpit"** — header (1 строка) + scrollable feed (80%) + input (3 строки) + footer (1 строка). Никаких экранов-оверлеев. Все артефакты (hypothesis / paper / code / verification) приходят как карточки в ленту. Ввод → Enter → лента оживает в реальном времени. Старый TUI v8 остаётся работать параллельно через флаг.

---

## 2. Архитектура: v8 и v9 бок-о-бок

```
src/tui/
├── v8/                       # Legacy. Не трогаем. Запускается через `./bin/c4tui-v8` или `c4tui --tui-version v8`
│   ├── main.go               # 160 LOC
│   ├── update.go             # 943 LOC
│   ├── view.go               # 199 LOC
│   ├── model.go              # 111 LOC
│   ├── widgets/              # 10 файлов
│   ├── screens/              # 21 файл
│   ├── styles/               # theme
│   ├── internal/             # i18n, lang, store, sanitize
│   ├── backend/              # client, sse, rate_limiter
│   ├── layout.go
│   ├── splash/
│   └── go.mod
│
├── v9/                       # NEW. Cockpit. Single-cockpit feed.
│   ├── main.go               # 200 LOC
│   ├── update.go             # 700 LOC
│   ├── view.go               # 250 LOC (compose: header + feed + input + footer)
│   ├── model.go              # 150 LOC
│   ├── layout.go             # 100 LOC (4 региона, не 3 колонки)
│   ├── splash/               # 1 файл, минимальный, 100 LOC
│   ├── styles/
│   │   ├── theme.go          # базовые палитры
│   │   └── card.go           # per-card-type colors (NEW)
│   ├── backend/              # REUSED from v8 (через internal package)
│   │   ├── client.go         # import path
│   │   ├── sse.go
│   │   └── rate_limiter.go
│   ├── widgets/
│   │   ├── feed.go           # NEW. Scrollable card list. 400 LOC
│   │   ├── card_phase.go     # NEW. 80 LOC
│   │   ├── card_hypothesis.go# NEW. 100 LOC
│   │   ├── card_paper.go     # NEW. 100 LOC
│   │   ├── card_code.go      # NEW. 100 LOC
│   │   ├── card_verification.go # NEW. 100 LOC
│   │   ├── card_error.go     # NEW. 60 LOC
│   │   ├── card_synthesis.go # NEW. 80 LOC
│   │   ├── progress.go       # NEW. 80 LOC
│   │   ├── header.go         # NEW. 50 LOC
│   │   ├── footer.go         # NEW. 200 LOC (narrative status)
│   │   ├── inputbar.go       # NEW. 250 LOC (rotating placeholders, token counter)
│   │   ├── palette.go        # NEW. 200 LOC (bottom-sheet palette)
│   │   ├── help_card.go      # NEW. 150 LOC (inline help, not overlay)
│   │   └── mascot.go         # Avatar-only. 80 LOC
│   ├── internal/             # REUSED from v8 (через go internal linking)
│   │   ├── store.go          # session persistence
│   │   ├── sanitize.go
│   │   ├── text.go
│   │   └── mascot_memory.go
│   ├── i18n/                 # NEW. Pipeline-driven i18n.
│   │   ├── en.toml           # reference (English source of truth)
│   │   ├── ru.toml           # Russian (authored)
│   │   ├── zh.toml           # Chinese (LLM-pipeline + native spot-check)
│   │   ├── ja.toml           # Japanese
│   │   ├── de.toml           # German
│   │   ├── ar.toml           # Arabic
│   │   ├── hi.toml           # Hindi
│   │   ├── i18n.go            # generated: T(key, lang) function
│   │   ├── i18n_test.go      # generated: 100% coverage tests
│   │   ├── README.md         # documents the pipeline
│   │   └── pipeline/         # the i18n LLM pipeline (Go + Python)
│   │       ├── translate.py  # main pipeline
│   │       ├── review.py     # cross-check pass
│   │       ├── eval.py       # quality metrics
│   │       ├── config.yaml   # provider config
│   │       ├── prompts/      # prompt templates per language
│   │       └── Makefile      # `make i18n-build`, `make i18n-audit`
│   ├── screens/              # УДАЛЁН. Всё inline в feed.
│   └── go.mod
│
└── shared/                   # NEW. Общий код для v8 и v9.
    ├── internal/i18n_common/  # только en.toml + базовые языковые константы
    └── backend/              # HTTP клиент к c4reqber API
```

**Правила сосуществования:**
- v8 и v9 — разные Go-модули (`v8/go.mod`, `v9/go.mod`).
- Общий код (HTTP клиент к API, типы бэкенда) — в `shared/backend/`, импортируется обеими.
- CLI-флаг `--tui-version v8|v9` (default v9 в production).
- Два бинаря: `bin/c4tui-v8`, `bin/c4tui-v9`.

---

## 3. LLM-pipeline для переводов (v1.0 = production)

### 3.1 Цель

Сгенерировать 7 файлов переводов (`zh.toml`, `ja.toml`, `de.toml`, `ar.toml`, `hi.toml`, + обновления `ru.toml`) с качеством **значительно лучше текущего baseline** (где ZH содержал JA, JA содержал DE, DE содержал AR).

### 3.2 Стратегия: 5-pass pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ Pass 1: Per-key direct translation (DeepSeek-V3)                    │
│   • Input: en.toml + key context (UI element type, где используется) │
│   • Output: raw translation                                          │
│   • Quality: ★★☆☆☆ baseline                                         │
│   • Cost: ~$0.05 total                                              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Pass 2: Contextual refinement (Claude-Sonnet-4.6)                   │
│   • Input: pass 1 + surrounding keys + UI context (where shown)      │
│   • Catches: keys that need tone consistency, formal/informal        │
│   • Quality: ★★★☆☆                                                  │
│   • Cost: ~$0.20 total                                              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Pass 3: Domain-specific gloss check (Qwen3-72B для CJK; LLaMA 3.3  │
│   70B для EU)                                                       │
│   • Сверяет: scientific terms (hypothesis, paper, citation, etc.)   │
│   • Reference: Helsinki-NLP/Opus-MT terminological pairs              │
│   • Quality: ★★★★☆                                                  │
│   • Cost: ~$0.10 total                                              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Pass 4: Cross-language contamination check                          │
│   • КРИТИЧНО: текущая катастрофа = ZЯ 糸JJ в DE-блоке и т.п.       │
│   • NLLB-200 (Meta) + langdetect для каждого key                    │
│   • Quality: ★★★★☆ (гарантирует отсутствие cross-contamination)      │
│   • Cost: $0 (self-hosted HF model или HF inference API)             │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Pass 5: Native-speaker spot-check (5% sample)                       │
│   • Random 5% ключей проверяются вручную                            │
│   • Если fail > 10% → регенерируем весь язык через pass 1+2         │
│   • Quality: ★★★★★ (post-check)                                     │
│   • Cost: ~$0 (time) or $50-100 (Upwork native-speaker per lang)     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Stack: реальные инструменты (с обоснованием из реального поиска)

| # | Tool | Use case | Source | License | Cost |
|---|------|----------|--------|---------|------|
| 1 | **DeepSeek-V3** (через DeepSeek API) | Pass 1 — базовая быстрая генерация | platform.deepseek.com | MIT weights + pay-per-token API | $0.14/1M in, $0.28/1M out |
| 2 | **Claude Sonnet 4.6** (Anthropic) | Pass 2 — тональный refine, formality | console.anthropic.com | Closed API | $3/1M in, $15/1M out |
| 3 | **Qwen3-72B-Instruct** | Pass 3 — CJK terminological accuracy | OpenRouter или DashScope | Apache 2.0 | $0.40/1M in, $0.40/1M out (DeepInfra) |
| 4 | **LLaMA 3.3 70B** (Meta) | Pass 3 — EU languages (FR/DE/ES) | OpenRouter или self-host | Llama 3.3 Community License | $0.40-$0.65/1M |
| 5 | **NLLB-200-distilled-600M** (Meta) | Pass 4 — language detection + cross-contamination check | HuggingFace | CC-BY-NC 4.0 (commercial ok w/ approval) | $0 self-host |
| 6 | **Helsinki-NLP/opus-mt-tc-big-*** | Pass 3 — back-translation verification | HuggingFace | CC-BY 4.0 | $0 self-host |
| 7 | **Argos Translate** | Offline fallback, no internet | github.com/argosopentech/argos-translate | MIT | $0 self-host |
| 8 | **LibreTranslate** (optional) | Локальный сервер переводов, замена OpenRouter | github.com/LibreTranslate/LibreTranslate | AGPL-3.0 | $0 self-host |
| 9 | **LTEngine** (alternative) | LLM-powered local translation, в 1.5x быстрее LT | github.com/LibreTranslate/LTEngine | AGPL-3.0 | $0 self-host |
| 10 | **Lingo.dev CLI** | Pipeline orchestration: read TOML, send to LLM, write back | github.com/lingodotdev/lingo.dev | MIT | $0 (CLI free, hosted API optional) |
| 11 | **go-i18n** | TOML → Go map generation | github.com/nicksnyder/go-i18n | BSD-3 | $0 |
| 12 | **lorca / gettext-style .po files** (optional) | Alt format for human translators via POEdit | — | GPL | $0 |
| 13 | **SimpleLocalize** (CI/CD) | Auto-sync с .po files, audit pipeline | simplelocalize.io | SaaS | Free tier до 1000 keys |
| 14 | **ChatGPT 5.3 (alternate Pass 2)** | Если нужна OpenAI-only альтернатива | api.openai.com | Closed | $5/1M in, $15/1M out |
| 15 | **Grok 4.3** (через XAI, если у тебя есть ключ) | Alt Pass 1 | api.x.ai | Closed | $3/1M in, $15/1M out |

**Используем 7+4 = 11 инструментов**. Не "скопировать один перевод из Claude". Каждый — для своей задачи.

### 3.4 Pipeline architecture (concrete)

```
/Users/figuramax/LocalProjects/c4reqber/src/tui/v9/i18n/
├── pipeline/
│   ├── Makefile
│   │   ├── i18n-build:  запускает translate.py → review.py → eval.py
│   │   ├── i18n-audit:  проверяет покрытие 100% × 7 langs
│   │   ├── i18n-test:   гоняет snapshot-test переводов
│   │   └── i18n-eval:   вычисляет BLEU/chrF vs human ref
│   ├── translate.py          # Pass 1+2+3: 3 провайдера, sequential
│   ├── review.py             # Pass 4: NLLB lang-detect + cross-check
│   ├── eval.py               # Pass 4.5: BLEU + chrF + native spot-check seed
│   ├── config.yaml           # providers, model IDs, costs
│   ├── prompts/
│   │   ├── translate_en_to_zh.txt
│   │   ├── translate_en_to_ja.txt
│   │   ├── translate_en_to_de.txt
│   │   ├── translate_en_to_ar.txt  # + RTL special notes
│   │   ├── translate_en_to_hi.txt
│   │   ├── translate_en_to_ru.txt
│   │   ├── refine_zh.txt          # for Pass 2
│   │   ├── domain_check_cjk.txt   # for Pass 3
│   │   └── domain_check_eu.txt
│   ├── glossary/
│   │   ├── c4_science_terms.json  # curated translation memory (TM)
│   │   │                         # "hypothesis" → 假设 (zh), 仮説 (ja)
│   │   │                         # "TRIZ principle" → 特利兹原理 (zh)
│   │   │                         # "C4 cube" → C4立方体 (zh), C4キューブ (ja)
│   │   └── styleguide.json       # formality per lang (RU=formal, DE=formal, JA=polite, AR=formal)
│   └── cache/
│       └── llm_responses/        # кэш LLM ответов для идемпотентности
├── en.toml                   # reference
├── ru.toml                   # human-authored baseline
├── zh.toml                   # generated by pipeline
├── ja.toml
├── de.toml
├── ar.toml
├── hi.toml
└── README.md                 # документирует весь pipeline
```

### 3.5 Glossary: ключевая защита от cross-contamination

**Конкретный пример** — чтобы ZH-перевод не уходил в JA:

```json
// glossary/c4_science_terms.json
{
  "hypothesis": {
    "zh": "假设",
    "ja": "仮説",
    "ko": "가설",
    "ru": "гипотеза",
    "de": "Hypothese",
    "fr": "hypothèse",
    "es": "hipótesis",
    "ar": "فرضية",
    "hi": "परिकल्पना",
    "en": "hypothesis"
  },
  "verification": {
    "zh": "验证",
    "ja": "検証",
    "ko": "검증",
    "ru": "верификация",
    "de": "Verifizierung",
    "ar": "التحقق",
    "hi": "सत्यापन"
  },
  "discovery": {
    "zh": "发现",       // НЕ 発見 (это JA!)
    "ja": "発見",
    "ko": "발견",
    "ru": "открытие",
    "de": "Entdeckung",
    "ar": "اكتشاف",
    "hi": "खोज"
  }
  // ... 60+ ключей
}
```

**Каждый pass pipeline'а получает этот glossary** и **ОБЯЗАН** использовать эти точные термины. Это убивает cross-contamination на корню.

### 3.6 Cross-contamination detector (Pass 4)

```python
# pipeline/review.py — sketch
from transformers import pipeline

# Load langdetect via fasttext (works on short strings too)
lang_detector = pipeline("text-classification", 
                          model="papluca/xlm-roberta-base-language-detection")

LANG_EXPECTED = {"zh": "zh", "ja": "ja", "de": "de", "ar": "ar", "hi": "hi"}

for lang, file in translation_files.items():
    toml = tomllib.load(file)
    for key, value in toml.items():
        detected = lang_detector(value)[0]["label"]
        expected = LANG_EXPECTED[lang]
        if detected != expected:
            print(f"❌ {lang}/{key}: detected {detected}, expected {expected}")
            # mark for re-translation
```

### 3.7 Промпты (примеры)

**Pass 1 (DeepSeek-V3):**
```
You are a professional UI localizer translating from English to {TARGET_LANG}.
For each i18n key below, provide the natural {TARGET_LANG} translation.

CRITICAL RULES:
1. The translation must be in {TARGET_LANG} ONLY. No characters from other languages.
2. Match the tone: {TONE_GUIDE[lang]} (e.g., JA: keigo/polite; AR: formal; DE: Sie form)
3. Use the EXACT scientific terms from the glossary below. Do NOT translate them.
4. Keep placeholders like {variable} and %s intact.
5. Match the length: if English is short, {TARGET_LANG} should also be concise.

GLOSSARY:
{glossary}

UI CONTEXT (where each key is used):
{context}

KEYS:
{keys}

Output format (JSON):
{{
  "key1": "translation1",
  "key2": "translation2",
  ...
}}
```

**Pass 4 (NLLB contamination check):**
```python
# Sample of ~50 keys per language, check each
# Reject and re-translate if not in expected language
```

### 3.8 Realistic cost estimate

| Pass | Tool | Volume | Cost |
|---|---|---|---|
| 1 | DeepSeek-V3 | 200 keys × 7 langs × 1.5K tok = 2.1M tok | $0.30 + $0.59 = **$0.89** |
| 2 | Claude Sonnet 4.6 | 200 keys × 7 langs × 2K tok (longer refine prompt) = 2.8M tok | $8.40 + $42 = **$50.40** |
| 3 | Qwen3-72B (CJK only) + LLaMA 3.3 (EU only) | 200 × 3 × 1.5K = 900K tok | $0.36 + $0.36 = **$0.72** |
| 4 | NLLB-200 self-hosted | 1400 inferences | $0 |
| 5 | Manual spot-check (5% × 7 = 70 keys) | optional: human via Upwork | $0-200 |
| **Total** | | | **~$52-252** |

**С DeepSeek + Claude-Sonnet мы за $52 получим production-quality v1**. Native re-pass (Phase 2) — опционально $200-500.

### 3.9 What goes into v9 vs v10

| Phase | Timeline | v9 (текущая) | v10 (будущее) |
|---|---|---|---|
| Pipeline | Day 1-3 | Build translate.py + 3 passes | — |
| Glossary | Day 1 | 60+ scientific terms | Expand to 200+ |
| Output | Day 4 | `zh/ja/de/ar/hi.toml` v1.0 from LLM | human re-pass |
| Quality | Day 5 | 5% manual spot-check | 100% native-speaker audit |
| i18n.go code | Day 6 | Generated by go-i18n from TOML | — |

---

## 4. UX-ТЗ (по 19 вопросам — сжато, см. v1-план для полной версии)

| # | Вопрос | Ответ (one-liner) |
|---|---|---|
| 1 | Что на экране? | Single-cockpit: header (1) + feed (80%) + input (3) + footer (1) |
| 2 | Где курсор? | Input bar (focused) — пользователь сразу печатает |
| 3 | Как переключать mode? | `:` palette ИЛИ `Ctrl+T` (turbo), `Ctrl+F` (flash), `Ctrl+D` (discover) |
| 4 | Почему один экран? | "Real-time discovery" — пользователь должен видеть поток мыслей ИИ |
| 5 | Цель карточки? | Самодостаточный артефакт (hypothesis/paper/code/verification) |
| 6 | Критерии качества feed'а? | Каждая карточка: title, provenance, inline actions, expandable |
| 7 | Куда cancel/quit? | `Esc` cancel pipeline, `Ctrl+C` quit (с confirm) |
| 8 | Откуда данные? | Backend HTTP API; SSE streaming |
| 9 | Варианты после discovery? | `→ Export | → Verify | → Publish | → Refine` chips в footer |
| 10 | Задачи/этапы? | 7 фаз A-G в feed'е как phase cards |
| 11 | Настройки? | `:settings` — bottom-sheet, не fullscreen |
| 12 | Порядок фаз? | A→G (backend фиксирует) |
| 13 | Относительно чего? | Время с submit, % фаз, quality (0-100) |
| 14 | Сколько длится? | 30-90s; live timer в header |
| 15 | Прогресс? | Per-phase: idle `▁` / running `▃` (pulsing) / done `█` |
| 16 | Зачем? | "Сделать из пользователя гениального учёного" |
| 17 | Результат? | Hypothesis + paper + simulation + verification, всё в feed'е |
| 18 | Что дальше? | Action chips + history peek |
| 19 | Как новый юзер поймёт? | Rotating placeholder "Try: design a CRISPR guide RNA…" |

---

## 5. Single-cockpit layout (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ● C4REQBER  F⟨1,1,0⟩  🇬🇧  DeepSeek  💎 12  🌙  00:42/1:30  ▰▰▰▱▱▱▱         │  ← HEADER (1 line)
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ▣ Phase A · Framing                                            ✓ 8s          │
│  System: CRISPR off-targets in T-cells. Class: biotech. Domain: precision     │
│  medicine. Complexity: 0.74. Entities: 23. Edges: 41.                          │
│                                                                                  │
│  ▣ Phase B · Knowledge acquisition                            ✓ 14s         │
│  📚 12 sources fired: openalex (4) · crossref (2) · arxiv (3) · doaj (2)        │
│  🔍 Top: Doench JG et al. · Nature Biotech 2016 · 1847 citations · [o] Open   │
│                                                                                  │
│  ▣ Hypothesis #1 — confidence 0.87                             NEW             │
│  "Use truncated 17-nt guide RNAs with NGG PAM + chemically-modified           │
│   2′-O-methyl at three terminal positions to reduce off-target binding …"     │
│  ↳ derived from: 3 papers · 5 tests proposed · novelty 0.78 · cost $1,240     │
│     [o] Open  [y] Copy  [e] Export  [v] Verify  [→] Run sim                    │
│                                                                                  │
│  ▣ Phase E · Simulation                                       ⏸ queued        │
│  Engine: OpenMM | 3,200 steps | ETA 2 min | queued after Hypothesis #1          │
│                                                                                  │
│  ▣ (history)                                                                       │
│  ▣ #10 sleep+memory · 2 days ago · quality S · 4 papers                          │
│  ▣ #9  language gene transfer · 5 days ago · quality A · 7 papers                │
│                                  [ scroll for more ↓ ]                           │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ ▶ DISCOVER  ⌘                                                  ⏵ RUNNING 0.42$ │  ← FOOTER (1)
├──────────────────────────────────────────────────────────────────────────────────┤
│  Try: design a CRISPR guide RNA with minimal off-targets in T-cells             │  ← INPUT (3 lines)
│  _                                                                              │
│      [Enter] Run  [Shift+Enter] Multi-line  [Tab] Mode  [Esc] Cancel            │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Deprecation в v9

| Что | Что с ним |
|---|---|
| 21 экран-оверлеев | **Удаляются** (v8 продолжает их иметь) |
| 3-колоночный layout | **Заменяется** на 4-регион (header/feed/input/footer) |
| Mascot cube | **Демотируется** в header avatar (1 cell, emotion = цвет) |
| Result panel | **Растворяется** в feed (cards) |
| 24 хоткея | **Сжимаются** до 8 (Enter, Tab, Esc, Ctrl+C, Ctrl+T, Ctrl+S, Ctrl+F, ?) |

---

## 7. Компоненты v9 (P0-P3)

### P0 — must для запуска

| File | LOC | Описание |
|---|---|---|
| `widgets/feed.go` | 400 | Scrollable card list, follow-mode |
| `widgets/card_*.go` (8 files) | 80×8 = 640 | Phase/Hypothesis/Paper/Code/Verification/Error/Synthesis/Empty cards |
| `widgets/progress.go` | 80 | Per-phase inline progress bar |
| `widgets/footer.go` | 200 | Narrative status (mode + action + cost + chips) |
| `widgets/header.go` | 50 | 1-line header |
| `widgets/inputbar.go` | 250 | Rotating placeholders, token counter, mode badge as button |
| `view.go` | 250 | Compose 4-region layout |
| `update.go` | 700 | FeedMsg handlers, ~8 hotkeys |
| `layout.go` | 100 | 4-region geometry |
| `i18n/pipeline/*` | Python ~600 | 5-pass translation pipeline |
| `i18n/glossary/c4_science_terms.json` | 60 terms | Cross-contamination guard |
| **Total P0** | **~3,200 LOC** | |

### P1 — polish (1-2 недели)

- `widgets/palette.go` (200) — bottom-sheet command palette
- `widgets/help_card.go` (150) — inline help (не overlay)
- `styles/card.go` (100) — per-card-type colors
- `i18n/{zh,ja,de,ar,hi}.toml` (full coverage, 7 langs)

### P2 — discovery-friendly

- Welcome card (first run)
- Cost predictor в input bar
- Smart suggestions
- History peek
- Auto-export on S-rank

### P3 — gamification

- Streak counter
- Persona evolution
- Citation network
- Field mastery

---

## 8. Интеграция с полным функционалом c4reqber backend

### 8.1 Что уже работает (подтверждено в первой сессии)

- 95 endpoints в `src/api/server.py`
- 43 knowledge sources (OpenAlex, DOAJ, Crossref, ArXiv, EuropePMC, etc.)
- Discovery pipeline с 7 фазами A-G
- SSE streaming
- C4 navigation (`/v8/discover/navigate-c4`)

### 8.2 Что v9 добавляет

**Backend изменения НЕ ТРЕБУЮТСЯ.** v9 — чисто UI. Используем существующие endpoints:

| v9 feed event | Backend endpoint |
|---|---|
| `PhaseCard A: Framing` | `POST /v8/discover/c4-navigate` |
| `PhaseCard B: Knowledge acquisition` + paper cards | `GET /v8/knowledge/search` (через SSE events) |
| `PhaseCard C: Gaps` | Phase msg from `GET /v8/discover/status/{job_id}` |
| `PhaseCard D: Hypotheses` | Phase msg + hypothesis events |
| `PhaseCard E: Simulation` | Phase msg |
| `PhaseCard F: Dissertation` | Phase msg |
| `PhaseCard G: Quality control` | Phase msg + JobCompleteMsg |
| HypothesisCard | parsed from JobCompleteMsg.result.hypotheses |
| PaperCard | parsed from JobCompleteMsg.result.papers |
| VerificationCard | `POST /v8/verify` (новый, отдельный flow) |
| ExportAction | `POST /v8/export/{md,json,html,bib}` (через palette) |

**Все 95 endpoints остаются доступны через palette** (`:browse-endpoints` или вручную через URL bar).

### 8.3 Реальные преимущества v9

1. **Latency видна пользователю:** phase card показывает реальное время каждой фазы.
2. **Cost в реальном времени:** footer обновляется после каждого LLM-вызова.
3. **SSE в feed:** backend events стримятся как `AppendCardMsg`, real-time.
4. **Source provenance:** каждая paper card имеет `↳ derived from: source X` — пользователь доверяет.

---

## 9. Roadmap 6.2 → 10/10 (v2)

| Iter | Score | Scope | Timeline |
|---|---|---|---|
| **v8.5.0** | 6.2→6.8 | Bug fixes в v8 + i18n native-speaker audit | 1 неделя |
| **v9.0** | 6.8→7.5 | **Новая `v9/` директория.** Минимальный cockpit: feed + 3 card types + basic header/footer | 2 недели |
| **v9.1** | 7.5→8.0 | + остальные card types (Paper, Code, Verification) + SSE integration | 1.5 недели |
| **v9.2** | 8.0→8.5 | + palette (`:browse-endpoints`) + help card + input placeholders | 1 неделя |
| **v9.3** | 8.5→9.0 | + LLM-pipeline переводов (5 passes) — 5 langs (zh/ja/de/ar/hi) | 1 неделя |
| **v9.4** | 9.0→9.5 | + snapshot tests (120 golden files), high-contrast theme, per-mode colors | 1 неделя |
| **v9.5** | 9.5→10.0 | + gamification (P3), native human audit (optional, $200/lang) | 1 неделя |

**Total:** ~8 недель, 1 разработчик.

---

## 10. Конкретные шаги на старт (после твоего "погнали")

1. **Создать структуру** `src/tui/v9/` с `go.mod`, минимальным `main.go` (копирующий v8 как стартовую точку).
2. **Добавить CLI flag** `--tui-version v8|v9` в общем шелле или в каждой TUI.
3. **Создать `i18n/pipeline/`** — Python скрипты + glossary + Makefile.
4. **Запустить pipeline для EN→RU** (ты автор), EN→ZH, EN→JA (наиболее нужные первыми).
5. **Реализовать 4-region layout** (header + feed + input + footer) в `v9/view.go`.
6. **Реализовать `feed.go`** + 3 базовых card types (Phase, Hypothesis, Empty).
7. **Wire backend events** → `AppendCardMsg` через SSE.
8. **CI test:** `go test` + golden snapshot tests.
9. **Manual TUI run** (твоё тестирование, ты в реальном терминале).
10. **Iterate** по твоему фидбэку.

---

## 11. Open decisions (нужен твой ответ)

1. **CLI binding** — два бинаря `c4tui-v8` + `c4tui-v9`, или один бинарь с флагом `--tui-version`? (рекомендую один бинарь, флаг)
2. **v8 навсегда** — оставляем навсегда как legacy branch, или помечаем deprecated и через 2 версии удаляем?
3. **i18n phase 1** — стартуем с EN+RU (ты сам), ZH/JA через LLM-pipeline (~$15), или ждём human translators для всех 7?
4. **Backend integration depth** — v9 использует только SSE feed events, или делаем full 2-way binding (v9 может отправлять commands в backend)?
5. **Splash** — у v8 был длинный (crystal→dissolve→waiting). У v9 сделать мгновенный (50ms) или такой же артистичный?

---

## 12. Связанные планы (backlog)

### 📋 `tui-v9-translation-stack-plan.md` (Phase 2 — translations)
Детальный breakdown **как именно** переводить 7 языков:
- **Tier 1: HY-MT1.5-1.8B** (Tencent Hunyuan) — специализированная translation-only модель, 90% Gemini-3.0-Pro, 33 языка, terminology intervention, 1.1GB на Mac через LM Studio, **$0**
- **Tier 2: Helsinki-NLP/opus-mt-tc-big-{src}-{tgt}** — per-pair fallback
- **Tier 3: NLLB-200-distilled-600M** — language detection (cross-contamination guard)
- **Tier 4: OpenRouter→claude-haiku-4.5** — optional style refinement (~$2-3)
- **Realistic total cost: $0-4** (не $50 как ошибочно считал)
- **Glossary: 60+ научных терминов** с per-language правильными формами — структурная защита от cross-contamination

Когда: после v9.0 (минимальный cockpit) или по запросу. Содержит concrete `lms add` команды и `i18n/pipeline/translate_hymt.py` скрипт-скелет.

---

## 13. Inspiration Library (Go-TUI-штуковины для v9)

Реальный research (brave+apify, ~30 источников). Все ссылки — **первоисточники**, не "AI-агитация".

### 13.1 Charm Ecosystem (Charmbracelet) — primary inspiration

Charm — это **фабрика** TUI-компонентов, используемая в **25 000+ production apps** (от open-source до enterprise). Каждый проект вдохновлён разным аспектом v9.

| Проект | Stars | Что берём для v9 | URL |
|---|---|---|---|
| **Bubble Tea** (TUI framework) | 35k+ | Базовый фреймворк, Elm Architecture, Msg/Cmd паттерн. v2 (Feb 2026) — 10x faster. | [github.com/charmbracelet/bubbletea](https://github.com/charmbracelet/bubbletea) |
| **Bubbles** (TUI components) | 8.5k | **БЕСПЛАТНЫЕ production-ready компоненты**: spinner, textinput, textarea, viewport, list, table, progress, paginator, help, key, timer, stopwatch, filepicker, cursor. **Используем** `viewport` для feed, `textarea` для input, `spinner` для "loading phase", `progress` для per-phase bars, `help` для keymap, `key` для keymap management. | [github.com/charmbracelet/bubbles](https://github.com/charmbracelet/bubbles) |
| **Lip Gloss** (style engine) | 9k+ | CSS-подобный style engine: `Style().Foreground(...).Padding(0,1).Render(text)`. Для per-card-type colors в v9. | [github.com/charmbracelet/lipgloss](https://github.com/charmbracelet/lipgloss) |
| **Huh?** (forms) | 6k+ | **Интерактивные формы** с валидацией, focus, accessibility. Используем для settings-palette (`:settings`). | [github.com/charmbracelet/huh](https://github.com/charmbracelet/huh) |
| **Harmonica** (animation) | 2k+ | Physics-based spring animation. Для pulsing phase indicators, particle effects. | [github.com/charmbracelet/harmonica](https://github.com/charmbracelet/harmonica) |
| **Wish** (SSH apps) | 2k+ | Если когда-нибудь захотим запустить TUI через SSH — это оно. | [github.com/charmbracelet/wish](https://github.com/charmbracelet/wish) |
| **Glamour** (markdown) | 3k+ | Stylesheet-driven markdown renderer. **Используем** для рендера hypothesis/paper content в feed cards. | [github.com/charmbracelet/glamour](https://github.com/charmbracelet/glamour) |
| **Log** (logger) | 1k+ | Structured logger, "This is fine." branding. Для backend.ts log forwarding в TUI footer. | [github.com/charmbracelet/log](https://github.com/charmbracelet/log) |
| **Crush** ⭐ | 25.2k | **Главный inspiration** для v9! Glamourous agentic coding TUI — multi-session, multi-LLM, real-time streaming agent activity, LSP, MCP, sessions, workspaces, embedded chat. **Это reference-impl** для single-cockpit with live-streaming. | [github.com/charmbracelet/crush](https://github.com/charmbracelet/crush) |
| **Soft Serve** | 6k+ | Git server TUI, single-screen data browser. Inspiration для streaming log/result display. | [github.com/charmbracelet/soft-serve](https://github.com/charmbracelet/soft-serve) |
| **Mods** | 2k+ | AI CLI tool, single-stream chat style. | [github.com/charmbracelet/mods](https://github.com/charmbracelet/mods) |
| **Glow** | 15k+ | Markdown reader TUI. Inspiration для rich-text rendering в feed cards. | [github.com/charmbracelet/glow](https://github.com/charmbracelet/glow) |
| **Skate** | 1k+ | KV-store TUI. Inspiration для keybinding UI. | [github.com/charmbracelet/skate](https://github.com/charmbracelet/skate) |
| **Bubblezone** | 1k+ | Mouse region tracking — clickable areas in TUI. **Используем** для clickable cards в feed. | [github.com/charmbracelet/bubblezone](https://github.com/charmbracelet/bubblezone) |
| **Reflow** | 500+ | ANSI-aware text wrapping/indenting. **Используем** для длинных hypothesis text в cards. | [github.com/muesli/reflow](https://github.com/muesli/reflow) |
| **Termenv** | 700+ | Terminal capability detection (color, unicode, mouse). **Используем** для адаптивного color theme. | [github.com/muesli/termenv](https://github.com/muesli/termenv) |
| **Additional Bubbles** (community) | 500+ | Community-maintained extensions. **Копаем сюда** для готовых card/feed компонентов. | [github.com/charm-and-friends/additional-bubbles](https://github.com/charm-and-friends/additional-bubbles) |

### 13.2 Gold-Standard TUI Apps (production-tested patterns)

| Проект | Stars | Что берём | URL |
|---|---|---|---|
| **lazygit** (Jesse Duffield) | 70k+ | **3-pane classic TUI**: status + files + diff. v1-pane commit graph. j/k navigation, `space` для stage, `c` для commit. **Ref** для single-screen density. | [github.com/jesseduffield/lazygit](https://github.com/jesseduffield/lazygit) |
| **lazydocker** | 45k+ | Тот же автор, та же модель. Ref для container/services display. | [github.com/jesseduffield/lazydocker](https://github.com/jesseduffield/lazydocker) |
| **k9s** | 30k+ | Real-time cluster monitoring, dynamic data refresh. Ref для live-updating data tables. | [github.com/derailed/k9s](https://github.com/derailed/k9s) |
| **btop** | 25k+ | Beautiful real-time system monitor. Ref для gradient progress bars, color-coded stat cards. | [github.com/aristocratos/btop](https://github.com/aristocratos/btop) |
| **gdu** | 14k+ | Disk usage analyzer TUI. Ref для treemap-style data viz. | [github.com/dundee/gdu](https://github.com/dundee/gdu) |
| **fzf** | 70k+ | Fuzzy finder, single-line. Ref для command palette. | [github.com/junegunn/fzf](https://github.com/junegunn/fzf) |
| **yazi** | 30k+ | Terminal file manager. Ref для async data loading в TUI. | [github.com/sxyazi/yazi](https://github.com/sxyazi/yazi) |
| **atuin** | 25k+ | Magical shell history. Ref для local-first persistence. | [github.com/atuinsh/atuin](https://github.com/atuinsh/atuin) |
| **helix** | 40k+ | Post-modern text editor. Ref для inline help (`:help` not fullscreen). | [github.com/helix-editor/helix](https://github.com/helix-editor/helix) |
| **below** | 5k+ | Time-travel system monitor. Ref для time-series viz. | [github.com/facebookincubator/below](https://github.com/facebookincubator/below) |
| **skim** | 6k+ | Fuzzy finder in Rust. Ref для fuzzy command palette. | [github.com/skim-rs/skim](https://github.com/skim-rs/skim) |
| **gum** (Charm) | 21k+ | Glamorous shell scripts. Ref для shell-scripting-based TUI elements. | [github.com/charmbracelet/gum](https://github.com/charmbracelet/gum) |
| **vhs** (Charm) | 16k+ | Record terminal GIFs. **Используем** для generating visual regression snapshots. | [github.com/charmbracelet/vhs](https://github.com/charmbracelet/vhs) |
| **freeze** (Charm) | 2k+ | Generate images of code. Ref для ASCII code rendering. | [github.com/charmbracelet/freeze](https://github.com/charmbracelet/freeze) |
| **ntcharts** | 2k+ | Terminal charts (line, bar, candlestick). **Используем** для phase progress visualization. | [github.com/NimbleMarkets/ntcharts](https://github.com/NimbleMarkets/ntcharts) |

### 13.3 TUI Design Patterns & Articles

| Источник | Что берём | URL |
|---|---|---|
| **griffen.codes TUI Design Skill** | Interaction patterns dissection fzf/lazygit/k9s/helix — focus management, discoverability, palette patterns. **Ref** для keyboard UX. | [griffen.codes/post/tui-design-skill-claude](https://griffen.codes/post/tui-design-skill-claude/) |
| **Best TUI Apps 2026 (The Tech Basket)** | 9 killer apps analysis: btop, lazygit, oxker, gum, below. | [thetechbasket.com/best-tui-apps](https://www.thetechbasket.com/best-tui-apps/) |
| **9 TUI Apps So Good I Stopped Opening My Browser** | Single-screen density, color, discoverability. | [medium.com/the-software-journal/9-tui-apps-so-good](https://medium.com/the-software-journal/9-tui-apps-so-good-i-stopped-opening-my-browser-a4c622e438c0) |
| **Teaching Claude to Design TUIs** | LLM-driven TUI design — meta doc. | [griffen.codes/post/tui-design-skill-claude](https://griffen.codes/post/tui-design-skill-claude/) |
| **Packagemain Bubble Tea Tutorial** | Elm architecture, Model/Update/View pattern reference. | [packagemain.tech/p/terminal-ui-bubble-tea](https://packagemain.tech/p/terminal-ui-bubble-tea) |
| **Bubble Tea v2 (10x faster) review** | Mar 2026 update, breaking changes — v9 must use v2. | [byteiota.com/bubble-tea-v2](https://byteiota.com/bubble-tea-v2-10x-faster-terminal-uis-for-go-developers/) |
| **Additional Bubbles community** | Cryptic spinner, gradient bars, multi-column lists. Inspiration для vivid card design. | [github.com/charm-and-friends/additional-bubbles](https://github.com/charm-and-friends/additional-bubbles) |

### 13.4 Concrete Components We Will USE in v9 (from research)

Из всего найденного, ниже — то что **реально импортируем** в v9.0:

| Component | Library | Why | LOC saved |
|---|---|---|---|
| `viewport.Model` | bubbles/viewport | **Scrollable feed** с high-perf mode для длинных discovery outputs. Built-in pager keys (PgUp/PgDn/g/G). | ~300 |
| `textarea.Model` | bubbles/textarea | **Multiline input** в inputbar с line numbers, scrolling, paste. | ~150 |
| `textinput.Model` | bubbles/textinput | (опционально) для compact single-line mode. | ~80 |
| `spinner.Model` | bubbles/spinner | "Phase A: Framing..." с rotating frames. 14 styles (DOT, JUMP, PULSE, etc.). | ~50 |
| `progress.Model` | bubbles/progress + Harmonica | Per-phase progress bar с pulsing animation. | ~80 |
| `paginator.Model` | bubbles/paginator | Feed pagination если > 1000 cards. | ~40 |
| `help.Model` | bubbles/help | **Auto-generates** keymap display from `key.Binding` definitions. | ~100 |
| `key.Binding` | bubbles/key | **Remappable keybindings** — пользователь может перебиндить. v9 must support. | ~120 |
| `table.Model` | bubbles/table | Knowledge sources table в palette. | ~60 |
| `list.Model` | bubbles/list | Mode selector в palette, history viewer. | ~80 |
| `filepicker.Model` | bubbles/filepicker | Export to local file (`.md`, `.bib`). | ~80 |
| `timer.Model` + `stopwatch.Model` | bubbles/timer | **Per-discovery timer** в footer (live), cumulative в header. | ~30 |
| `cursor.Model` | bubbles/cursor | Blinking cursor в inputbar. | ~20 |
| `lipgloss.Style` | lipgloss | Per-card-type colors, theme system, borders. | ~150 |
| `harmonica.Spring` | harmonica | Phase transition animations. | ~30 |
| `glamour.TermRenderer` | glamour | Markdown rendering в hypothesis/paper cards. | ~30 |
| `bubblezone` | bubblezone | Mouse clickable areas (cards, mode badge). | ~40 |
| `reflow.*` | reflow | ANSI-aware wrapping для длинных text в cards. | ~30 |
| `termenv` | termenv | Terminal capability detection (adaptive color/mouse). | ~20 |

**Total LOC saved by using bubbles/lipgloss ecosystem: ~1,400 LOC** (vs writing from scratch).
**Total LOC для v9 reduced from ~3,200 to ~1,800.**

### 13.5 Architecture Inspiration (specifically from Crush)

Из чтения кода crush (v0.76.0) — **рекомендации для v9** (не копировать код, а вдохновляться):

1. **Session-based architecture** — каждый discovery = session, sessions list в palette
2. **Workspace sharing** — два TUI подключаются к одному workspace (для multi-user real-time)
3. **Attribution** — `Generated with c4reqber v9` в каждом export
4. **Config hierarchy** — `~/.config/c4reqber/crush.json` (или `c4reqber.json`) > `.crush.json` > env vars
5. **LSP-enhanced** (v10) — gopls/pyright context для code-output cards
6. **MCP** — `c4_solve`, `c4_search`, `c4_verify` уже есть; v9 добавляет client bridge
7. **Crush config skill** — AI-configures-itself через встроенный skill. v9 имеет аналог: `:config` palette.
8. **`crush logs`** — отдельная команда для log viewer. v9: `:logs` в palette.

### 13.6 Tools & Ecosystem for v9 build pipeline

| Tool | Purpose | URL |
|---|---|---|
| **vhs** (Charm) | Record golden TUI snapshots для regression tests | [github.com/charmbracelet/vhs](https://github.com/charmbracelet/vhs) |
| **gotty** | Web-share TUI через браузер (для v10 collab) | [github.com/yudai/gotty](https://github.com/yudai/gotty) |
| **asciinema** | Record terminal sessions для demos | [github.com/asciinema/asciinema](https://github.com/asciinema/asciinema) |
| **ttyd** | TUI → web (как gotty, но проще) | [github.com/tsl0922/ttyd](https://github.com/tsl0922/ttyd) |
| **Mermaid/GraphViz** | ASCII graph rendering для proof graph cards | [mermaid.js.org](https://mermaid.js.org/) |

### 13.7 What we WILL NOT do (anti-patterns observed)

- ❌ **Не копируем код lazygit** (3-pane не подходит для v9 vision)
- ❌ **Не используем tview** (legacy framework, не Elm-style)
- ❌ **Не пишем свой viewport** (используем bubbles)
- ❌ **Не пишем свой style engine** (используем lipgloss)
- ❌ **Не используем ncurses bindings** (только charm-bubbletea)

---

## 14. Game Inspiration Library (Go TUI + 2D игры + effects)

Расширенный research (~30 источников) для v9 — игры, движки, эффекты, анимации, sci-fi. **Люди реально креативят** — целые awesome-листы с 100+ проектами.

### 14.1 TUI-игры на Bubble Tea (production-ready)

| Проект | Stars | Жанр / Что берём | URL |
|---|---|---|---|
| **Tetrigo** ⭐ | 671 | **Tetris по официальному 2009 Design Guideline**. Smooth grid, scoring, hold mechanics, leaderboard (SQLite). **Ref** для real-time game loop, tick-based rendering, keybinds (Q/W/E/A/S/D + space). | [github.com/Broderick-Westrope/tetrigo](https://github.com/Broderick-Westrope/tetrigo) |
| **Signls** ⭐ | - | **Generative MIDI sequencer** для live performance. Real-time control, animation, VU-meters. **Ref** для streaming visual feedback, color-coded state, animated meters. | [github.com/emprcl/signls](https://github.com/emprcl/signls) |
| **Glow** (Charm) | 15k | Markdown reader TUI. **Ref** для rich-text rendering в feed cards. | [github.com/charmbracelet/glow](https://github.com/charmbracelet/glow) |
| **Cemetery Escape** | 100+ | Terminal RPG на bubbletea. **Ref** для story/narrative flow в TUI. | [github.com/tom-on-the-internet/cemetery-escape](https://github.com/tom-on-the-internet/cemetery-escape) |
| **Superfile** (yorukot) | 7k+ | File manager. **Ref** для nested navigation в palette. | [github.com/yorukot/superfile](https://github.com/yorukot/superfile) |
| **chezmoi** | 16k+ | Dotfile manager. **Ref** для status indicators + diff display. | [github.com/twpayne/chezmoi](https://github.com/twpayne/chezmoi) |
| **gh-dash** | 6k+ | GitHub PRs/issues dashboard. **Ref** для action-rich card lists. | [github.com/dlvhdr/gh-dash](https://github.com/dlvhdr/gh-dash) |

### 14.2 Ebitengine (2D игры, 100+ проектов в awesome-list)

**Ebitengine** = самая живая Go game-библиотека, 100+ игр в [sedyh/awesome-ebitengine](https://github.com/sedyh/awesome-ebitengine). Берём идеи, **НЕ сам engine** (TUI ≠ pixel graphics). Адаптируем в ASCII/Unicode.

| Проект | Жанр | Что берём для v9 |
|---|---|---|
| **aaaaxy** (divVerent) | Non-Euclidean 2D puzzle | **Non-Euclidean C4 navigation** — путь через Z₃³ куб с variable perspective |
| **roboden-game** (quasilyte) | Indirect-control RTS | **Multi-agent visualization** — feed показывает 5+ параллельных hypothesis evolutions |
| **escort-mission** (sinisterstuf) | Post-apoc dog escort | **Path-following animation** в feed — hypothesis line ведёт к verification card |
| **tetriverse** (Critters) | Tetris IN REVERSE | **Reverse logic** — пересмотр данных с конца, timeline scrubber |
| **retromancer** (ketMix) | Time-rewind bullet-hell | **Time-rewind interaction** — `Ctrl+Z` откатывает последний feed card |
| **monovania** (tslocum) | Metroidvania | **Map explorer** — keyboard navigation across full feed history с breadcrumbs |
| **feta-feles** | Bullet hell with pet cat | **Boss patterns** = cool card animations (spiral, sweep, burst) |
| **games-sokoban-go** (x-hgg-x) | Sokoban | **Grid-push animation** = drag hypothesis through pipeline phases |
| **game-of-life-ebiten** | Conway's Game of Life | **Cellular automaton viz** = live hypothesis evolution в corner of feed |
| **fire** (dim13) | Doomfire effect | **🔥 Real-fire animation** в card borders (100fps color decay) |
| **charm-matrix** (RadhiFadlillah) | cmatrix clone | **Matrix rain background** в idle phase (subtle, behind text) |
| **skulls** (rootVIII) | Columns-like | **Column-shifting** = fluid discover/flash/turbo mode switcher |
| **puzzle/sokoban** | Puzzle | **Push state transitions** = state machine visualization |
| **bouncing-balls-ebiten** | Physics balls | **Bouncing tokens** in input field (each char = particle) |
| **raycaster-go** | 3D raycaster | **Fake 3D exploration** of pipeline (3 phases deep) |

### 14.3 ECS / Game-фреймворки (inspiration для v9 architecture)

| Фреймворк | Что берём |
|---|---|
| **donburi** (yohamta) | **ECS для feed cards** — каждая card = entity, components = title/source/expandable, systems = render |
| **ark** (mlange-42) | **Archetype-based design** — C4 cube = archetype, 27 instantiations |
| **mizu** (sedyh) | **ECS framework for TUI** — could v9 cards use ECS? |
| **egriden** (greenthepear) | **Grid-based games** — ref для C4 grid (3×3×3) |
| **gween** (tanema) | **Tweening library** — smooth card transitions (HypothesisCard slides in from right) |
| **ganim8** (yohamta) | **Animation library** — sprite-style card animations |
| **kage / kagei / kageviewer / kageland / luluka** | **Kage shader language** — мог бы использоваться для terminal "shaders" (color gradients, post-processing) |

### 14.4 Физика / Генеративное / Demoscene

| Проект | Что берём |
|---|---|
| **protozoa** (Zebbeni) | Simulation of protozoan behavior = **Hypothesis swarm evolution** в feed |
| **balls-ebiten** (icza) | Bouncing balls with gravity = **Cursor spark particles** на input |
| **biogo** (Scrimgeour) | Genetic simulator = **Hypothesis genetic algorithm** viz |
| **gween** + **ganim8** + **nature-of-code-ebiten** | Springs, easing, Conway, automata = **Living feed animations** |
| **aaeaxy** (non-Euclidean) | Variable perspective = **C4 cube с adjustable projection** |
| **retromancer** (time rewind) | Time rewind interaction = **Ctrl+Z откатывает feed card** |
| **tps-vs-fps** tutorial | Game loop explanation = **60fps ticker в footer** |
| **kage-desk** (shader intro) | Shader tutorials = **gradient bars в feed** |

### 14.5 Audio (для delightful UX)

| Проект | Что берём |
|---|---|
| **resound** (SolarLune) | Sound effects = **pipeline phase transitions с subtle beeps** (если включено) |
| **xm** (quasilyte) | XM module player = **ambient background music в TUI** (opt-in, off by default) |

### 14.6 Физика / Collision (для feed card layout)

| Проект | Что берём |
|---|---|
| **resolv** (SolarLune) | 2D collision = **cards не перекрываются**, automatic layout |
| **cp** (jakecoffman) | Chipmunk2D = **physics-based card stacking** (drag, drop, bounce) |
| **paths** (SolarLune) | Pathfinding = **auto-route hypothesis through pipeline** (visually) |

### 14.7 Other TUI Tools (niche, but cool)

| Проект | Что берём |
|---|---|
| **termgine** (C#) | Terminal game engine inspiration |
| **gruid** (anaseto) | Grid-based UI framework для roguelikes |
| **Aeconomy7/Terminal_ROGUELIKE** | Simple dungeon crawler с AI in pure TUI |
| **ligurio/awesome-ttygames** | Curated 187 ASCII games across languages |
| **radhi/charm-matrix** (CMatrix clone) | **Visual reference для background ambient effects** |
| **SYSC-GO** (Reddit) | TUI animation library (real-time, smooth) |
| **awesome-tuis** (rothgar) | Community list of 100+ TUI projects |
| **awesome-ebitengine** (sedyh) | Best 2D game-engine awesome list |
| **awesome-ascii** (90dy) | 187 ASCII games + tools + libraries |
| **charm-in-the-wild** (charm-and-friends) | Charm ecosystem projects (10+ games) |

### 14.8 Particle / Animation эффекты для v9 feed

| Эффект | Implementation | Где в v9 |
|---|---|---|
| **Matrix rain** background | unicode chars falling per frame | Behind feed in idle state |
| **Doomfire** color decay | palette gradient on chars | Card borders when status changes |
| **Bouncing particles** | physics integration | On keypress в input field |
| **Shake vibrato** | harmonic oscillation | C4 cube on state change (1-2 cells) |
| **Phase swoosh** | sweep animation | Between pipeline phases |
| **Pulsing badges** | scale + color | Mode/Focus/Phase badges |
| **Typewriter effect** | char-by-char reveal | Hypothesis text on first appearance |
| **Burst pattern** | radial explosion | On discovery quality ≥ 0.9 |
| **Spiral pattern** | helix path | Phase transition (succ → done) |
| **Glow tail** | gradient fade | Animated progress bars |
| **Idle breath** | sine wave opacity | Mascot avatar в header |
| **Spark particles** | gravity + friction | On every user keypress |

### 14.9 Примеры «game-feel» в TUI (что реально работает)

Из наблюдений за Tetrigo, Signls, Glow, gh-dash:

1. **Smooth interpolation** — никогда не jump-cut между состояниями, используй `tween` (100-300ms)
2. **Color coding per state** — running=cyan, success=green, warn=yellow, error=red, neutral=gray
3. **Persistent status bar** — bottom 1-2 lines всегда показывают state (как Signls)
4. **Sound feedback** (опционально) — subtle beep на phase transitions
5. **Particle confetti** — на success states (как в Tetrigo line clear)
6. **Smooth scroll** — momentum-based, не jump-to-position
7. **Contextual help** — `?` показывает keymap (уже делаем)
8. **Visual rhythm** — repeating patterns: cards, badges, status line
9. **Surprise & delight** — easter eggs, animations на milestones (как charm-Birthday)
10. **Performance** — 60fps для анимаций, no flicker (Harmonica springs)

### 14.10 Real-world character/animation patterns

- **Tetrigo**: gravity-based piece drop, line-clear flash, hard-drop particle burst
- **Signls**: VU-meters с smooth interpolation, knob controls с inertia
- **Glow**: prose typewriter effect, smooth scroll momentum
- **lazygit**: 3-pane synced cursor, instant diff highlight
- **crush**: real-time streaming LLM responses, "thinking..." indicators
- **lazydocker**: container status with color-coded cards

### 14.11 Длинный список конкретных визуальных паттернов, которые мы МОЖНО адаптировать

1. **Hexagonal grid C4 navigator** (от hex-grid игр) — alternative to 3×3×3 cube
2. **Boss-pattern hypothesis** — hypothesis as "boss" with phases (intro → state 1 → state 2 → defeated)
3. **Tron-like light cycles** — hypothesis paths оставляют colored trails через phases
4. **Sokoban-style state puzzle** — drag hypothesis through phases to reach quality
5. **Tetris-style** quality bars — fill up как tetris line, 1 row per phase
6. **Shooter-style** confidence meter — target shoots down as quality increases
7. **Pong-style** (real-time game) — back-and-forth prompt+response in feed
8. **Tower defense** — knowledge sources as "towers" defending hypothesis
9. **Minesweeper** — first attempts reveal "safe" knowledge gaps
10. **2048** — quality scores combine into next-tier card
11. **Snake** — feed cards form a "snake" of context
12. **Breakout/Arkanoid** — quality gate breaks hypothesis blocks
13. **Frogger** — hypothesis crosses phases "river" of papers
14. **Asteroids** — feed cards float in 3D-like cosmic background
15. **Doom 3D** — raycasted feed of next cards (preview)

**Не обязательно всё** — берём что резонирует с научным/исследовательским вайбом.

### 14.12 Game-Inspired UX паттерны для v9

**Quoting from "Game Feel" book (Steve Swink):**

- **Juice** — мелкие визуальные реакции (shake, flash, particles) на каждое действие
- **Game states** — clear visual transitions (idle → active → success/fail)
- **Player feedback loop** — input → state change → visible response → reward
- **Variable reward** — неожиданные открытия (rare paper, perfect confidence)
- **Social proof** — «you found this hypothesis in N1 scientific frontier»

**Применяем к v9:**

- Каждый input → instant feedback (cursor spark)
- Phase change → swoosh + color + sound
- Hypothesis confidence 0.9+ → burst animation
- New paper from rarest source (Inspire-HEP) → gold glow
- "First of kind" achievement → particles + persistent badge

### 14.13 Concrete "playable" features v9 must have

Помимо обычных utilities, v9 должен иметь **game-feel**:

1. **Smooth ticker в header** (60fps) — постоянно пульсирующий, не flat
2. **Phase progress с анимацией** — 1→7 letters, current phase glowing
3. **Hypothesis card spawn** — slide in from right с ease-out (300ms)
4. **Paper card hover** — на mouse over, glow effect
5. **Discovery burst** — 100 particles + screen shake на quality ≥ S
6. **Cost ticker** — `$0.42` counting up real-time (each token)
7. **Idle mascot** — header avatar breathes (sine wave opacity)
8. **Cancel button** — Esc shows timer counting down для graceful shutdown
9. **Achievement system** — "First CRISPR paper!", "10th discovery!", "100% quality"
10. **Theme unlocks** — complete 10 discoveries → unlock "Scholar" theme

### 14.14 Сколько из этого мы реально возьмём в v9.0

**P0 (must):**
- bubbles viewport + spinner + progress + help (Charm ecosystem)
- lipgloss styling
- Harmonicas spring animations (shake, breath, swoosh)
- Discovery burst particles
- Smooth phase progress
- Cost ticker

**P1 (P2-priority):**
- Cursor spark on keypress
- Hover effects (mouse)
- Typewriter effect
- Hexagonal C4 alternative

**P2 (later iterations):**
- Game-state achievements
- Theme unlocks
- Sound effects
- Background ambient effects (matrix rain, etc.)

---

*Конец плана v2.*
