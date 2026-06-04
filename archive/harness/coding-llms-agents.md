Бро, я разобрал твой список и свежайшие данные по Mistral. Ситуация сильно поменялась — они только что (29 апреля 2026) выпустили **Mistral Medium 3.5**, который по сути убивает необходимость выбирать между кодингом и рейзонингом. Вот мой вердикт:

------

## 🏆 Топ-3 для agentic coding mid-to-long horizon + tools + большой контекст

Table





| Место | Модель                                     | Почему именно она                                            | Контекст | Цена (input/output) |
| :---- | :----------------------------------------- | :----------------------------------------------------------- | :------- | :------------------ |
| **1** | **Mistral Medium 3.5**                     | Это merged-модель: объединила Medium 3.1 (чат), Magistral (рейзонинг) и **Devstral 2 (кодинг)** в один чекпоинт. 128B dense, configurable reasoning effort per request, 77.6% SWE-Bench Verified — выше Devstral 2. Заменила Devstral 2 в Vibe CLI как дефолт. | **256K** | $1.50 / $7.50       |
| **2** | **Devstral 2 (latest)**                    | Если Medium 3.5 по каким-то причинам не зашёл — это чистый кодинг-специалист. 123B dense, 72.2% SWE-Bench, лучший tool-calling в линейке Mistral, заточен под мультифайловые рефакторы и long-horizon агентские циклы. | **256K** | $0.40 / $1.20       |
| **3** | **Mistral Large 3** (675B MoE, 41B active) | Флагман для случаев, когда нужен максимальный рейзонинг + кодинг + мультимодальность. Но для чистого агентного кодинга Medium 3.5 эффективнее и дешевле. | **256K** | $0.50 / $1.50       |

------

## 🔥 Почему Medium 3.5 — главный выбор

**Ключевой инсайт:** Mistral сделала ставку на **merged-модели** вместо отдельных специалистов. Medium 3.5 — это один чекпоинт, который переключается между режимами через `reasoning_effort` параметр. 

Для твоих задач (agentic coding + tools + long horizon) это идеально:

- **Agentic benchmarks:** 91.4% на τ³-Telecom (телеком-агентские задачи), 77.6% SWE-Bench Verified 
- **Tool calling:** native function calling, parallel tool calls, structured outputs — всё на уровне 
- **Self-hosting:** влезает на 4 GPU (H200 node или 2×H100) — если захочешь локально 
- **Open weights:** modified MIT license, можно качать с Hugging Face 

**Trade-off:** output дорогой ($7.50/M), но для агентного кодинга это норм — ты платишь за качество мультишаговых цепочек.

------

## 🗑️ Что НЕ использовать (legacy / перекрытые модели)

Table





| Модель                                    | Почему skip                                                  |
| :---------------------------------------- | :----------------------------------------------------------- |
| **Devstral Small / Small 2 / Small 2505** | Для агентного кодинга слабоваты, контекст меньше, нет long-horizon stamina |
| **Mistral Medium 3 / 3.1 / 3.5 (старая)** | Medium 3.5 (новая 128B) их полностью заменила                |
| **Magistral Medium / Small**              | Влиты в Medium 3.5, отдельно не нужны                        |
| **Mistral Large 2.1 / Large (latest)**    | Legacy pricing ($2/$6), уступают Large 3 и Medium 3.5        |
| **Mistral Small 3.2 / 4 / Nemo / 7B**     | Для твоего use case слишком мелкие                           |
| **Mixtral 8x7B / 8x22B**                  | MoE-архитектура, устарели, нет agentic focus                 |
| **Ministral 3B / 8B**                     | Edge-модели, не для кодинг-агентов                           |
| **Mistral Embed**                         | Это embedding-модель, не для генерации                       |
| **Pixtral Large / 12B**                   | Vision-специфичные, если не нужна мультимодальность — избыточны |
| **Codestral**                             | Устарел, функциональность влита в Medium 3.5 и Devstral 2    |

------

## 💡 Моя рекомендация для твоего стека

plain

Copy

```plain
Основной движок:    Mistral Medium 3.5 (256K, merged, agentic)
Фallback для кодинга: Devstral 2 (если Medium 3.5 "размыливает" код)
Быстрые задачи:       Ministral 8B (только если нужна скорость, не качество)
```

Если работаешь через **OpenClaw / Kilo Code** — Medium 3.5 уже доступна как дефолт в Kilo Code с 174 tok/s 

. Через **Vibe CLI** — она там тоже дефолт с 29 апреля 

.

**По ценам:** Medium 3.5 дороже Devstral 2 на input ($1.50 vs $0.40), но если считать end-to-end стоимость агентской сессии (где много output-токенов на генерацию кода), Devstral 2 может оказаться дешевле. Тестируй A/B на реальных задачах

------

## 🏆 ТОП-5: Кого брать в работу

Table





