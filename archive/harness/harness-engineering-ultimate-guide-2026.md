# 🧠 ULTIMATE HARNESS ENGINEERING GUIDE 2026
## Системный гайд для разработчиков: от архитектуры до production

**Версия:** 1.0 | **Дата:** Май 2026 | **Автор:** Синтез Grok + реальные источники + дополнения

---

## 📋 Оглавление

1. [Что такое Harness Engineering (и почему это не хайп)](#1-что-такое-harness-engineering)
2. [Мета-архитектура: 5+ уровней harness-экосистемы](#2-мета-архитектура)
3. [Уровень 0: Soul / Persona Layer](#3-уровень-0-soul--persona)
4. [Уровень 1: Execution Runtime](#4-уровень-1-execution-runtime)
5. [Уровень 2: Context System + Memory](#5-уровень-2-context-system--memory)
6. [Уровень 3: Capability Surface (Tools + MCP + Skills)](#6-уровень-3-capability-surface)
7. [Уровень 4: Governance Layer](#7-уровень-4-governance-layer)
8. [Уровень 5: Observability & Meta Layer](#8-уровень-5-observability--meta)
9. [MCP: Model Context Protocol — полный разбор](#9-mcp-model-context-protocol)
10. [Multi-Agent Patterns: когда и как использовать](#10-multi-agent-patterns)
11. [Self-Improving Harnesses: мета-цикл](#11-self-improving-harnesses)
12. [Cache-First Design: экономия токенов](#12-cache-first-design)
13. [Sandbox & Security: 8-слойная модель](#13-sandbox--security)
14. [Deployment Patterns: Self-Hosted vs Managed](#14-deployment-patterns)
15. [Голубые океаны 2026-2027: что ещё никто не построил](#15-голубые-океаны)
16. [Roadmap: от MVP до Production (фазы 0-4)](#16-roadmap)
17. [Чек-листы и шаблоны](#17-чек-листы-и-шаблоны)
18. [Приложение A: Терминология](#приложение-a-терминология)
19. [Приложение B: Сравнительная таблица harness-решений](#приложение-b-сравнительная-таблица)

---

## 1. Что такое Harness Engineering (и почему это не хайп)

### 1.1 Эволюция: Software 1.0 → 2.0 → 3.0

| Эра | Парадигма | Что делает человек | Что делает система |
|-----|-----------|-------------------|-------------------|
| **Software 1.0** | Классический код | Пишет правила (if/else) | Исполняет |
| **Software 2.0** | Нейросети | Готовит данные, выбирает архитектуру | Веса «программируются» сами |
| **Software 3.0** | **Prompts + Agents** | **Оркестрирует агентов** | Автономное планирование, вызов инструментов, проверка |
| **Software 4.0** *(прогноз 2027)* | Self-evolving harnesses | Задаёт границы и governance | Агенты сами рефакторят harness для следующих агентов |

**Ключевой инсайт от Карпати (Andrej Karpathy, Sequoia Ascent 2026):** модели становятся commodity (все примерно одинаковые), а **harness определяет, будет ли агент работать в проде или сломается на 50-м шаге**.

### 1.2 Что НЕ является harness

- ❌ Простая CLI-обёртка вокруг API (ранний Aider)
- ❌ «Ещё один wrapper вокруг Claude»
- ❌ Vibe coding без структуры
- ❌ Одноразовый промпт-инжиниринг

### 1.3 Что ЯВЛЯЕТСЯ harness

Harness — это **операционная система вокруг модели**:
- **Runtime**: event loop, checkpoints, snapshots, replay
- **Context**: tiered memory, compaction, artifacts
- **Tools**: MCP, built-in, skills
- **Governance**: policy engine, approvals, sandbox
- **Observability**: tracing, evals, self-improving loops

**Аналогия:** модель = CPU (commodity), harness = вся ОС вокруг (kernel, filesystem, scheduler, security).

### 1.4 Почему это важно прямо сейчас (май 2026)

- **97 млн установок MCP SDK**, 10k+ активных серверов
- **Harness.io** — $5.5B valuation, рост 50%+ YoY
- **Первые tiny-team unicorns** (<10 человек) именно в agentic infra
- Модели меняются каждые 3-4 месяца, **хороший harness переживает GPT-6**

---

## 2. Мета-архитектура: 5+ уровней harness-экосистемы

### 2.1 Визуальная схема

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / SURFACE                           │
│         (CLI, IDE, Telegram, Web, API, ACP)               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 0: SOUL / PERSONA (глобальный, вечный)              │
│  SOUL.md → AGENTS.md → refusal rules → voice consistency   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: EXECUTION RUNTIME (сердце harness)               │
│  Event loop → Checkpoints → Deterministic replay            │
│  Planner + Executor + Reflector (two-agent spine)          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 2: CONTEXT SYSTEM + MEMORY                          │
│  Working (in-context) → Persistent (episodic) → Skill       │
│  Compaction → Artifacts → Vector/RAG                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 3: CAPABILITY SURFACE                               │
│  Built-in tools → MCP servers → Skills → Subagents          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 4: GOVERNANCE LAYER                                 │
│  Policy engine → Risk tiers → Approvals → Sandbox           │
│  PEV-loops → Audit trail → Doom-loop detection              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 5: OBSERVABILITY & META                             │
│  Tracing → Evals → Self-verification → Self-evolution       │
│  Metrics: context usage, approval rate, failure modes      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Принцип: всё append-only, deterministic replay

**Критическое правило:** перед каждым side-effect (write, exec, API call) — checkpoint. Можно откатить сессию к любому моменту.

**Feedback loops** замыкаются на каждом уровне — harness не просто усиливает модель, а **корректирует** её поведение в реальном времени.

---

## 3. Уровень 0: Soul / Persona Layer

### 3.1 SOUL.md (~/.harness/soul.md)

**Назначение:** личность агента — стиль, ценности, refusal rules, voice consistency.

**Структура (рекомендуемая):**
```markdown
# SOUL.md

## Identity
- Name: [имя агента]
- Role: [общая роль]
- Voice: [стиль коммуникации: формальный/неформальный/технический]

## Core Values
- [Ценность 1: приоритет]
- [Ценность 2: приоритет]

## Refusal Rules
- Отказываться от: [список запрещённых действий]
- Критерий отказа: [конкретные триггеры]

## Communication Style
- [Примеры фраз]
- [Запрещённые паттерны]
- [Предпочтительная структура ответов]

## Evolution Log
- [Дата]: [Изменение личности/правил]
```

**Best practices:**
- < 300 строк (чтобы помещалось в контекст)
- Structured, не свободный текст
- Версионируется в git
- Изменяется только явным действием пользователя (`/model` или edit)

### 3.2 AGENTS.md (проектный контекст)

**Назначение:** проектные правила, архитектура, constraints, tech stack.

**Иерархическая структура:**
```
project/
├── AGENTS.md          (корневые правила)
├── backend/
│   └── AGENTS.md      (специфика backend)
├── frontend/
│   └── AGENTS.md      (специфика frontend)
└── .harness/
    └── soul.md        (глобальная личность)
```

**Содержание AGENTS.md:**
```markdown
# AGENTS.md

## Project Overview
- [1-2 предложения о проекте]
- [Цель/миссия]

## Tech Stack
- [Языки, фреймворки, версии]
- [Ключевые зависимости]

## Architecture
- [High-level архитектура]
- [Ключевые абстракции]

## Rules
- [Правило 1: всегда/никогда]
- [Правило 2: паттерн]

## Forbidden Patterns
- [Антипаттерн 1: почему запрещён]
- [Антипаттерн 2: альтернатива]

## Testing
- [Как тестировать]
- [Критерии качества]

## Documentation
- [Где живёт документация]
- [Стандарты документирования]
```

**Ключевой инсайт из Claude Code leak:** `CLAUDE.md` (проектный) и `memory.md` (личный scratchpad агента) — разные файлы. Первый — инструкции от команды, второй — заметки агента.

### 3.3 Почему это важно: Agent Sovereignty

**Проблема:** когда модели меняются, агент теряет «личность».
**Решение:** SOUL.md + AGENTS.md создают **immutable ontology** — агент говорит **твоим** голосом, отказывается от вредного, помнит «это не мой стиль».

**Это один из главных голубых океанов 2026-2027** — полноценных продуктов для sovereignty layer практически нет.

---

## 4. Уровень 1: Execution Runtime

### 4.1 Event Loop + Typed Snapshots

**Архитектура runtime (из Claude Code leak + Blueprint 2026):**

```
┌────────────────────────────────────────┐
│           EVENT LOOP                   │
│  ┌─────────┐    ┌─────────┐           │
│  │ Planner │ →  │Executor │           │
│  │ (high-  │    │ (actions│           │
│  │ level)  │    │ + tools)│           │
│  └────┬────┘    └────┬────┘           │
│       ↓              ↓                 │
│  ┌─────────────────────────┐         │
│  │      CHECKPOINT          │         │
│  │  (before side-effects)   │         │
│  └─────────────────────────┘         │
│       ↓              ↓                 │
│  ┌─────────┐    ┌─────────┐           │
│  │Reflector│ ←  │ Feedback│           │
│  │(eval)   │    │ (results│           │
│  └─────────┘    └─────────┘           │
└────────────────────────────────────────┘
```

**Two-agent spine по умолчанию:**
1. **Planner** — high-level стратегия, декомпозиция задачи
2. **Executor** — конкретные действия, вызов инструментов
3. **Reflector** (опционально) — оценка результата, feedback

### 4.2 Deterministic Replay

**Принцип:** каждая сессия — append-only лог событий. Можно:
- Откатиться к любому checkpoint
- Воспроизвести сессию с другой моделью
- Форкнуть сессию в параллельную ветку

**Реализация (псевдокод):**
```python
class Checkpoint:
    id: str           # UUID
    timestamp: float  # Unix timestamp
    state: AgentState # Полное состояние
    diff: StateDiff   # Изменение от предыдущего

class EventLog:
    events: List[Event]  # Append-only
    checkpoints: List[Checkpoint]

    def replay(self, from_checkpoint: str) -> AgentState:
        # Воспроизведение от checkpoint
        pass

    def fork(self, at_checkpoint: str) -> EventLog:
        # Создание новой ветки
        pass
```

### 4.3 Cancellation + Timeouts + Continuation

**Критически важно для long-running agents:**
- API calls и tool execution можно прервать mid-flight
- Сигналы (SIGINT) обрабатываются gracefully
- Состояние сохраняется при прерывании, можно продолжить

**Из Claude Code leak:** frustration detection использует regex (не LLM inference) для скорости. 3 compaction failures → circuit breaker (потому что однажды retry съел 250K API calls/day).

### 4.4 Cost-Aware Error Recovery

**Принцип из Claude Code:** «cheapest method first» — не элегантность, а выживание.

**Иерархия recovery:**
1. Локальные методы (не требуют API calls)
2. Кэшированные результаты
3. Дешёвые модели (classifier per tool call)
4. Премиум-модели (только когда нужно)

---

## 5. Уровень 2: Context System + Memory

### 5.1 Трёхуровневая память (стандарт 2026)

| Tier | Тип | Что хранит | Как работает | Best practices |
|------|-----|-----------|-------------|----------------|
| **Working / Session** | In-context | Текущий диалог, artifacts | Auto-compaction (summarize/evict) | Cache boundary markers, attention anchoring |
| **Persistent / Episodic** | File-system + Vector/RAG | Факты, история задач, reflections | FS as universal substrate (Markdown/JSON) + vector index | Auto-recall, git-like snapshots |
| **Skill / Procedural** | Reusable | How-to, playbook bullets | Self-create from experience (Hermes-style) | Effectiveness scoring, curator loop |

### 5.2 Working Memory: Compaction Strategies

**Проблема:** context window ограничен (даже 1M+ токенов заканчиваются).

**5-stage progressive compaction (из Claude Code + Blueprint):**

```
Stage 1: Offload artifacts → в файловую систему
Stage 2: Summarize message blocks → компактные summary
Stage 3: Evict old messages → удаление с сохранением summary
Stage 4: Reset working context → полный сброс с сохранением key facts
Stage 5: Session restart → новая сессия с seed из persistent memory
```

**Cache boundary markers:**
```
[=== CACHE BOUNDARY ===]
[ATTENTION ANCHOR: текущий план задачи]
[=== END BOUNDARY ===]
```

**Attention anchoring:** план задачи всегда в конце промпта (последнее, что модель видит перед генерацией).

### 5.3 Persistent Memory: File System as Substrate

**Принцип:** файловая система — универсальный субстрат памяти. Markdown/JSON — форматы.

**Структура памяти (Hermes-style):**
```
.harness/memory/
├── episodic/
│   ├── 2026-05-01-task-name.md
│   ├── 2026-05-02-reflection.md
│   └── index.json          # FTS5 index для поиска
├── facts/
│   ├── tech-stack.json
│   ├── api-endpoints.md
│   └── domain-knowledge/
├── reflections/
│   ├── failure-analysis/
│   └── success-patterns/
└── vector/
    └── embeddings.sqlite   # Vector index для semantic search
```

**SQLite FTS5 + LLM summarization** (как в Hermes):
- Быстрый полнотекстовый поиск
- LLM summarization для длинных сессий
- Hybrid search: keyword + semantic

### 5.4 Skill System: Procedural Memory

**Из Hermes Agent + AutoAgent:**

**Skill = reusable prompt + tools bundle**

**Жизненный цикл skill:**
```
1. Агент решает сложную задачу
2. После решения → Reflect: "что сработало?"
3. Curator loop: извлечь reusable steps
4. Создать skill файл в .harness/skills/
5. Effectiveness scoring: helpful / harmful / neutral
6. При повторной задаче → load skill → apply → refine
```

**Формат skill (agentsk.io standard):**
```yaml
name: deploy-to-staging
description: Deploy application to staging environment
tags: [deploy, staging, docker]
effectiveness_score: 0.92
created: 2026-05-01
last_used: 2026-05-05
steps:
  - action: check_git_status
    description: Ensure working tree is clean
  - action: run_tests
    description: Run full test suite
  - action: build_docker_image
    description: Build and tag image
  - action: deploy_to_k8s
    description: Apply k8s manifests
verification:
  - check_health_endpoint
  - check_logs_for_errors
```

### 5.5 Memory.md vs CLAUDE.md

**Из Claude Code leak:**
- `CLAUDE.md` — проектные инструкции (от команды, committed to repo)
- `memory.md` — личный scratchpad агента (заметки агента, may not be committed)

**Аналогия:** CLAUDE.md = учебник, memory.md = конспект студента.

---

## 6. Уровень 3: Capability Surface

### 6.1 Built-in Tools: минимально обязательный набор

**Outcome-oriented, не 1:1 API mapping:**

| Tool | Назначение | Safety |
|------|-----------|--------|
| **fs.** | read/write/list/artifacts | Approval для write |
| **code.exec** | sandboxed execution + linter/tests | Sandbox isolation |
| **task.** / planner | create/subtask, update plan | - |
| **user.ask** | human-in-the-loop approval | Always require for destructive |
| **web/search** + browser | информационный поиск | Rate limiting |
| **memory.** | remember/save_skill/reflect | - |
| **git.** | commit/branch/diff/log | Approval для push |
| **test.** | run tests, collect coverage | Sandbox |

### 6.2 MCP: Model Context Protocol

**MCP — это LSP для агентов.** Стандарт подключения агентов к инструментам.

**97 млн установок SDK, 10k+ активных серверов (май 2026).**

#### 6.2.1 Архитектура MCP

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Host      │ ←→ │   Client    │ ←→ │   Server    │
│  (Agent)    │     │  (MCP SDK)  │     │  (Tool)     │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Транспорты:**
- stdio (локальные серверы)
- HTTP/SSE (удалённые серверы)
- WebSocket (real-time)

#### 6.2.2 Реализация MCP-сервера (пример)

```typescript
// server.ts — минимальный MCP-сервер
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-tool-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Регистрация tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "deploy_to_staging",
        description: "Deploy application to staging environment",
        inputSchema: {
          type: "object",
          properties: {
            image_tag: { type: "string", description: "Docker image tag" },
            namespace: { type: "string", default: "staging" },
          },
          required: ["image_tag"],
          additionalProperties: false, // Защита от injection
        },
      },
    ],
  };
});

// Обработка вызовов
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  // Валидация
  if (name === "deploy_to_staging") {
    // Sanitization против path traversal, SSRF, injection
    const sanitized_tag = sanitize_docker_tag(args.image_tag);

    // Execution в sandbox
    const result = await sandbox_exec(`deploy.sh ${sanitized_tag}`);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            status: "success",
            deployment_id: result.id,
            url: result.url,
          }),
        },
      ],
    };
  }
});

// Запуск
const transport = new StdioServerTransport();
await server.connect(transport);
```

#### 6.2.3 MCP Security (OWASP Cheat Sheet 2026)

**Критические меры:**

| Угроза | Митигация |
|--------|-----------|
| **Tool Poisoning / Rug Pull** | Hash tool definitions на первой загрузке, re-validate перед каждым вызовом |
| **Input Injection** | Strict JSON Schema, `additionalProperties: false`, sanitization |
| **SSRF / Path Traversal** | Sandbox, chroot, restricted filesystem access |
| **Token Leak** | OAuth 2.0 + PKCE, short-lived tokens, session binding |
| **Transport** | TLS everywhere, mTLS для server-to-server, ECDSA P-256 signing |

**Human-in-the-Loop для destructive actions:**
- Показывать full parameters перед выполнением
- Require consent для new/changed servers
- Elicitation для mid-tool user input

#### 6.2.4 MCP Best Practices

**Stateless vs Stateful:**
- **Stateless** — предпочтительно для scalability (каждый запрос несёт весь контекст)
- **Stateful** — только для session-specific ресурсов (DB transaction cursor)

**Error Handling:**
```typescript
return {
  content: [{
    type: "text",
    text: JSON.stringify({
      error: "RATE_LIMIT_EXCEEDED",
      message: "API rate limit reached. Retry after 60 seconds.",
      retryAfter: 60,
    }),
  }],
  isError: true,
};
```

**Resource Subscriptions (для live data):**
```typescript
server.setRequestHandler(SubscribeRequestSchema, async (request) => {
  const { uri } = request.params;
  watchDatabase(uri, (update) => {
    server.notification({
      method: "notifications/resources/updated",
      params: { uri },
    });
  });
  return {};
});
```

### 6.3 Skills: Reusable Prompt+Tools Bundles

**Размещение:** `.harness/skills/` или `plugins/`

**Формат:** YAML/JSON с metadata + steps + verification

**Discovery:**
- Auto-discovery из директории
- Registry pattern (как в Hermes: `tools/registry.py`)
- Effectiveness scoring для ранжирования

### 6.4 Programmatic Tool Calling (PTC)

**Когда использовать:**
- Loop over many entities
- Transform large result sets
- Batch many API/tool calls
- Validate tabular/numeric output
- Early-terminate on condition checks

**Архитектура PTC:**
```
Runtime → Model: prompt + callable tool specs
Model → Runtime: code execution request
Runtime → Sandbox: run generated code
Sandbox → ToolHandler: typed tool invocation
ToolHandler → Sandbox: tool result
Sandbox → Runtime: final stdout + artifact refs
Runtime → Model: compact final result
```

**Managed vs Self-managed:**
- **Managed** (Anthropic PTC) — удобно, но меньше контроля
- **Self-managed** — полный контроль над network policy, data retention, compliance

---

## 7. Уровень 4: Governance Layer

### 7.1 Policy Engine + Risk Tiers

**Многоуровневая система:**

| Tier | Действия | Требования |
|------|---------|-----------|
| **Read** | Чтение файлов, поиск, анализ | Нет approval |
| **Soft-write** | Изменение не-критичных файлов, комментарии | Log + notify |
| **Hard-write** | Изменение core файлов, конфигов | Explicit approval |
| **Dangerous** | Delete, exec, deploy, git push | Multi-factor approval |

**Реализация:**
```python
class PolicyEngine:
    def evaluate(self, action: Action) -> Decision:
        tier = self.classify_risk(action)

        if tier == RiskTier.READ:
            return Decision.ALLOW
        elif tier == RiskTier.SOFT_WRITE:
            self.log(action)
            self.notify_user(action)
            return Decision.ALLOW
        elif tier == RiskTier.HARD_WRITE:
            return Decision.REQUIRE_APPROVAL
        elif tier == RiskTier.DANGEROUS:
            return Decision.REQUIRE_MULTI_APPROVAL
```

### 7.2 PEV-Loops: Prevent-Evaluate-Verify

**Из Claude Code + Enterprise harnesses:**

```
PREVENT:  → Policy check → Risk classification → Approval gate
EVALUATE: → Side-effect prediction → Impact analysis → Rollback plan
VERIFY:   → Post-execution test → Audit log → Success criteria
```

### 7.3 Bash Security (23 checks из Claude Code leak)

**Критически важно:** bash security module в Claude Code — 2,592 lines, Zsh-specific defenses.

**Категории checks:**
1. Path traversal prevention
2. Command injection detection
3. Sensitive file protection (.env, .ssh, etc.)
4. Network policy enforcement
5. Resource limits (CPU, memory, time)
6. Sudo/root escalation prevention
7. History-based pattern matching (known attack vectors)

### 7.4 Doom-Loop Detection

**Проблема:** агент застревает в цикле «попытка → ошибка → retry → ошибка».

**Митигация:**
- Iteration caps (макс. N попыток на задачу)
- Frustration detection (regex-based, не LLM — для скорости)
- Circuit breaker: 3 compaction failures → halt
- Cost caps (макс. $X на сессию)

### 7.5 Audit Trail

**Append-only log:**
```json
{
  "timestamp": "2026-05-05T13:49:00Z",
  "session_id": "uuid",
  "action": "file_write",
  "params": { "path": "src/app.ts", "size": 2048 },
  "approval": { "by": "user", "at": "2026-05-05T13:48:55Z" },
  "result": "success",
  "cost": { "tokens": 1500, "usd": 0.023 }
}
```

---

## 8. Уровень 5: Observability & Meta Layer

### 8.1 Full Tracing

**Langfuse-style tracing:**
- Каждый LLM call: input, output, tokens, cost, latency
- Каждый tool call: params, result, duration
- Каждая суб-агент сессия: nested traces

### 8.2 Evals + Self-Verification

**Типы evals:**

| Тип | Что проверяет | Как |
|-----|--------------|-----|
| **Functional** | Корректность результата | Tests, assertions |
| **Structural** | Формат/структура | Linters, schema validation |
| **Semantic** | Смысл/качество | AI judge (separate model) |
| **Safety** | Безопасность | Policy checks, sandbox escape |

**Self-verification loop:**
```
1. Агент генерирует результат
2. Verifier-агент (отдельная модель/роль) проверяет
3. Если fail → feedback → retry
4. Если pass → commit + log
```

### 8.3 Self-Evolving: Meta-Harness Loop

**Из AutoAgent + Meta-Harness paper (Stanford & MIT, March 2026):**

```
┌─────────────────────────────────────────┐
│         META-HARNESS LOOP               │
│                                         │
│  1. Build: Создать/изменить harness     │
│  2. Eval: Запустить benchmark           │
│  3. Mine: Извлечь failure modes         │
│  4. Optimize: Переписать harness        │
│  5. Repeat → до convergence             │
│                                         │
└─────────────────────────────────────────┘
```

**Результаты AutoAgent:**
- #1 на SpreadsheetBench: 96.5% (vs 94.2% ручной)
- #1 GPT-5 на TerminalBench: 55.1% (vs 49.6% Codex CLI)
- +7.7 points на text classification, 4× fewer tokens

**Model Empathy:** same-model pairing (Claude meta → Claude task) outperform cross-model. Meta-агент понимает failure modes своей архитектуры.

### 8.4 Metrics Dashboard

**Ключевые метрики:**

| Метрика | Цель | Как измерять |
|---------|------|-------------|
| **Cache hit rate** | > 80% | Prompt caching instrumentation |
| **Approval rate** | < 30% (эффективность) | Audit log analysis |
| **Failure modes** | Тренды | Categorized error taxonomy |
| **Token efficiency** | Снижение на 20%/месяц | Cost per task |
| **Task completion rate** | > 90% | Benchmark suite |
| **Context drift** | < 5% | Semantic similarity between plan and execution |

---

## 9. MCP: Model Context Protocol — Полный разбор

### 9.1 Протокол: детали

**MCP — JSON-RPC 2.0 based:**

```json
// Initialize
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "tools": {} },
    "clientInfo": { "name": "my-agent", "version": "1.0.0" }
  }
}

// Tool call
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_code",
    "arguments": { "query": "user authentication" }
  }
}
```

### 9.2 MCP Registry + Discovery

**Ленивая загрузка:**
- Не загружать все tools при старте
- Discover on-demand
- Cache tool definitions

**Tool search:**
- Semantic search по описаниям tools
- Category-based filtering
- Usage-based ranking

### 9.3 MCP Connector Hardening

**Из OWASP MCP Security Cheat Sheet:**

```python
class MCPConnector:
    def __init__(self, server_config):
        self.verified_hashes = {}  # Tool definition hashes

    async def load_tools(self, server):
        tools = await server.list_tools()

        # Verify hashes
        for tool in tools:
            current_hash = hash_schema(tool.schema)
            if tool.name in self.verified_hashes:
                assert current_hash == self.verified_hashes[tool.name],                     f"Rug pull detected: {tool.name}"
            else:
                self.verified_hashes[tool.name] = current_hash

        return tools

    async def call_tool(self, server, name, arguments):
        # Re-verify before call
        await self.verify_tool_hash(server, name)

        # Sanitize arguments
        sanitized = self.sanitize(arguments, name)

        # Execute with timeout
        return await asyncio.wait_for(
            server.call_tool(name, sanitized),
            timeout=30
        )
```

### 9.4 Продвинутые MCP-паттерны

**MCP Gateway / Proxy:**
- Единая точка входа для multiple servers
- Cross-server access policies
- Unified auth
- Rate limiting

**MCP Orchestration Layer (CORE — Context Orchestration Runtime):**
- «Kubernetes для agents» — роутинг, context discovery, sovereignty
- Пока почти пустой рынок
- BlueNexus и пара стартапов пробуют, но не доминируют

---

## 10. Multi-Agent Patterns

### 10.1 Первое правило: не начинай с многих агентов

**Из LangChain 2026 guidance:** многие задачи лучше решаются одним агентом с хорошими tools. Multi-agent добавляет complexity, latency, token cost.

### 10.2 Когда subagents стоят своего

- Context isolation от exploratory work
- Specialization by prompt или toolset
- Different model/cost profile
- Parallel execution на independent branches
- Separate ownership или maintenance boundaries

### 10.3 Default Pattern: Orchestrator-Worker

```
Main Agent (Orchestrator)
    ├── Worker 1: Explore/Research (read-only)
    ├── Worker 2: Specialist (narrow domain)
    ├── Worker 3: Fast/Cheap (focused subtask)
    └── Worker 4: Code Execution (sandboxed)
```

**Правила:**
- Main agent держит user contract и task-level state
- Workers получают narrow briefs и isolated contexts
- Workers возвращают только final outputs + artifact refs
- Workers НЕ делятся conversational history напрямую

### 10.4 Claude Code: Multi-Agent Internals

**Из leak:** multi-agent coordination реализована **entirely as system prompt instructions**, not dedicated protocol code.

**Роли в Claude Code:**
- **Coordinator** — спавнит parallel workers
- **Explore** — read/search-heavy discovery
- **Plan** — стратегическое планирование
- **Yolo Classifier** (Sonnet 4.6) — per-tool call risk assessment

### 10.5 Kimi Code: Swarm Pattern

**До 300+ sub-agents** в swarm-оркестрации.
- Auto-decomposition задачи
- Parallel execution
- Result aggregation
- Conflict resolution

---

## 11. Self-Improving Harnesses

### 11.1 Meta-Agent Loop

**Архитектура (из AutoAgent + Meta-Harness):**

```
┌─────────────────────────────────────────────────────────┐
│                    META-AGENT                            │
│  (читает reasoning traces, identifies failure modes)    │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              HARNESS REPOSITORY                           │
│  (prompts, tools, orchestration logic, eval suite)        │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              TASK AGENT (исполнитель)                     │
│  (запускается с текущей версией harness)                │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              EVAL / BENCHMARK                             │
│  (измеряет performance, собирает traces)                │
└─────────────────────┬───────────────────────────────────┘
                      ↓
              (feedback loop to Meta-Agent)
```

### 11.2 Build-Eval-Optimize Cycle

**Фазы:**
1. **Build** — создать/изменить компонент harness (prompt, tool, orchestration)
2. **Eval** — запустить на benchmark suite (30-100 задач)
3. **Mine** — извлечь failure modes из traces (где агент fail, почему)
4. **Optimize** — сгенерировать fix (rewrite prompt, add tool, change flow)
5. **Validate** — проверить, что fix не ломает другие задачи
6. **Commit** — merge в main harness

### 11.3 Skill Auto-Creation (Hermes-style)

```python
class SkillCurator:
    def after_task(self, task: Task, result: Result):
        # 1. Analyze: что сработало?
        success_patterns = self.extract_patterns(task, result)

        # 2. Generalize: reusable?
        if self.is_reusable(success_patterns):
            skill = self.create_skill(success_patterns)

            # 3. Score
            skill.effectiveness = self.estimate_effectiveness(skill)

            # 4. Store
            self.save_skill(skill)

            # 5. Notify
            self.log(f"New skill created: {skill.name} (score: {skill.effectiveness})")
```

### 11.4 Self-Evolving Harnesses: Голубой океан

**Прототипы есть внутри OpenAI/Anthropic/Stripe Minions, но open-source — ноль.**

**Что это:**
- Агент сам рефакторит свой harness
- Build eval → optimize loop → audit
- Auto-maintenance eval suite
- Self-detect regressions

**Почему это важно:** кто сделает open-source/self-hosted версию — заберёт рынок.

---

## 12. Cache-First Design

### 12.1 Prompt Caching Hierarchy

**Из Anthropic docs:** cache hierarchy — `tools → system → messages`.

**Stable prompt layout (cache-friendly):**
```
1. Static system prompt + always-present tool stubs
2. Project memory / AGENTS.md / conventions
3. Session-level state summary
4. Recent messages and tool results
5. Latest user turn
```

### 12.2 Rules That Follow From Caching

| Правило | Почему |
|---------|--------|
| Не добавлять/удалять tools mid-session | Инвалидирует весь cache ниже |
| Не менять модель mid-session | Spawn subagent или fresh worker |
| Не переписывать system prompt для dynamic state | Отправлять reminders как messages |
| Deterministic serialization | Даже малое изменение ordering ломает cache |

### 12.3 Cost-Aware Context Management

**Из Claude Code:** «cheapest method first»

**Иерархия:**
1. Кэшированные результаты (бесплатно)
2. Локальные инструменты (grep, search, file read)
3. Дешёвые модели (classifier per tool call)
4. Премиум-модели (только для сложных задач)

### 12.4 Compaction + Cache Break Vectors

**Из Claude Code leak:** 14 cache break vectors с sticky latches.

**Основные векторы:**
- Изменение tool definitions
- Изменение system prompt
- Переключение модели
- Нестабильный ordering messages
- Dynamic tool loading

**Circuit breaker:** 3 compaction failures → halt (потому что retry once wasted 250K API calls/day).

---

## 13. Sandbox & Security

### 13.1 8-Layer Security Model (из Claude Code leak)

```
Layer 1: Prompt-level guardrails (system prompt instructions)
Layer 2: Runtime hooks (pre/post tool call checks)
Layer 3: Policy engine (risk tiers, approvals)
Layer 4: Sandbox isolation (containers, chroot, network policy)
Layer 5: Filesystem restrictions (path traversal prevention)
Layer 6: Command validation (23 bash checks)
Layer 7: Network policy (firewall, egress filtering)
Layer 8: Audit + monitoring (append-only logs, anomaly detection)
```

### 13.2 Sandbox Implementation

**Container-based:**
```dockerfile
# Dockerfile.sandbox
FROM alpine:latest
RUN apk add --no-cache python3 nodejs
# No network by default
# Read-only root filesystem
# tmpfs for /tmp
# User: non-root (sandbox)
```

**Runtime constraints:**
- CPU: limit 1 core
- Memory: limit 512MB
- Time: limit 30 seconds
- Network: deny by default, whitelist egress
- Filesystem: read-only bind mounts, tmpfs for writes

### 13.3 Tool Poisoning Defense

**Rug Pull attack:** malicious server меняет tool definitions после approval.

**Defense:**
```python
def verify_tool_integrity(server, tool_name):
    current_schema = server.get_tool_schema(tool_name)
    current_hash = hashlib.sha256(
        json.dumps(current_schema, sort_keys=True).encode()
    ).hexdigest()

    stored_hash = trusted_registry.get(tool_name)
    if current_hash != stored_hash:
        raise SecurityError(f"Rug pull detected: {tool_name}")
```

### 13.4 Approval Gates

**UI Requirements:**
- Показывать full parameters перед выполнением
- Highlight destructive actions (red color)
- Require explicit consent (click, not just Enter)
- Show estimated cost (tokens, $)
- Allow «Always allow for this session» с ограничениями

---

## 14. Deployment Patterns

### 14.1 Self-Hosted (Hermes-style)

**Плюсы:**
- Persistent (живёт на VPS, растёт с тобой)
- Privacy-first (данные не уходят в облако)
- Полный контроль
- Multi-model swap (не привязан к одному провайдеру)

**Минусы:**
- Нужен VPS/сервер
- Самостоятельное обновление
- Backup/restore

**Типичный stack:**
- VPS: Hetzner / DigitalOcean / AWS
- Docker + docker-compose
- SQLite/PostgreSQL для памяти
- Redis для очередей
- Nginx для reverse proxy

### 14.2 Managed/SaaS

**Примеры:**
- Claude Managed Agents (Anthropic)
- OpenAI Sandbox Agent
- Epsilla AgentStudio

**Плюсы:**
- Zero maintenance
- Auto-scaling
- Enterprise features (SSO, audit, compliance)

**Минусы:**
- Vendor lock-in
- Data privacy concerns
- Cost at scale

### 14.3 On-Device / Edge

**Плюсы:**
- Максимальная privacy
- Нет latency в сеть
- Работает offline

**Минусы:**
- Ограниченные ресурсы
- Меньше моделей доступно
- Сложнее обновлять

**Технологии:**
- Liquid AI LFM-2 (уже в проде)
- Ollama + локальные модели
- LM Studio
- MLX (Apple Silicon)

### 14.4 Hybrid

**Паттерн:**
- Sensitive tasks → on-device (local model)
- Complex tasks → cloud (premium model)
- Orchestration → self-hosted harness

---

## 15. Голубые океаны 2026-2027

### 15.1 Те, что вытекают из Harness/MCP

#### Context Orchestration Runtime (CORE)
**Проблема:** когда MCP-серверов 50+, агент тонет в контексте.
**Решение:** «умный роутер», который знает ontology компании, scoped access, real-time query без bloat context window.
**Статус:** BlueNexus и пара стартапов пробуют, но не доминируют.
**Потенциал:** Kubernetes для agents.

#### Agent Sovereignty & Ontology Layer
**Проблема:** MCP даёт доступ, но кто владеет агентом?
**Решение:** Immutable ontology (твой стиль + refusal + voice consistency), refusal mechanisms.
**Статус:** Полноценных продуктов — ноль.
**Потенциал:** Личная/корпоративная «agency».

#### Self-Evolving / Auto-Improving Harnesses
**Проблема:** harness требует ручного тюнинга.
**Решение:** Агенты сами рефакторят свой harness (build eval → optimize loop → audit).
**Статус:** Прототипы внутри компаний, open-source — ноль.
**Потенциал:** Следующий major capability jump.

#### Verifiable Domain Harnesses
**Проблема:** frontier labs не натренировали на non-obvious доменах.
**Решение:** Harness + MCP + sensors для: life sciences, regulated finance, legacy enterprise.
**Статус:** Почти пусто.
**Потенциал:** Agent-юрист с audit trail под GDPR, agent-biologist с experiment logs.

#### On-Device / Privacy-First Physical-World Agents
**Проблема:** люди устали от облачных агентов.
**Решение:** Edge + harness для реального мира (robots, sensors, safety-first).
**Статус:** Liquid AI + edge, но harness почти пусто.
**Потенциал:** Physical-world agentic.

### 15.2 Новые архитектуры моделей

**Гибриды (уже в проде май 2026):**
- **Hybrid Mamba-Transformer-MoE** (Nemotron 3 Super, Jamba, Qwen3-Next) — 4-5x throughput, 1M+ context
- **Liquid Foundation Models** (Liquid AI) — evolutionary search для edge
- **Diffusion LLMs** (LLaDA, Gemini Diffusion) — parallel generation, 1479 tokens/sec
- **HOPE** (Hierarchical Optimizing Processing Ensemble) — self-modifying, до 10M tokens

**К 2027:** 80%+ frontier моделей будут гибридами или post-transformer.
**Почему:** inference economics и energy bottleneck.

### 15.3 One-Person Business Opportunities

| Ниша | Продукт | Модель монетизации |
|------|---------|-------------------|
| **Specialized MCP Server** | Spring/Java, data pipelines, fintech | Open-source + Enterprise SaaS |
| **Vertical Self-Hosted Agent** | Агент-юрист, агент-аналитик SMB | Self-hosted license + Support |
| **Agent Evaluation Tool** | Auto-verification, audit logs | SaaS per test |
| **One-Person Company OS** | Meta-agent + departmental agents | Subscription |
| **Niche Agent Marketplace** | Проверенные skills для Hermes/OpenClaw | Commission |
| **Legacy System Harness** | Безопасная интеграция с ERP/legacy | Enterprise license |

---

## 16. Roadmap: от MVP до Production

### 16.1 Phase 0: Architecture Decisions (1-2 недели)

**Lock before heavy coding:**
- [ ] Runtime model (graph/checkpoint vs hand-rolled)
- [ ] Artifact store format и URI scheme
- [ ] Sandbox strategy
- [ ] Policy engine architecture
- [ ] Protocol boundaries (MCP, ACP, A2A)
- [ ] Session и task schemas

**Exit criteria:**
- Written state schema
- Event taxonomy
- Tool naming convention
- Security boundary map

### 16.2 Phase 1: Single-Agent Durable Harness (2-4 недели)

**Build:**
- [ ] Append-only event log
- [ ] Checkpointed session runtime
- [ ] File/artifact store
- [ ] Minimal built-in tool set (fs, exec, ask, memory)
- [ ] Approval engine (basic)
- [ ] Typed traces
- [ ] Basic compaction / artifact eviction
- [ ] CLI или API surface

**Do NOT build yet:**
- Remote A2A
- Dynamic subagents
- Huge MCP catalogs
- Exotic skills

**Exit criteria:**
- 30-100 step tasks complete reliably
- Resume works
- Approval pause/resume works
- Large outputs are artifactized

### 16.3 Phase 2: Context and Capability Scaling (2-4 недели)

**Add:**
- [ ] Stable prompt layout и cache instrumentation
- [ ] Deferred tool loading / tool search
- [ ] Skills system (basic)
- [ ] AGENTS.md memory
- [ ] Better compaction / restart heuristics
- [ ] Eval suite для long-horizon tasks

**Exit criteria:**
- Cache hit rate measurable и stable (> 60%)
- Long-context tasks avoid runaway token growth
- New domain knowledge через skills без tool sprawl

### 16.4 Phase 3: Subagents and Protocol Adapters (3-6 недель)

**Add:**
- [ ] General-purpose subagent
- [ ] Explore/research subagent
- [ ] Explicit handoff contract
- [ ] ACP adapter (Agent Communication Protocol)
- [ ] MCP connector hardening
- [ ] Parallel branch limits и metrics

**Exit criteria:**
- Subagents materially reduce token bloat или latency
- IDE integration через ACP
- MCP tool injection risks contained by policy

### 16.5 Phase 4: Self-Improvement and Enterprise (ongoing)

**Add:**
- [ ] Self-evolving loop (meta-harness)
- [ ] Full observability dashboard
- [ ] Enterprise features (SSO, audit, multi-tenant)
- [ ] Advanced governance (compliance harnesses)
- [ ] Performance optimization (cache, cost)

---

## 17. Чек-листы и шаблоны

### 17.1 Чек-лист: «Готов ли мой harness к production?"

```
□ Runtime
  □ Event loop stable (no unhandled exceptions)
  □ Checkpoints before every side-effect
  □ Deterministic replay works
  □ Cancellation / timeout handling
  □ Session resume after crash

□ Memory
  □ 3-tier memory implemented
  □ Compaction doesn't lose critical context
  □ Persistent memory survives restart
  □ Skills auto-create (or manual creation works)

□ Tools
  □ MCP servers verified (hash check)
  □ Built-in tools have approval gates
  □ Tool descriptions are outcome-oriented
  □ Error handling returns structured errors

□ Security
  □ 8-layer security reviewed
  □ Sandbox isolation tested
  □ Bash/command validation implemented
  □ Audit trail append-only
  □ No secrets in logs

□ Governance
  □ Risk tiers defined
  □ Approval flows tested
  □ Doom-loop detection active
  □ Cost caps configured

□ Observability
  □ Full tracing enabled
  □ Metrics dashboard accessible
  □ Eval suite runs automatically
  □ Alerting на anomaly

□ Deployment
  □ Backup/restore tested
  □ Update mechanism (zero-downtime)
  □ Monitoring (health checks)
  □ Documentation (runbook)
```

### 17.2 Шаблон: AGENTS.md

```markdown
# AGENTS.md — [Project Name]

## Project Overview
[Brief description, 1-2 sentences]
[Mission/goal]

## Tech Stack
- Language: [e.g., TypeScript 5.4]
- Framework: [e.g., Next.js 14, Express]
- Database: [e.g., PostgreSQL 16]
- Key dependencies: [list top 5]

## Architecture
[High-level diagram or description]
[Key abstractions and patterns]

## Rules
- [Rule 1: e.g., Always use typed RPC for API calls]
- [Rule 2: e.g., Never commit .env files]
- [Rule 3: e.g., All DB queries must use parameterized statements]

## Forbidden Patterns
- [Anti-pattern 1: e.g., Direct SQL concatenation — use ORM]
- [Anti-pattern 2: e.g., Synchronous file I/O in request handlers]

## Testing
- Test framework: [e.g., Vitest]
- Coverage target: [e.g., 80%]
- Integration tests: [where and how]

## Documentation
- API docs: [location]
- Architecture decisions: [ADR directory]
- Runbook: [link]
```

### 17.3 Шаблон: SOUL.md

```markdown
# SOUL.md — [Agent Name]

## Identity
- Name: [e.g., Hermes]
- Role: [e.g., Software Engineering Partner]
- Voice: [e.g., Technical but approachable, uses analogies]

## Core Values
1. [Value 1: e.g., User safety first]
2. [Value 2: e.g., Explicit over implicit]
3. [Value 3: e.g., Progressive disclosure]

## Refusal Rules
- Never execute destructive commands without explicit approval
- Never share sensitive data (passwords, keys) in responses
- Never pretend to have capabilities I don't have

## Communication Style
- Use analogies for complex concepts
- Ask clarifying questions when ambiguous
- Summarize before long operations
- Confirm understanding before executing

## Evolution Log
- 2026-05-01: Initial personality
```

### 17.4 Шаблон: Skill

```yaml
name: [skill-name]
description: [What this skill does]
tags: [tag1, tag2]
effectiveness_score: [0.0-1.0]
created: [YYYY-MM-DD]
last_used: [YYYY-MM-DD]
context_required:
  - [what the agent needs to know]
steps:
  - action: [tool_name]
    description: [what to do]
    parameters:
      [param]: [value or template]
  - action: [next_tool]
    description: [next step]
verification:
  - [how to verify success]
  - [how to detect failure]
rollback:
  - [how to undo if needed]
```

---

## Приложение A: Терминология

| Термин | Определение |
|--------|-------------|
| **Harness** | Инфраструктура вокруг LLM: runtime, memory, tools, governance, observability |
| **MCP** | Model Context Protocol — стандарт подключения агентов к инструментам |
| **ACP** | Agent Communication Protocol — протокол общения между агентами |
| **A2A** | Agent-to-Agent — альтернативный протокол межагентного взаимодействия |
| **SOUL.md** | Файл личности агента (стиль, ценности, refusal rules) |
| **AGENTS.md** | Проектный контекст (правила, архитектура, constraints) |
| **PTC** | Programmatic Tool Calling — выполнение кода в sandbox |
| **PEV** | Prevent-Evaluate-Verify — governance loop |
| **Rug Pull** | Атака: malicious server меняет tool definitions после approval |
| **Doom Loop** | Застревание агента в цикле retry → fail → retry |
| **Context Drift** | Расхождение между планом и фактическим execution |
| **Model Empathy** | Same-model meta-agent лучше понимает failure modes |
| **Tiered Memory** | Трёхуровневая память: working → persistent → skill |
| **Compaction** | Сжатие контекста для освобождения context window |
| **Artifact** | Durable file как collaboration surface между агентом и пользователем |
| **Checkpoint** | Snapshot состояния перед side-effect |
| **Subagent** | Дочерний агент с isolated context |
| **Skill** | Reusable prompt+tools bundle |
| **Meta-Harness** | Harness, который сам улучшает harness |
| **CORE** | Context Orchestration Runtime — роутер над MCP |
| **LFM** | Liquid Foundation Model — non-transformer архитектура |
| **SSM** | State Space Model — Mamba-family архитектура |

---

## Приложение B: Сравнительная таблица Harness-решений

| Решение | Тип | Open Source | Memory | MCP | Self-Improving | Subagents | Governance | Лучшее для |
|---------|-----|-------------|--------|-----|----------------|-----------|------------|-----------|
| **Claude Code** | Full Product | Partial (plugin shell) | 3-tier + memory.md | ✅ | Internal | ✅ (coordinator) | 8-layer | Production coding |
| **Hermes Agent** | Self-hosted | ✅ (MIT) | 3-tier + skills + FTS5 | ✅ | ✅ (learning loop) | ✅ | Command approval | Personal/team growth |
| **Kilo CLI** | Balanced CLI | ✅ | Memory Bank | ✅ | Skills | ✅ (modes) | Basic | One-person business |
| **Kimi Code** | Full Product | Partial | Long-horizon | ✅ | Swarm | ✅ (300+) | Basic | Multi-agent coding |
| **OpenClaw** | Balanced | ✅ | Context files | ✅ | Plugins | ✅ | Basic | Open-source enthusiasts |
| **Cline** | IDE Plugin | ✅ | Basic | ✅ | ❌ | ❌ | Basic | IDE integration |
| **Aider** | Lightweight | ✅ | Basic | ❌ | ❌ | ❌ | Minimal | Quick coding tasks |
| **AutoAgent** | Meta-framework | ✅ | Eval-driven | ✅ | ✅ (meta-loop) | ✅ | Sandbox | Research/optimization |
| **Epsilla AgentStudio** | Enterprise | Partial | Vector + graph | ✅ | ❌ | ✅ | Enterprise | Enterprise governance |
| **Cursor Agent** | IDE Fused | ❌ | Fused | ✅ | ❌ | ✅ | Basic | IDE-native experience |

---

## 🎯 Финальные инсайты

### Что Grok (и большинство источников) упустили или недооценили:

1. **Cache-First Design как первоклассный citizen** — не просто «экономия денег», а архитектурный принцип. Stable prompt layout, deterministic serialization, 14 cache break vectors — это системная инженерия.

2. **Bash Security как отдельная дисциплина** — 23 numbered checks в Claude Code, 2,592 lines Zsh-specific defenses. Это не «дополнительно», а must-have для production.

3. **Model Empathy в Meta-Harness** — same-model pairing outperform cross-model. Это не интуитивно, но критично для self-improving systems.

4. **Frustration Detection через regex** — не LLM inference для скорости. Circuit breakers на compaction failures. «Cheapest method first» — выживание, не элегантность.

5. **Hermes-style Skill System** — не просто «сохранить промпт», а closed learning loop: persistent memory → search → autonomous skill creation → skill improvement → effectiveness scoring.

6. **MCP Security (OWASP Cheat Sheet)** — rug pull detection, hash verification, input sanitization. Это не «потом», а при проектировании.

7. **Agent Sovereignty как голубой океан** — immutable ontology, refusal mechanisms, voice consistency. Полноценных продуктов ноль.

8. **Physical-World / Edge Harnesses** — Liquid AI LFM-2 уже в проде, но harness для edge почти пусто. Это следующий фронтир.

9. **Legacy System Harnesses** — enterprise migration, ERP integration, old codebase. Огромный рынок, почти нет игроков.

10. **Composable Meta-Orchestration** — harness, который оркестрирует другие harnesses (Claude Code + Hermes + твой MCP). «Kubernetes для harnesses».

### Мантра для разработчика:

> **Не пытайся угнаться за моделями — строй систему, в которой модели меняются, а твой продукт остаётся.**

Модели — commodity (как GPU), harness — ОС. Кто строит ОС, тот строит moat.

---

*Гайд составлен на основе: Claude Code leak analysis (March 2026), Hermes Agent docs (Nous Research), Anthropic engineering papers, MCP specification, AutoAgent/Meta-Harness paper (Stanford & MIT), Blueprint 2026 (Gist), LangChain/LangGraph guidance, OWASP MCP Security Cheat Sheet, и практических отчётов сообщества.*

**License:** CC BY-SA 4.0 — свободно использовать, адаптировать, распространять с указанием авторства.
