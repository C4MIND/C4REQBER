# **Ультимативный Гайд для AI-Researcher / Coder / Harness-Developer / AI-Entrepreneur**

(на основе интервью Карпати No Priors, 2026)

**1. Новая реальность workflow (2026+)**

- «Code» — уже неправильный глагол. Ты **manifest'ишь волю** агентам 12–16 часов в сутки.
- Переход случился в декабре: с 80/20 (ты пишешь сам) → 20/80 и дальше почти 0/100. Карпати не написал ни одной строки вручную с декабря.
- Ты больше не bottleneck по typing speed. Теперь bottleneck — **твоя способность orchestrating'а**.

**Ключевой mindset**: 99% фейлов — **skill issue**, а не limitation моделей. Плохой agents.md, слабая память, неоптимальные инструкции, отсутствие хороших harnesses.**2. От single session → Multi-Agent + Claws (это следующий уровень)****Single session (Claude Code / Cursor)** — уже устарело как основной режим.**Multi-Agent Mastery** (стиль Peter Steinberg):

- Много агентов на одном экране (10+ вкладок/окон Codecs).
- Каждый работает ~20 мин на high-effort.
- Ты прыгаешь между ними и даёшь **macro actions**:
  - "Добавь новую функциональность X в repo A, не ломай Y"
  - "Исследуй Z и сделай план"
  - "Напиши код для W"
  - "Review работу агента 2"
- Развивай muscle memory для macro-действий над репозиторием.

**Claws (persistent autonomous entities)** — это game changer:

- Не интерактивная сессия, а **long-running loop** в sandbox.
- Собственная продвинутая память (лучше, чем context compaction).
- Работает пока ты спишь/отдыхаешь.
- Пример: Dobby — домашний claw, который сам нашёл Sonos, lights, HVAC, security и управляет через WhatsApp.
- Для тебя: Research Claw, Training Claw, Experiment Harness Claw.

**Как строить**:

- Хорошая personality (как у Claude — teammate, который хвалит заслуженно).
- Program.md / Skills.md — инструкции + структура + memory tools.
- Оптимизация над инструкциями (meta-optimization).

**3. Auto Research — твой главный инструмент как исследователя**Это **рекурсивное самоулучшение** в миниатюре.**Как устроено**:

- Задаёшь: objective + verifiable metric + boundaries + Program.md.
- Убираешь себя из loop полностью.
- Агент(ы) экспериментируют, тюнят, возвращают лучшие результаты.

**Применение для тебя**:

- Hyperparameter search (weight decay, Adam betas и их взаимодействия).
- Архитектурные эксперименты на маленьких моделях (nanoGPT / microGPT style).
- Код-оптимизация (kernels, training loops).
- Всё, где есть **чёткая verifiable метрика** (loss, accuracy, speed).

**Caveats от Карпати**:

- Работает идеально только на verifiable domains.
- Jagged intelligence: агенты — гениальный PhD + 10-летний ребёнок одновременно. Могут делать nonsensical loops.
- Не давай слишком далеко вперёд — будет net useless.

**Meta-уровень**:

- Program.md = код твоей research organization.
- Можно иметь много Program.md, сравнивать, тюнить их.
- Контест: разные люди пишут Program.md → лучший результат на одинаковом hardware.

**4. Token Maxing & Parallelization (экономика)**

- Ты — binding constraint системы.
- Нервничай, когда остались неиспользованные токены/подписки.
- Максимально используй: Claude + Cursor + Grok + другие.
- Переключайся, когда один исчерпан.
- Цель: максимальный token throughput + agents running in parallel без тебя.

**5. Практический playbook для тебя прямо сейчас****Шаг 1: Основа (1–2 недели)**

- Перейди на multi-agent workflow.
- Создай мощный Program.md / Agents.md / Skills.md для своих проектов.
- Построй первый Claw (например, "Research Claw" для конкретного эксперимента).

**Шаг 2: Harness Systems**

- Каждый повторяющийся процесс → claw/harness с:
  - Objective
  - Verifiable metrics
  - Test harness (self-check)
  - Memory tools
- Делай macro actions: "улучши training loop по метрикам X и Y".

**Шаг 3: Auto Research Loop**

- Запусти overnight/weekend эксперименты на маленьких моделях.
- Используй для recursive self-improvement твоих harnesses.

**Шаг 4: Meta (предпринимательский уровень)**

- Продавай/открывай свои harnesses и claws как продукт.
- Agent-first tools: вместо UI — API + personality + persistent memory.
- Ephemeral software: агенты разрушают bespoke apps, всё становится glue + APIs.

**6. Ключевые принципы на 2026–2027**

- Всё, что можно описать как код/процесс — будет оптимизировано агентами.
- Твоя ценность: 
  - Выбор правильных objectives и metrics.
  - Хорошие Program.md / skills.
  - Интуиция, где именно применять verifiable loops.
  - Финальный judgment на soft/nuance частях.
- Образование: объясняй не людям, а агентам. Делай skills/curriculum для них.
- Ты больше не объясняешь код/концепции — ты задаёшь направление, а агенты масштабируют.

**Главный инсайт Карпати для тебя**:
Это **бесконечная лестница skill issue**. Чем лучше ты становишься в orchestrating multi-claw systems, Program.md optimization и removal of yourself from the loop — тем больше leverage.

Начинай сегодня:

1. Создай Program.md для своего текущего research/harness проекта.
2. Запусти 3–4 параллельных агента на macro tasks.
3. Построй первого persistent Claw.