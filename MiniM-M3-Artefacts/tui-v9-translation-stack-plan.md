# TUI v9 — LLM Translation Stack Plan (PHASE 2)

**Дата:** 2026-06-10
**Связан с:** `tui-v9-cockpit-plan-v2.md` (см. §3 "LLM-pipeline для переводов" — это его детализация)
**Статус:** BACKLOG — выполняется ПОСЛЕ v9.0/v9.1 (минимальный cockpit) или параллельно, если попросишь
**Цель:** Production-grade переводы v1.0 для 7 языков (EN+RU+ZH+JA+DE+AR+HI) с затратами **~$3-4** (не $50 как ошибочно считал ранее)

---

## 0. Контекст — почему это отдельный план

В плане v9 я насчитал **$52** на pipeline переводов (перепутал Claude Sonnet top-tier с реальным). Реальный объём текста — **400 строк × 7 языков = ~6000 слов**. Это **5-6 КБ** в каждом языке. Задача **сильно** меньше чем я думал.

В этом плане — детальный technical breakdown **как именно** потратить $3-4 максимально эффективно, с реальными моделями найденными через research (brave+apify).

---

## 1. Топ open-source translation models (research results)

### 🏆 Tier 1 — Главное оружие: **HY-MT1.5-1.8B** (Tencent Hunyuan)

**Это то что нужно.** Specialized translation-only модель, не general-purpose LLM.