| #     | Модель                      | Почему именно она                                            | Контекст         | SWE-Bench V | Особенности                                       |
| :---- | :-------------------------- | :----------------------------------------------------------- | :--------------- | :---------- | :------------------------------------------------ |
| **1** | **NVIDIA Nemotron 3 Super** | Лучший open-модель для агентов. 85.6% на PinchBench (OpenClaw-агент), 1M контекст, Mamba-Transformer гибрид — линейное время на длинных последовательностях, goal drift минимален. Обучен в 15 RL-средах NeMo Gym. | **1M**           | ~75%        | MTP speculative decoding 2-3x speedup, latent MoE |
| **2** | **Qwen3 Coder 480B A35B**   | SOTA на SWE-Bench среди open-моделей. 73.4% Verified, 51.5% Terminal-Bench 2.0. Thinking Preservation для stable multi-turn reasoning. Мультимодален (текст/картинка/видео). | **262K** (до 1M) | **73.4%**   | Apache 2.0, extendable context                    |
| **3** | **Poolside Laguna M.1**     | Специально под агентный кодинг. 72.5% SWE-Bench V, 46.9% Pro. Заточен под Poolside Agent workflows: дебаг, рефактор, тесты, итерации. 225B MoE, 23B active. | **128K**         | **72.5%**   | Бесплатно через OpenRouter!                       |
| **4** | **Tencent Hy3 preview**     | 295B MoE, 74.4% SWE-Bench V, 67.1% BrowseComp. Configurable reasoning (disabled/low/high). Уже интегрирован в Tencent CodeBuddy — значит, под кодинг заточен серьёзно. | **256K**         | **74.4%**   | Бесплатно, fast/slow thinking                     |
| **5** | **inclusionAI Ling-2.6-1T** | Триллион параметров, "fast thinking" = дешевле в 4x. #9 в Code Mode Kilo Code, #3 в Debug. Для масштабных агентских workflow — топ. | **262K**         | ~70%        | Бесплатно в Kilo CLI!                             |

------

## ⚡ Бонус: Локальный вариант на твой M3 Max 48GB

Table





| Модель                      | Почему                                                       | Параметры | RAM на M3 Max    |
| :-------------------------- | :----------------------------------------------------------- | :-------- | :--------------- |
| **Poolside Laguna XS.2**    | 33B total / 3B active, **влезает на 36GB RAM**. 68.2% SWE-Bench V, native reasoning, interleaved thinking between tool calls. Apache 2.0. | 33B MoE   | ~28-32GB в 4-bit |
| **Nemotron 3 Nano 30B A3B** | 1M контекст (!), Mamba-Transformer, 3.6B active. 4x faster inference. Работает в llama.cpp на Mac. | 31.6B MoE | ~24-28GB в Q4    |
| **Gemma 4 26B A4B**         | 26B total / 4B active, 256K context, multimodal, native function calling. Локально через Ollama/LM Studio. | 26B MoE   | ~18-22GB в 4-bit |

**Laguna XS.2** — твой лучший выбор для локального агентного кодинга. Он специально спроектирован под "local machine" и agentic coding. 

------

## 🗑️ SKIP — не трать время

Table





| Модель                   | Почему skip                                                  |
| :----------------------- | :----------------------------------------------------------- |
| **GPT-OSS 120B / 20B**   | OpenAI забросила линейку. 20B — #109 из 115 моделей, 18/100 overall. Агентик — единственный непровальный скор (22.5/100). Это мёртвый проект. |
| **Nemotron 3 Nano Omni** | Мультимодальный, но **не для кодинга**. Топит в OCR, видео, аудио. Для чистого агентного кодинга — Nano 30B A3B лучше и с 1M контекстом. |
| **MiniMax M2.5**         | Хорош для extraction/summarization, но "misses edge cases" в коде. Серверы в Китае — латентность. Не для сложного агентного кодинга. |
| **GLM 4.5 Air**          | 128K контекст, 12B active — слабоват для long-horizon. GLM-5/5.1 гораздо лучше, но их нет в твоём списке. |
| **Nous Hermes 3 405B**   | Устарел (2024), нет свежих данных по агентике. 405B dense — не влезет локально, а через API есть лучше. |
| **Baidu CoBuddy**        | Нет данных по агентике и кодингу. Китайский продуктовый LLM, не заточен под твой кейс. |
| **Ling-2.6-flash**       | Облегчённая версия 1T — меньше параметров, хуже reasoning. Бери 1T если есть. |

------

## 🎯 Моя рекомендация для твоего стека

plain

Copy

```plain
┌─────────────────────────────────────────────────────────────┐
│  ОСНОВНОЙ ДВИЖОК (через Kilo CLI / OpenRouter):            │
│  → Nemotron 3 Super  — если доступен (1M контекст, лучший    │
│    агентик, но может быть платным/ограниченным)             │
│                                                             │
│  → Qwen3 Coder 480B A35B  — если Super недоступен           │
│    (SOTA кодинг, 262K→1M, мультимодален)                   │
│                                                             │
│  ФОЛБЭКИ (бесплатные, high-quality):                        │
│  → Poolside Laguna M.1  — чистый агентный кодинг            │
│  → Tencent Hy3 preview  — лучший reasoning/coding баланс  │
│  → Ling-2.6-1T  — масштаб, скорость, дешевизна             │
│                                                             │
│  ЛОКАЛЬНО (на M3 Max 48GB):                                │
│  → Poolside Laguna XS.2  — 33B/3B active, 128K, agentic    │
│  → Nemotron 3 Nano 30B A3B  — 1M контекст (!), Mamba       │
│  → Gemma 4 26B A4B  — 256K, multimodal, Apache 2.0         │
└─────────────────────────────────────────────────────────────┘
```

**Ключевой инсайт:** Nemotron 3 Super с 1M контекстом и Mamba-архитектурой — это единственная модель в списке, которая решает твою главную боль: **goal drift на длинных агентских сессиях**. Традиционные трансформеры квадратично деградируют на 200K+, а Mamba линейно — можешь держать целый репозиторий + историю агента + tool definitions в контексте без truncation.

----

