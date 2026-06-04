# TURBO-CDI → WorldMonitor Grade: Системный План Апгрейда v7

> **Бенчмарк:** [worldmonitor](https://github.com/koala73/worldmonitor) — 52.5k ★, 8.4k форков, 3598 коммитов, 43 релиза
> **Дата:** 2026-04-25
> **Текущий грейд TURBO-CDI:** 5.5/10
> **Целевой грейд:** 8.5+/10

---

## Summary: Gap Analysis

TURBO-CDI обладает **уникальной архитектурной глубиной** (C4 framework, 7 метамоделей, TRIZ 39×39, 95 паттернов) — аналогов нет. Но по инженерной зрелости проект находится на стадии **технического прототипа**. WorldMonitor демонстрирует, как довести продукт до production-grade через 7 ключевых измерений.

| Измерение | TURBO-CDI (сейчас) | WorldMonitor (бенчмарк) | Разрыв |
|-----------|---------------------|--------------------------|--------|
| **Тестовое покрытие** | ~4.5% (4500 строк) | Unit + Integration + E2E + Visual regression | 🔴 Критический |
| **Модульность кода** | Монолиты по 1000-1500 строк | 86 панельных классов, domain-хендлеры | 🔴 Критический |
| **CI/CD** | 2 workflow, базовый pre-commit | 6+ workflows, 7-step pre-push hook | 🟠 Высокий |
| **API-контракты** | Ручные эндпоинты без схем | Protocol Buffers + кодогенерация (92 proto) | 🟠 Высокий |
| **Документация** | Разрозненные MD, смесь языков | ARCHITECTURE.md, CHANGELOG.md, SECURITY.md, структурированный doc-site | 🟡 Средний |
| **Observability** | Стандартный logging | Sentry + structured logging + health endpoint + аналитика | 🟡 Средний |
| **Безопасность** | Хорошая база (JWT, rate-limit), но .env staged | CSP hashes, CORS hardening, keychain vault, per-session tokens | 🟡 Средний |
| **Desktop-приложение** | Отсутствует | Tauri 2 (macOS/Windows/Linux) + Node.js sidecar | 🟡 Средний |
| **Мультивариантность** | Нет | 5 вариантов из одной кодовой базы | 🟢 Низкий |
| **i18n** | Только EN/RU вперемешку | 21 язык + RTL | 🟢 Низкий |
| **Кэширование** | Базовое Redis/SQLite | 4-tier (seed → memory → Redis → upstream) + ETag + CDN | 🟡 Средний |
| **Инфраструктура** | Docker Compose + K8s | Vercel Edge Functions + Railway relay + Upstash Redis + Convex | 🟡 Средний |

---

## Фаза 1: Фундамент Качества (Недели 1–3)

### 1.1 Тестовое покрытие — с 4.5% до 60%+

**Цель:** Каждый модуль должен иметь тесты. CI блокирует PR при падении coverage.

```
Задачи:
├── [1.1.1] pytest-cov + coverage threshold (80% для core/tests)
│           config: pyproject.toml → [tool.coverage.*]
│           CI: --cov=src --cov-report=term --cov-fail-under=60
├── [1.1.2] Приоритетные модули для покрытия:
│           ├── src/core/cdi_engine.py (332 строки) — ядро, сейчас 0 тестов
│           ├── src/c4/engine.py (318 строк) — когнитивный движок
│           ├── src/llm/multi_provider.py (775 строк) — critical path
│           ├── src/patterns/runner.py (313 строк) — симуляции
│           ├── src/api/v6_router.py (1491 строка) — API слой
│           └── src/triz/bridge.py, contradiction_matrix.py — TRIZ
├── [1.1.3] E2E тесты (Playwright):
│           ├── e2e/solve-flow.spec.ts — полный цикл решения
│           ├── e2e/auth-flow.spec.ts — регистрация/логин
│           ├── e2e/canvas.spec.ts — drag-and-drop графов
│           └── playwright.config.ts
├── [1.1.4] Property-based тесты (Hypothesis для Python):
│           ├── test_hypothesis_c4_states.py — валидация C4 состояний
│           └── test_hypothesis_triz_matrix.py — валидация 39×39
└── [1.1.5] CI интеграция:
            └── .github/workflows/test.yml — PR блокировка при <60% coverage
```

### 1.2 Статическая типизация — mypy для Python

```
Задачи:
├── [1.2.1] Добавить mypy в CI: mypy src/ --strict
├── [1.2.2] Постепенное покрытие типов:
│           ├── Фаза A: src/c4/, src/core/ (критические модули)
│           ├── Фаза B: src/llm/, src/api/
│           └── Фаза C: src/patterns/, src/triz/, src/metamodels/
└── [1.2.3] pyproject.toml конфигурация mypy
```

### 1.3 Модульность — разбивка монолитов

```
Задачи:
├── [1.3.1] src/api/server.py (1466 строк):
│           ├── server.py → делегатор (≤200 строк)
│           ├── api/middleware/cors.py
│           ├── api/middleware/rate_limit.py
│           ├── api/middleware/auth.py
│           ├── api/routers/solve.py
│           ├── api/routers/patterns.py
│           ├── api/routers/triz.py
│           ├── api/routers/c4.py
│           ├── api/routers/search.py
│           ├── api/routers/metamodels.py
│           └── api/routers/plugins.py
├── [1.3.2] src/api/v6_router.py (1491 строка):
│           └── Разбить на v6_routers/* (каждый ≤300 строк)
├── [1.3.3] src/agents/pipeline.py (1049 строк):
│           └── Разбить на pipeline/steps/* (каждый шаг — отдельный модуль)
├── [1.3.4] Убрать module-level singletons (v6_router.py:44-58):
│           └── Использовать FastAPI lifespan + dependency injection
└── [1.3.5] Удалить мёртвые директории:
            ├── src/analytics/
            ├── src/math_engine/
            ├── src/workflows/
            └── api/ (top-level legacy)
```

### 1.4 Технический долг и гигиена

```
Задачи:
├── [1.4.1] Удалить .env.development, .env.production из staging
│           → git rm --cached .env.development .env.production
│           → Проверить .gitignore: .env*
├── [1.4.2] Унифицировать язык файлов → английский
│           ├── docs/upgrades/ → переименовать на EN
│           └── DOCUMENTATION/ → structure in English
├── [1.4.3] Alembic миграции:
│           ├── alembic init migrations/
│           ├── alembic revision --autogenerate -m "initial"
│           └── Makefile: make db-migrate → alembic upgrade head
└── [1.4.4] Pre-push hook (подобно worldmonitor):
            ├── TypeScript typecheck
            ├── Python mypy
            ├── Python ruff
            ├── ESLint
            ├── pytest --cov
            └── Markdown lint
```

---

## Фаза 2: Инженерная Зрелость (Недели 4–6)

### 2.1 Pre-push Validation Pipeline (7 шагов)

```
Создать .husky/pre-push:
┌─────────────────────────────────────────────────┐
│ 1. TypeScript typecheck (tsc --noEmit)          │
│ 2. Python mypy --strict                          │
│ 3. Python ruff check                             │
│ 4. ESLint                                        │
│ 5. pytest --cov --cov-fail-under=60              │
│ 6. Markdown lint (markdownlint-cli2)             │
│ 7. Version sync check (package.json ≡ pyproject.toml) │
└─────────────────────────────────────────────────┘
```

### 2.2 Makefile — Production Grade

```
Добавить цели (по образцу worldmonitor):
├── make install         — install ALL deps (pip + npm + playwright + pre-commit)
├── make lint            — lint check (не просто отчёт, а блокировка)
├── make typecheck       — tsc + mypy (оба стека)
├── make test            — pytest + vitest + playwright (все уровни)
├── make test-backend    — только pytest
├── make test-frontend   — только vitest
├── make test-e2e        — только Playwright
├── make coverage        — открыть HTML coverage report
├── make generate        — кодогенерация из контрактов (Proto/OpenAPI)
├── make clean           — включая .ruff_cache, .mypy_cache
├── make format          — black + prettier (оба стека)
├── make security        — trivy scan + npm audit + pip-audit
├── make release         — tag + changelog + build
└── make help            — show all targets
```

### 2.3 CI/CD — 6+ GitHub Actions Workflows

```
.github/workflows/:
├── test.yml             — pytest + vitest на каждый PR/push
├── typecheck.yml        — tsc + mypy
├── lint.yml             — ruff + ESLint + markdownlint
├── security.yml         — trivy + npm audit + pip-audit (weekly)
├── build.yml            — production build (backend + frontend)
├── build-desktop.yml    — сборка десктоп-приложения (5 платформ)
├── docker-publish.yml   — multi-arch Docker image → GHCR
└── release.yml          — авто-changelog + GitHub Release
```

### 2.4 API Contracts — Proto-first Approach

```
Задачи:
├── [2.4.1] Определить proto/ контракты для ключевых сервисов:
│           ├── proto/turbo-cdi/c4/v1/service.proto
│           ├── proto/turbo-cdi/triz/v1/service.proto
│           ├── proto/turbo-cdi/solve/v1/service.proto
│           ├── proto/turbo-cdi/patterns/v1/service.proto
│           └── proto/turbo-cdi/search/v1/service.proto
├── [2.4.2] Кодогенерация:
│           ├── Python: protoc → pydantic-модели + FastAPI routers
│           ├── TypeScript: protoc → typed clients
│           └── OpenAPI 3.1: автоматическая спецификация
├── [2.4.3] CI: proto-check.yml — проверка свежести генерированного кода
└── [2.4.4] Миграция существующих эндпоинтов на proto-контракты
```

---

## Фаза 3: Observability & Production Readiness (Недели 7–8)

### 3.1 Structured Logging + OpenTelemetry

```
Задачи:
├── [3.1.1] structlog для Python-бэкенда:
│           ├── JSON-формат для production
│           ├── Console-формат для разработки
│           ├── Trace IDs во всех логах
│           └── Интеграция с FastAPI middleware
├── [3.1.2] OpenTelemetry:
│           ├── Traces: все LLM-запросы, API-вызовы, пайплайны
│           ├── Metrics: длительность, ошибки, использование кэша
│           ├── Export: Jaeger / Grafana Tempo
│           └── Sampling: adaptive (100% errors, 10% норма)
├── [3.1.3] Health endpoint (подобно worldmonitor):
│           ├── GET /health — общий статус
│           ├── GET /health/ready — readiness probe
│           ├── GET /health/live — liveness probe
│           └── Per-service статус (DB, Redis, LLM providers, seed freshness)
└── [3.1.4] Sentry integration (frontend + backend):
            ├── src/api/errors.py — Sentry SDK + middleware
            └── web-v2/src/services/sentry.ts — Sentry SDK
```

### 3.2 Кэширование — 4-Tier Hierarchy

```
Текущее: Redis или SQLite (один уровень)
Цель (worldmonitor-style):

┌──────────────────────────────────────┐
│ Tier 1: Bootstrap Seed               │
│   Cron-задачи заполняют Redis        │
│   Предпрогретые кэши для всех доменов │
├──────────────────────────────────────┤
│ Tier 2: In-Memory (per-instance)     │
│   LRU cache, TTL 60-300s             │
├──────────────────────────────────────┤
│ Tier 3: Redis (cross-instance)       │
│   cache stampede protection          │
│   ETag-валидация                     │
├──────────────────────────────────────┤
│ Tier 4: Upstream (LLM / APIs)        │
│   Auto-retry, circuit breaker        │
│   Cost tracking + rate limiting      │
└──────────────────────────────────────┘

Задачи:
├── [3.2.1] Классификация кэшей по TTL:
│           ├── fast (60s) — live solving streams
│           ├── medium (600s) — patterns, plugins
│           ├── slow (1800s) — prior art search
│           └── static (7200s) — C4 states, TRIZ matrix
├── [3.2.2] Cache stampede protection (concurrent miss coalescing)
├── [3.2.3] Seed meta freshness tracking
│           └── seed-meta:{key} → {fetchedAt, recordCount}
└── [3.2.4] Cache-Control headers + ETag для всех API ответов
```

---

## Фаза 4: Продуктовые Фичи (Недели 9–12)

### 4.1 Desktop-приложение (Tauri 2)

```
Задачи:
├── [4.1.1] src-tauri/ — Tauri 2 Rust shell:
│           ├── tauri.conf.json — окна, плагины, CSP
│           ├── src/main.rs — lifecycle, IPC команды, system tray
│           └── capabilities/ — permission model
├── [4.1.2] Python sidecar:
│           ├── src-tauri/sidecar/ — FastAPI running as child process
│           ├── Secret management: OS keychain (не plaintext)
│           └── Fetch patch: перенаправление /api/* → sidecar
├── [4.1.3] Платформы:
│           ├── macOS (ARM64 + Intel)
│           ├── Windows (x64)
│           └── Linux (AppImage)
├── [4.1.4] CI/CD: build-desktop.yml (5-platform matrix build)
└── [4.1.5] Code signing + auto-update
```

### 4.2 Мультивариантная система

```
Задачи:
├── [4.2.1] Варианты из единой кодовой базы:
│           ├── create-invent (полный, по умолчанию)
│           ├── create-engineering (упор на инженерию)
│           ├── create-business (упор на бизнес)
│           └── create-science (упор на научные исследования)
├── [4.2.2] Конфигурация вариантов:
│           ├── src/config/variants/ — плагины, паттерны, LLM-модели
│           ├── Hostname detection: business.turbo-cdi.local → business
│           └── localStorage override для desktop
└── [4.2.3] Vite dev server для каждого варианта:
            ├── npm run dev → full
            ├── npm run dev:eng → engineering
            ├── npm run dev:biz → business
            └── npm run dev:sci → science
```

### 4.3 i18n — Многоязычность

```
Задачи:
├── [4.3.1] i18next для фронтенда:
│           ├── 12 ключевых языков: EN, RU, ZH, ES, AR, PT, DE, FR, JA, KO, HI, TR
│           ├── RTL поддержка (AR)
│           └── Language switcher в UI
├── [4.3.2] Локализация:
│           ├── UI строки → JSON translation keys
│           ├── Документация → /docs/{lang}/
│           └── C4-описания состояний и операторов
└── [4.3.3] Crowdin/GitLocalize интеграция для community translations
```

### 4.4 Документационный сайт (Mintlify / Docusaurus)

```
Создать docs/ структуру worldmonitor-уровня:
├── docs/
│   ├── docs.json / mint.json
│   ├── index.mdx — landing page
│   ├── getting-started/ — installation, quick start
│   ├── architecture/ — C4 framework, pipeline, metamodels
│   ├── api/ — OpenAPI-generated + guides
│   ├── triz/ — TRIZ methodology, 40 principles, matrix
│   ├── patterns/ — pattern library (95+)
│   ├── plugins/ — plugin development guide
│   ├── contributing/ — CONTRIBUTING.md
│   └── security/ — SECURITY.md
```

---

## Фаза 5: Community & Open Source (Недели 13–16)

### 5.1 Community-инфраструктура

```
Задачи:
├── [5.1.1] CODE_OF_CONDUCT.md — Contributor Covenant
├── [5.1.2] CONTRIBUTING.md — детальное руководство:
│           ├── Архитектурный обзор
│           ├── Development setup
│           ├── Coding standards (Python + TypeScript)
│           ├── Pull request process
│           ├── AI-assisted development (как в worldmonitor)
│           └── Добавление новых паттернов/плагинов
├── [5.1.3] SECURITY.md — security policy + responsible disclosure
├── [5.1.4] CHANGELOG.md — структурированный changelog
├── [5.1.5] GitHub Discussions + Issue templates
├── [5.1.6] Discord/Telegram community
└── [5.1.7] DEPLOYMENT-PLAN.md / SELF_HOSTING.md
```

### 5.2 Сравнительная дорожная карта

```
┌──────────────────┬──────────────┬───────────────┬─────────────────┐
│ Измерение        │ До апгрейда  │ После апгрейда│ WorldMonitor     │
│                  │ (5.5/10)     │ (8.5/10)      │ (9/10)           │
├──────────────────┼──────────────┼───────────────┼─────────────────┤
│ Тестирование     │ 4.5%         │ 65%+          │ 3 уровня         │
│ CI/CD            │ 2 workflow   │ 8+ workflows  │ 6+ workflows     │
│ API контракты    │ Ручные       │ Proto-first   │ Proto-first (92) │
│ Пре-пуш хуки     │ 3 шага       │ 7 шагов       │ 7 шагов          │
│ Модульность      │ Монолиты     │ ≤300 строк    │ Панельные классы │
│ Кэширование      │ 1 уровень    │ 4 уровня      │ 4 уровня         │
│ Observability    │ Стандартный  │ OTel + Sentry │ Sentry + health  │
│ Desktop          │ Нет          │ Tauri 2       │ Tauri 2          │
│ Варианты         │ Нет          │ 4 варианта    │ 5 вариантов      │
│ i18n             │ EN/RU        │ 12 языков     │ 21 язык          │
│ Документация     │ Разрозненная │ Doc-site      │ Mintlify         │
│ Безопасность     │ 7/10         │ 8.5/10        │ 8.5/10           │
│ Changelog        │ Нет          │ Структ.       │ 2000+ строк      │
│ Community        │ Нет          │ Discussions   │ Discord/Issues   │
└──────────────────┴──────────────┴───────────────┴─────────────────┘
```

---

## Фаза 6: Continuous Evolution (Постоянно)

### Мета-процессы

```
Задачи:
├── [6.1] Еженедельные Sentry triage (подобно worldmonitor — 26+ issues за спринт)
├── [6.2] Ежемесячные security audit (trivy, pip-audit, npm audit)
├── [6.3] Квартальный architecture review + обновление ARCHITECTURE.md
├── [6.4] Release cadence: минорные каждые 2 недели, патчи по необходимости
├── [6.5] Community issue triage + label automation
└── [6.6] AI-assisted development labelling (claude/gpt/cursor на PR)
```

---

## Приоритеты и Зависимости

```
Фаза 1 (Фундамент) ──────────┬── Фаза 2 (Зрелость)
                              │
                              ├── Фаза 3 (Observability)
                              │
                              └── Фаза 4 (Фичи) ── Фаза 5 (Community)
                                                  │
                                                  └── Фаза 6 (Evolution)
```

**Critical path:** Фаза 1 (3 недели) → Фаза 2 (3 недели) → Фаза 3 (2 недели)
**Параллельно:** Фаза 4 может стартовать после Фазы 1
**Финал:** Фаза 5 и 6 — после стабилизации

---

## Ресурсы и Оценка

| Ресурс | Количество |
|--------|-----------|
| **Общая длительность** | 16 недель |
| **Фаза 1 (Фундамент)** | 3 недели — тесты, mypy, модульность |
| **Фаза 2 (Зрелость)** | 3 недели — CI/CD, Makefile, proto-контракты |
| **Фаза 3 (Observability)** | 2 недели — логи, кэш, Sentry |
| **Фаза 4 (Фичи)** | 4 недели — desktop, варианты, i18n, doc-site |
| **Фаза 5 (Community)** | 3 недели — документы, инфраструктура |
| **Фаза 6 (Evolution)** | Постоянно |

---

## Ключевые Метрики Успеха

- [x] ~~Аудит текущего состояния завершён~~ (2026-04-25)
- [ ] Test coverage > 60%
- [ ] mypy --strict проходит без ошибок
- [ ] Все модули ≤ 300 строк
- [ ] 7-step pre-push hook активен
- [ ] Proto-контракты для 5+ доменов
- [ ] OpenTelemetry traces для всех критических путей
- [ ] Desktop app собрана для 3 платформ
- [ ] 4 варианта из единой кодовой базы
- [ ] Doc-site опубликован
- [ ] CHANGELOG.md ведётся регулярно
- [ ] 12 языков с i18n инфраструктурой
- [ ] 100+ звёзд на GitHub

---

## Приложение: WorldMonitor Grade Markers (Чеклист)

Этот чеклист определяет, что значит "уровень worldmonitor". Каждый пункт — конкретный deliverable.

### Документация
- [ ] `ARCHITECTURE.md` — глубокая архитектурная документация с диаграммами и ссылками на исходники
- [ ] `CHANGELOG.md` — структурированный, с секциями Added/Changed/Fixed/Security/Performance
- [ ] `CONTRIBUTING.md` — полное руководство для контрибьюторов (архитектура, coding standards, PR process)
- [ ] `SECURITY.md` — security policy + supported versions + responsible disclosure
- [ ] `CODE_OF_CONDUCT.md` — Contributor Covenant
- [ ] `SELF_HOSTING.md` — руководство по самостоятельному деплою
- [ ] `DEPLOYMENT-PLAN.md` — план деплоя
- [ ] `AGENTS.md` — гид для AI-агентов (текущее состояние, быстрый старт)
- [ ] Doc-site (Mintlify/Docusaurus) с навигацией

### Код
- [ ] Все модули ≤ 300 строк (исключение: сгенерированный код)
- [ ] TypeScript strict mode (tsc --noEmit без ошибок)
- [ ] Python mypy --strict без ошибок
- [ ] Pre-push hook: 7 шагов валидации
- [ ] Protocol Buffers кодогенерация (клиент + сервер + OpenAPI)
- [ ] CI проверка свежести сгенерированного кода
- [ ] Нет module-level синглтонов (dependency injection)
- [ ] Нет мёртвого кода
- [ ] Единый язык в кодовой базе

### Тестирование
- [ ] Unit тесты: > 60% coverage
- [ ] Integration тесты: API endpoints, DB, Redis
- [ ] E2E тесты: Playwright для критических flow
- [ ] Property-based тесты: Hypothesis для алгоритмов
- [ ] CI блокировка при падении coverage

### Безопасность
- [ ] CSP headers (без unsafe-inline)
- [ ] CORS allowlist (не wildcard)
- [ ] Rate limiting на всех эндпоинтах
- [ ] API keys → header (не query string)
- [ ] Secrets в OS keychain (desktop) / env vars (server)
- [ ] .env НЕ в git (только .env.example)
- [ ] Bot protection middleware
- [ ] Non-root user в Docker
- [ ] CSPRNG для всех ID (crypto.randomUUID)

### DevOps
- [ ] GitHub Actions: 6+ workflows (test, typecheck, lint, security, build, release)
- [ ] Docker multi-arch (amd64 + arm64)
- [ ] Health endpoint (ready/live) для Kubernetes
- [ ] Docker Compose: dev + test + prod конфигурации
- [ ] Makefile: install, lint, typecheck, test, test-e2e, coverage, generate, clean, format, security, release, help
- [ ] Stale bot для issues

### Observability
- [ ] Structured logging (JSON) в production
- [ ] OpenTelemetry traces
- [ ] Sentry error tracking (frontend + backend)
- [ ] Health endpoint с per-service статусом
- [ ] Seed meta freshness tracking
- [ ] Cache hit rate мониторинг

### Desktop
- [ ] Tauri 2: macOS (ARM64, Intel) + Windows (x64) + Linux (AppImage)
- [ ] Python sidecar с аутентификацией
- [ ] OS keychain для секретов
- [ ] Code signing
- [ ] Auto-update
- [ ] Fetch patch для локального API

### Продукт
- [ ] Мультивариантная система (3+ варианта из одной кодовой базы)
- [ ] i18n: 12+ языков с RTL поддержкой
- [ ] Language switcher в UI
- [ ] Ни одной захардкоженной строки
- [ ] Community discussions (GitHub Discussions)
- [ ] Issue templates (bug report, feature request)

### AI Интеграция
- [ ] Multi-provider routing с auto-retry
- [ ] Локальный LLM (Ollama/LM Studio) без API-ключей
- [ ] Browser-side ML (Transformers.js)
- [ ] 4-tier fallback chain (local → cloud 1 → cloud 2 → browser)
- [ ] Cost tracking для всех LLM запросов
- [ ] AI-assisted development policy (как в CONTRIBUTING.md worldmonitor)

---

**Документ будет обновляться по мере выполнения фаз. Каждый завершённый этап — это PR с обновлением этого плана.**
