## **Мега-таблица агентских .md-файлов (по состоянию на май 2026)**

Вот **умная сравнительная таблица** всех основных файлов, которые используют в Claude Code, OpenClaw, Cursor, Codex и других agent harnesses. Я собрал актуальные практики из Karpathy-style workflow, OpenClaw (Peter Steinberger), Anthropic Skills, LangChain и сообщества.

| Файл            | Полное название / Альтернативы       | Основная цель                                                | Что именно писать (структура)                                | Уровень (Project / Personal / Skill)     | Как часто читается агентом                | Примеры использования                                        | Ключевые советы (best practices)                             |
| --------------- | ------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ---------------------------------------- | ----------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **SOUL.md**     | Soul.md, Soul and D document         | **Личность, идентичность, ценности, голос** (Who I am)       | - Core values & ethics - Tone & voice - Hard limits (banned words, never do X) - Personality traits - "Why I exist" | Personal / Per-agent (в workspace)       | Каждый session (инжектится первым)        | Dobby (домашний claw Карпати), личный AI-ассистент           | Держи **коротким** (≤400-500 токенов). Не суй сюда SOP! Только "кто ты". Используй для эмоциональной coherence. |
| **AGENTS.md**   | Agents.md, CLAUDE.md (в Claude)      | **Операционные правила, как работать** (How I operate)       | - Boot sequence - Memory protocol - Task handling rules - Escalation (когда спрашивать человека) - Checklists & workflows | Project / Workspace                      | Каждый session + при релевантных задачах  | Общие инструкции по проекту, coding standards, review process | Самый "универсальный" файл. Перемещай сюда всё procedural из SOUL.md. Коротко и модульно. |
| **SKILL.md**    | Skill.md (в папке skill-name/)       | **Конкретная reusable способность / workflow**               | - Name + Description (обязательно) - Instructions - Examples - When to use - Optional: scripts, references, assets | Reusable / Portable (skills/ директория) | Динамически (агент сам решает или /skill) | Code review, deployment, testing, documentation gen, prompt engineering | **Открытый стандарт**(agentskills.io). Одна skill — одна папка. Делай portable. Можно публиковать в marketplace. |
| **Program.md**  | Program.md (Karpathy)                | **Описание research/org loop** (Meta-инструкции для Auto Research) | - Objective + Metrics - Experiment plan - Roles & collaboration - Boundaries & stopping criteria - Meta-optimization rules | Research / Claw level                    | В начале Auto Research loop               | Auto Research harness, recursive self-improvement, multi-agent org | "Код" твоей research organization. Можно иметь несколько и оптимизировать их. |
| **MEMORY.md**   | Memory.md, memory/YYYY-MM-DD.md      | **Долгосрочная + short-term память**                         | - Curated facts & learnings - User preferences - Project history - "Dream" summaries | Per-workspace / Per-agent                | При старте + обновляется                  | Что агент узнал о тебе/проекте                               | Curate вручную или через "dream" процессы. Не сваливай всё — только valuable. |
| **USER.md**     | User.md                              | **Модель пользователя**(Who am I helping)                    | - Твои предпочтения - Style & communication - Goals & priorities - Constraints | Personal                                 | Каждый session                            | Как агент должен взаимодействовать именно с тобой            | Отдельный от SOUL.md — агент "знает тебя".                   |
| **IDENTITY.md** | Identity.md                          | **Self-image агента**(metadata)                              | - Name, role, capabilities - Display info - Dependencies     | Per-agent                                | При инициализации                         | Для multi-agent setups                                       | Техническая идентичность.                                    |
| **CLAUDE.md**   | Project-specific rules (Claude Code) | Аналог AGENTS.md для Claude                                  | Coding standards, architecture rules, do's & don'ts          | Project root                             | Каждый session                            | Karpathy-inspired skills (forrestchang repo)                 | Часто symlink на AGENTS.md для кросс-tool совместимости.     |
| **TOOLS.md**    | Tools.md                             | **Доступные инструменты & permissions**                      | Список tools, когда использовать, security rules             | Workspace                                | При boot                                  | API keys, sandbox rules                                      | Безопасность и scoping.                                      |

**Ключевые принципы работы с этими файлами (2026)**

1. **Иерархия загрузки** (обычно):
   - SOUL.md → AGENTS.md → MEMORY → SKILL.md (по необходимости) → Project files.
2. **Token economy**:
   - SOUL + AGENTS — держи lean (агент читает их всегда).
   - Skills — lazy loading (экономия контекста).
3. **Лучшие комбинации**:
   - **Личный Claw** → SOUL.md (личность) + AGENTS.md (правила) + MEMORY.md.
   - **Research Claw** → Program.md + Auto Research loop.
   - **Multi-agent** → Отдельный workspace на роль + routing.
4. **Cross-tool совместимость**:
   - AGENTS.md / SKILL.md — самые portable.
   - CLAUDE.md часто symlink'ят на AGENTS.md.
   - OpenClaw — самый богатый набор (Soul + Agents + Memory).
5. **Эволюция**:
   - Агент сам может обновлять некоторые файлы (с твоего одобрения).
   - Делай versioning (git) на эти .md — они и есть "мозг" системы.

**Мой совет как researcher/harness-builder**:
Начни с **SOUL.md** (личность) + **AGENTS.md** (операции) + 2–3 **SKILL.md** под твои домены (например, "Hyperparam Tuning", "Code Review", "Experiment Design"). Потом поднимайся до **Program.md** для полноценного Auto Research.