| Spec | Value |
|---|---|
| Параметры | 1.8B (базовая), 7B (pro) |
| Поддержка языков | 33 + 5 диалектов (Tibetan, Mongolian, Uyghur, Kazakh, Cantonese) |
| Покрывает наши 7 | ✅ EN, RU, ZH, JA, DE, AR, HI (все) |
| Качество (vs Gemini-3.0-Pro) | **1.8B = 90%**, **7B = 95%** на WMT25 |
| Mac-готовность | ✅ GGUF (4bit/2bit/1.25bit) + MLX варианты на HF |
| Размер | 1.8B 4bit ≈ **1.1GB**; 2bit = **574MB**; 1.25bit = **440MB** |
| License | Tongyi License (open-source, research-friendly) |
| Спецфичи | terminology intervention, contextual translation, format preservation |
| HF | [huggingface.co/tencent/HY-MT1.5-1.8B-GGUF](https://huggingface.co/tencent/HY-MT1.5-1.8B-GGUF) |
| GitHub | [Tencent-Hunyuan/HY-MT](https://github.com/Tencent-Hunyuan/HY-MT) |
| Paper | [arxiv.org/html/2512.24092v1](https://arxiv.org/html/2512.24092v1) |

**Почему это лучше чем Claude Sonnet за $3/1M:**
- Специализированная (не generalist) — лучше в translation per param
- Terminology intervention (встраивает наш `c4_science_terms.json` нативно)
- $0 за любой объём
- On-device → мгновенный latency, no API rate-limits

### Tier 2 — Per-pair fallback

| Модель | Размер | Best for | Mac-готовность |
|---|---|---|---|
| **Helsinki-NLP/opus-mt-tc-big-{src}-{tgt}** | ~300M | Per-pair narrow (EN-RU, EN-JA, etc.) | ✅ MLX 700MB |
| **Helsinki-NLP/Tatoeba-Challenge** | 0.5-2B | Per-pair, высокое качество | ✅ MLX |
| **NLLB-200-distilled-600M** (Meta) | 600M | 200 языков, lang-detection | ✅ MLX 1.5GB |

### Tier 3 — General-purpose LLM для refine (через OpenRouter)

| Model | Cost | Когда использовать |
|---|---|---|
| `claude-haiku-4.5` (OpenRouter→Bedrock) | $1/$5 per 1M | Style refinement (formal/informal/tone) |
| `llama-3.1-8b-instruct` (OpenRouter→DeepInfra) | $0.04/$0.04 per 1M | Cheap fallback для tone |
| `deepseek-chat-v3.1` (OpenRouter→DeepInfra) | $0.14/$0.28 per 1M | Tech translations |
| `qwen-2.5-72b` (OpenRouter→DeepInfra) | $0.40/$0.40 per 1M | CJK terminological accuracy |
| `grok-4.3` (XAI напрямую) | $3/$15 per 1M | DE/EU multilingual |

### Tier 4 — Tools / orchestrators

| Tool | Use case | URL |
|---|---|---|
| **LM Studio** (у тебя уже есть) | GUI/CLI для GGUF/MLX | lmstudio.ai |
| **mlx-lm** (Apple) | Python пакет для MLX | [github.com/ml-explore/mlx-lm](https://github.com/ml-explore/mlx-lm) |
| **llama.cpp** | C++ runtime + Metal backend | [github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp) |
| **mlx-serve** (ddalcu) | OpenAI-compatible server for MLX | [github.com/ddalcu/mlx-serve](https://github.com/ddalcu/mlx-serve) |
| **mlx-my-repo** (HF Space) | Convert any HF model to MLX | [huggingface.co/spaces/mlx-community/mlx-my-repo](https://huggingface.co/spaces/mlx-community/mlx-my-repo) |
| **LibreTranslate** | Self-hosted REST API | [github.com/LibreTranslate/LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) |
| **LTEngine** | LLM-powered local translation | [github.com/LibreTranslate/LTEngine](https://github.com/LibreTranslate/LTEngine) |
| **Argos Translate** | Offline pure-python (MIT) | [github.com/argosopentech/argos-translate](https://github.com/argosopentech/argos-translate) |
| **Opus-MT server** | Helsinki-NLP per-pair server | [github.com/Helsinki-NLP/Opus-MT](https://github.com/Helsinki-NLP/Opus-MT) |
| **bibproj MLX collection** | Curated MLX quants for translation | [huggingface.co/collections/bibproj/translation-models-mlx](https://huggingface.co/collections/bibproj/translation-models-mlx) |
| **Lingo.dev CLI** | i18n pipeline orchestrator (i18n.json → TOML) | [github.com/lingodotdev/lingo.dev](https://github.com/lingodotdev/lingo.dev) |
| **go-i18n** | TOML → Go map generator | [github.com/nicksnyder/go-i18n](https://github.com/nicksnyder/go-i18n) |

---

## 2. Реальный объём текста для перевода

| Источник | Строк | Слов (EN) | На 7 языков |
|---|---|---|---|
| `i18n.go` текущий | 48 ключей | 110 | 770 |
| Hardcoded widget/screen | 297 | 600 | 4200 |
| Новые v9-компоненты | 50 | 100 | 700 |
| Placeholder examples | 4 примера | 60 | 420 |
| **ИТОГО для v9** | **~400** | **~870 EN** | **~6000 слов** |

Это **5-6 КБ текста** в каждом языке. **Крошечный** объём — никаких $50 не нужно.

---

## 3. 4-Pass Pipeline (Final)

### Pass 1 — Direct translation (HY-MT1.5-1.8B, локально)

```
Tool: LM Studio + HY-MT1.5-1.8B (4bit GGUF, ~1.1GB)
Input: en.toml + glossary c4_science_terms.json
Output: {ru,zh,ja,de,ar,hi}.toml v1.0
Quality: ★★★★☆ (90% Gemini-3.0-Pro level)
Cost: $0 (локально, на твоём Mac)
Time: ~30 min на 7 языков × 50 строк каждый
```

**Ключевое:** HY-MT поддерживает `terminology intervention` — мы передаём наш `glossary/c4_science_terms.json` (60+ научных терминов) прямо в prompt. **Это убивает cross-contamination на этапе генерации**, не на этапе review.

### Pass 2 — Cross-contamination check (NLLB-200-600M, локально)

```
Tool: mlx-lm + facebook/nllb-200-distilled-600M (~1.5GB)
Input: 7 toml файлов
Process: для каждой строки — определить язык (NLLB lang-classifier)
Output: report с подозрительными строками (если в `de.toml` сидит арабский → flag)
Quality: ★★★★★ (100% гарантия отсутствия cross-contamination)
Cost: $0 (локально)
Time: ~5 min
```

### Pass 3 — Style refinement (опционально, через OpenRouter)

```
Tool: claude-haiku-4.5 (OpenRouter→Bedrock)
Use: для строк где tone/formality важна (placeholder examples, mascot musings)
Quality: ★★★★★ (literary-grade)
Cost: ~$2-3 (на 7 языков × 4-5 длинных строк = 30 вызовов)
Skip: если Pass 1 + Pass 2 уже good enough
```

### Pass 4 — Safety fallback для edge cases

```
Tool: deepseek-chat (твой ключ) или OpenRouter→deepseek-chat-v3.1
Use: для строк которые HY-MT вернул с low confidence или пустыми
Cost: $0.50-1
```

### Realistic total cost

| Pass | Tool | Cost |
|---|---|---|
| 1 | HY-MT1.5-1.8B (local) | **$0** |
| 2 | NLLB-200-600M (local) | **$0** |
| 3 | claude-haiku-4.5 (optional) | **$2-3** |
| 4 | DeepSeek safety | **$0.50-1** |
| **ВСЕГО** | | **$0 (минимум) — $4 (полный)** |

---

## 4. Glossary: ключевая защита от cross-contamination

`i18n/glossary/c4_science_terms.json` (60+ научных терминов с per-language правильными формами):

```json
{
  "hypothesis": {
    "zh": "假设", "ja": "仮説", "ko": "가설",
    "ru": "гипотеза", "de": "Hypothese", "fr": "hypothèse",
    "es": "hipótesis", "ar": "فرضية", "hi": "परिकल्पना",
    "en": "hypothesis"
  },
  "verification": {
    "zh": "验证", "ja": "検証", "ko": "검증",
    "ru": "верификация", "de": "Verifizierung",
    "ar": "التحقق", "hi": "सत्यापन"
  },
  "discovery": {
    "zh": "发现",       // НЕ 発見 (JA)
    "ja": "発見", "ko": "발견",
    "ru": "открытие", "de": "Entdeckung",
    "ar": "اكتشاف", "hi": "खोज"
  }
  // ... 60+ ключей
}
```

**HY-MT terminology intervention** встраивает этот glossary в prompt — модель **ОБЯЗАНА** использовать эти формы. Это структурно не даёт ZH утечь в JA.

---

## 5. Concrete steps когда ты скажешь "погнали"

1. **`lms add` HY-MT1.5-1.8B-4bit-GGUF** (через LM Studio CLI) — ~1.1GB download
2. **Тест 1-2 строки** в каждом из 7 направлений — проверка качества + latency
3. **`lms add` NLLB-200-distilled-600M** для lang detection — ~1.5GB
4. **Pass 1:** запуск скрипта `i18n/pipeline/translate_hymt.py` → 7 toml файлов
5. **Pass 2:** NLLB detect → report + auto-fix для flagged строк
6. **Pass 3 (опционально):** через OpenRouter haiku-4.5 для tone
7. **Output:** `src/tui/v9/i18n/{ru,zh,ja,de,ar,hi}.toml` готовы, `i18n.go` сгенерирован
8. **CI test:** `go test ./i18n/...` проверяет 100% coverage × 7 langs
9. **Коммит** с подробным commit message описывающим pipeline + стоимость

---

## 6. Когда выполнять

| Trigger | Phase |
|---|---|
| Сейчас | **НЕ выполняем.** Сохранил как backlog. |
| После v9.0 (минимальный cockpit) | ✅ Pass 1+2 — основное ядро переводов |
| После v9.2 (palette + help) | ✅ Pass 3 (style refine) — polish |
| После v9.4 (snapshot tests) | ✅ Pass 4 + full pipeline audit |
| Production | ✅ Native-speaker human re-pass (опционально, $200-500) |

---

## 7. Deliverable

В конце Phase 2:
- `src/tui/v9/i18n/{en,ru,zh,ja,de,ar,hi}.toml` — все 7 языков, 100% coverage
- `src/tui/v9/i18n/glossary/c4_science_terms.json` — 60+ научных терминов
- `src/tui/v9/i18n/i18n.go` — generated by `go-i18n` from TOML
- `src/tui/v9/i18n/i18n_test.go` — coverage tests
- `src/tui/v9/i18n/pipeline/` — reproducible pipeline (если понадобится re-run)
- `src/tui/v9/i18n/README.md` — документирует pipeline + commits
- `runs/translation-pipeline-{date}.json` — артефакты: timing, costs, quality metrics

---

## 8. Open questions (если захочешь обсудить до старта)

1. **Mac specs** — у тебя M1/M2/M3? Сколько unified memory? (влияет на выбор 4bit vs 8bit quant HY-MT)
2. **Glossary** — хочешь сразу 200+ терминов, или start с 60 (что в плане), расширим по мере?
3. **Refine tier** — обязательно haiku-4.5 для tone, или HY-MT pass 1 достаточно?
4. **Human re-pass** — есть budget на $200-500 для native-speaker audit всех 7 языков? (опционально)

---

*Связан с `tui-v9-cockpit-plan-v2.md` §3. Выполняется по запросу или автоматически после v9.2.*
