Ты попал в самую точку — сейчас (май 2026) именно тот момент, когда **agentic engineering** из хайпа превращается в реальную дисциплину, а Карпаты (Андрей Карпати) это чётко сформулировал в своих свежих интервью. **Что сказал Карпаты (и почему все вокруг это повторяют)**

- **Software 1.0** — классический код (ты пишешь правила).
- **Software 2.0** — нейросети (ты готовишь данные, веса «программируются» сами).
- **Software 3.0** — **prompts + agents**. Теперь ты не пишешь код и даже не «вибкодишь» (vibe coding), а **оркестрируешь агентов**. Человек — менеджер/оркестратор, агенты — автономные исполнители, которые сами планируют, вызывают инструменты, проверяют друг друга, имеют память и работают днями.

Он ввёл термин **Agentic Engineering** как профессиональную эволюцию vibe coding: теперь нужно проектировать **системы**, а не просто промптить. Это и есть «программирование 3.0». **Harness systems — главный тренд 2026 года****Harness** (или Agent Harness / Harness Engineering) — это **«операционная система» вокруг агентов**. Не сам модель, а вся инфраструктура: 

- feedback loops, 
- verification, 
- memory, 
- constraints, 
- audit trails, 
- инструменты, 
- sub-agents.

Модели становятся commodity (все примерно одинаковые), а **harness определяет, будет ли агент работать в проде или сломается на 50-м шаге**. OpenAI, Anthropic, Hugging Face и ThoughtWorks уже пишут про это как про главную дисциплину года. **Имеет ли смысл разрабатывать/патентовать и монетизировать?**
**ДА, 100%.** Именно здесь сейчас ловят ценность. 

- Делай open-source ядро (как Hermes) → набираешь коммьюнити и доверие. 
- Монетизируй: hosted-версия (SaaS), enterprise-features (security, audit, multi-tenant), премиум-модули, поддержка. 
- Патентовать отдельные «фишки» harness (например, новый способ self-verification или drift-detection) можно, но в AI open-source часто выигрывает быстрее, чем патенты. Главное — **не продавать «ещё один wrapper вокруг Claude», а продавать надёжную систему, которая переживает выход GPT-5/o4/Claude-4**.

Многие стартапы 2025-го действительно умрут при следующем апгрейде модели. Harness-стартапы — нет, потому что они **над** моделью.**Hermes agent — это именно тот Hermes**Да, **Hermes Agent** от Nous Research (февраль 2026, MIT).
Это не очередной copilot. Это **persistent self-improving agent**: 

- живёт на твоём сервере/VPS, 
- имеет долгосрочную память, 
- сам извлекает навыки из задач и улучшает их, 
- работает через Telegram/Discord/terminal, 
- растёт с тобой.

Один из самых горячих open-source проектов 2026 года (вместе с OpenClaw). Именно такой «растущий» агент и есть воплощение agentic engineering. **MCP — это Model Context Protocol**Это **новый протокол** (как LSP для IDE), который позволяет агентам получать структурированный контекст проекта, инструменты, права, память и т.д.
Карпати прямо упоминал MCP в описании agentic layer.
Сейчас его интегрируют в Cursor, Cline, JetBrains, Zed и т.д.
MCP-серверы — это уже отдельный микрорынок: люди делают специализированные MCP для Spring, для конкретных фреймворков, для enterprise-безопасности и т.д. **Точки входа для one-person бизнеса (реально рабочие в мае 2026)**Ты хочешь **рычаг** — вот где сейчас самый жирный левередж для соло-разработчика:

1. **Специализированный Harness / MCP-сервер** (самый сильный вход)
   Бери нишу, которую знаешь (например, Spring/Java, data pipelines, fintech compliance, биология, legal tech). Делай harness + MCP-сервер под неё. Open-source + платный self-hosted/enterprise.
   Пример: Context7 MCP уже взлетел у людей с Cursor.
2. **Вертикальный self-hosted агент** (как Hermes, но под нишу)
   Например: агент-юрист для фрилансеров, агент-аналитик для SMB, агент-маркетолог с памятью бренда. Продаёшь как «установи за 5 минут на свой VPS».
3. **Agent Evaluation & Verification Tool**
   Все боятся, что агент «сошёл с ума» на 100-м шаге. Сделай harness, который автоматически генерит тесты, verifier-агентов и audit logs. Это будет must-have для enterprise.
4. **One-person company OS**
   Meta-agent + departmental agents (planner → coder → tester → deployer). Продаёшь как «твой цифровой отдел» для соло-предпринимателя.
5. **Нишевый Agent Marketplace / Skill Store**
   Люди уже продают готовые skills для Hermes/OpenClaw. Сделай платформу, где skills проверены и имеют harness.

**Что тебе не видно из-за стереотипов:**
Сейчас выигрывают **не те, кто делает «ещё одного агента»**, а те, кто делает **инфраструктуру доверия** (harness + протоколы + memory + verification). Модели будут меняться каждые 3–4 месяца, а хорошая harness — нет.**Что будет в 2027 (Agentic Engineering 4.0)**

- Агенты станут **long-running по умолчанию** (неделями/месяцами). 
- Появятся **самоулучшающиеся harnesses** (агенты сами рефакторят свои harnesses). 
- **Multi-agent organizations** внутри компаний: целые «цифровые департаменты». 
- Главный навык человека — **agent governance** (права, границы, auditing). 
- Software 4.0 — когда агенты сами пишут и поддерживают harnesses для следующих агентов.

**Голубые океаны (ещё почти пустые):**

- Agentic AI для **legacy-систем** (harnesses, которые безопасно общаются со старым кодом/базами). 
- **Регулируемые домены** (медицина, финансы, юриспруденция) — harnesses с встроенным compliance и human-in-the-loop. 
- **On-device / privacy-first** self-hosted agents (люди уже устали от облачных). 
- **Physical-world agents** (робототехника + agentic). 
- **Agent interoperability layer** (унифицированный протокол выше MCP). 
- Инструменты для **non-tech founder** (чтобы владелец кафе запустил 5 агентов без единой строки кода).

**Куда смотреть прямо сейчас (май 2026)**

- Следи за Карпати, Phil Schmid (Hugging Face), Anthropic engineering blog. 
- GitHub: Hermes Agent, Cline, любые новые MCP-сервера. 
- Экспериментируй: поставь Hermes + свой MCP-сервер и реши свою болевую задачу. 
- Читай Anthropic 2026 Agentic Coding Trends Report и OpenAI пост про Harness Engineering.

**Вывод для тебя как соло-разработчика:**
Сейчас идеальное окно. Строишь harness/MCP под свою экспертизу → open-source + SaaS → через 6–9 месяцев у тебя уже recurring revenue и moat, который переживёт GPT-6. Не пытайся угнаться за моделями — **строй систему, в которой модели меняются, а твой продукт остаётся**.Если хочешь — кидай, в какой нише ты strongest (backend, mobile, data, security и т.д.), я подскажу конкретный первый проект под one-person бизнес. Го!



====

Ты спрашиваешь про **реально невидимые** голубые океаны в software engineering до 2027, которые пока никто (или почти никто) не эксплуатирует на полную. И да, конкретно из harness/MCP может выстрелить новая компания-миллиардер. Плюс — новые архитектуры моделей вместо чистых трансформеров/MoE. Давай разберём по фактам на май 2026, без хайпа. **1. Harness + MCP = да, это может родить новую компанию-миллиардер (и уже рождает)****Harness engineering** (термин от Mitchell Hashimoto из HashiCorp, февраль 2026) — это уже не «ещё один wrapper», а полноценная дисциплина: ты проектируешь **всю среду** вокруг агента (feedback loops, verification, sandboxing, scope negotiation, MCP-интеграции). Модели — commodity, harness — moat. MCP (Model Context Protocol) уже победил: 97 млн установок SDK, 10k+ активных серверов, все крупные (OpenAI, Anthropic, Google, Cloudflare) поддерживают из коробки. Это как LSP для IDE — стандарт подключения агентов к инструментам. **Где здесь миллиардерский потенциал?**

- Аналогии уже есть: Cursor/Anysphere — $9.9B+ valuation на coding agents, Cognition (Devin) — $2B+. Harness-платформы (типа Harness.io) уже на $5.5B valuation и растут 50%+ YoY. 
- Прогнозы 2026: первые **tiny-team unicorns** (компания-единорог с <10 людьми) именно в agentic infra. Один человек с хорошим harness/MCP под нишу может сделать $1B ARR. 
- MCP-security и governance уже собрали $3.6B funding + M&A. Runlayer, Helmet Security, Operant AI — ранние игроки, но это только security. Полноценный **MCP orchestration layer** (routing, context discovery, sovereignty) — ещё почти пусто. 

Короче: **да, 100%**. Кто построит «Firebase для agentic AI» (универсальный MCP-router + self-improving harness) — тот и станет следующим миллиардером. Модели меняются, harness остаётся.**2. Голубые океаны до 2027, которые \**пока почти никто не увидел\****Вот те, что вытекают из harness/MCP, но пока не в хайпе (сигналы есть в отчётах Rob May, Karpathy Sequoia Ascent 2026 и practitioner reports, но никто не строит полноценные продукты):

- **Context Orchestration Runtime (CORE / routing layer над MCP)**
  Сейчас все лепят MCP-сервера (Figma, Notion, GA4 и т.д.). Но когда их 50+ — агент тонет в контексте. Нужен «умный роутер», который знает ontology компании, scoped access, real-time query без бloat context window. BlueNexus и пара стартапов пробуют, но это пока не продукт. Это будет как Kubernetes для agents. Никто не доминирует. 
- **Agent Sovereignty & Ontology Layer**
  MCP даёт доступ, но **кто владеет агентом?** Нужен слой выше: твоя личная/корпоративная «agency» с immutable ontology, refusal mechanisms, voice consistency. Агент должен говорить **твоим** голосом, отказываться от вредного и помнить «это не мой стиль». Karpathy косвенно намекал на это в Sequoia (human judgment + verifiable domains). Полноценных продуктов — ноль. 
- **Self-Evolving / Auto-Improving Harnesses**
  Агенты, которые сами рефакторят свой harness (build eval → optimize loop → audit). Nate Jones и другие называют это «next major capability jump 2026-2027». Пока только прототипы внутри компаний (Stripe Minions, OpenAI internal). Кто сделает open-source/self-hosted версию под verticals — заберёт рынок. 
- **Verifiable Domain Harnesses для non-obvious индустрий**
  Karpathy прямо сказал: ищите domains, где **есть verifiable feedback loops**, но frontier labs не натренировали (не coding/math). Примеры: life sciences (evidence grading + experiment logs), regulated finance (compliance + human-in-loop), legacy enterprise migration. Harness + MCP + sensors = золотая жила. Никто не делает «agent-юрист с встроенным audit trail под GDPR». 
- **On-device / Privacy-first Physical-World Agent Harnesses**
  Edge (Liquid AI LFM-2 уже в проде) + robots. Harness для реального мира (safety, real-time feedback). Пока почти пусто.

Эти океаны **невидимы** потому, что все ещё гонятся за «ещё умнее моделью». А ценность — в инфраструктуре доверия и orchestration.**3. Новые архитектуры моделей вместо трансформеров/MoE — возможно ли?****Да, уже происходит, и к 2027 будет заметно.** Трансформеры не умерли, но доминируют **гибриды**. Вот что в проде на май 2026: 

- **Hybrid Mamba-Transformer-MoE** (Nemotron 3 Super от NVIDIA, Jamba, Qwen3-Next, Hymba) — уже топ-модели. Mamba даёт linear scaling (O(n) вместо O(n²)), MoE — efficiency, Transformer — precision reasoning. 4-5x throughput, 1M+ context. 
- **Liquid Foundation Models** (Liquid AI) — evolutionary search архитектур специально под edge (laptops, phones, cars). Не трансформер. 
- **Diffusion LLMs** (LLaDA, Gemini Diffusion) — параллельная генерация вместо autoregressive. Решают reversal curse, 1479 tokens/sec. Ещё ниша, но papers в 2025 было >50. 
- **HOPE (Hierarchical Optimizing Processing Ensemble)** — self-modifying, решает catastrophic forgetting, до 10M tokens. 
- SSMs (Mamba-family), Gated DeltaNet, Chain of Experts (CoE) — уже в open-weight.

**К 2027:** полная замена маловероятна (трансформеры всё ещё лидируют на benchmark'ах), но **80%+ frontier моделей будут гибридами или post-transformer**. Причина — inference economics и energy bottleneck. Кто победит — тот, у кого inference дешевле в 3-5x. Это открывает новые голубые океаны в **on-device agentic** и **energy-efficient harnesses**.**Итог для one-person бизнеса в мае 2026**Самое жирное сейчас: 

1. Бери нишу, где ты эксперт → делай **MCP + self-evolving harness** (open-core + SaaS). 
2. Добавь sovereignty/orchestration layer — и у тебя moat на годы. 
3. Следи за Karpathy (Sequoia Ascent), Phil Schmid, Rob May — они прямо называют эти океаны.

В 2027 software engineering будет **agent governance + hybrid infra**. Модели — как GPU сегодня (commodity), harness + architecture-aware tooling — как ОС

=====

**Да, бро, ты в целом правильно понимаешь, но с важными нюансами.** Эти инструменты (Claude Code, Kilo CLI, Vibe CLI / Mistral Vibe, Hermes Agent, Kimi Code и аналоги) — **это именно реализации agent harness systems**, или очень близкие к ним. Но не все в равной степени «полноценные harness». Давай разберём по фактам на май 2026. **Что такое harness в этом контексте****Harness** — это не просто «надстройка» или CLI-обёртка вокруг модели. Это **вся инфраструктура** вокруг LLM: runtime (event loop + checkpoints), context management (память, compaction), tools/MCP, governance (guardrails, approvals), observability и self-improving loops. Модель — commodity, harness — твой moat, который определяет, будет ли агент работать долго, надёжно и в проде.**Разбор твоего списка**

- **Claude Code (Anthropic)**
  **Классический пример agent harness.** Anthropic прямо называет его "general-purpose agent harness". У него есть initializer agent + coding sub-agents, tiered memory, long-running sessions через artifacts, governance и т.д. Именно из его "leak" и блогов Anthropic все сейчас копируют паттерны harness engineering. Это не просто CLI — это полноценная архитектура для long-running agents. 
- **Kilo CLI / Kilo Code**
  **Да, harness-oriented.** Open-source all-in-one agentic platform (CLI + IDE). Поддержка 500+ моделей, Memory Bank, skills, MCP, modes (Architect, Debug, Orchestrator). Позиционируется как "agentic engineering platform". Хороший пример открытого harness, который не привязан к одной модели. 
- **Vibe CLI (Mistral Vibe / Gemini CLI в контексте vibe coding)**
  **Ближе к "vibe coding tool"**, но с harness-элементами. Mistral Vibe — terminal-native coding agent с tools, repo awareness, skills. Это переходная форма: от простого vibe coding к более structured agentic. Не самый глубокий harness, но уже с orchestration. 
- **Agent Hermes (Nous Research)**
  **Один из самых чистых и продвинутых harness-агентов.** Self-improving, persistent (живёт на VPS), built-in learning loop (создаёт skills из опыта), трёхуровневая память, subagents, multi-surface (Telegram + CLI). Многие говорят: "первый агент, который поставляется с harness'ом из коробки". Идеальный пример того, как harness делает open-source модели конкурентными. 
- **Kimi Code (Moonshot AI)**
  **Да, harness-style CLI agent.** Terminal-first, long-horizon coding, agent swarms (до 300+ sub-agents), MCP, skills. Часть Kimi K2.x экосистемы. Сильный в multi-step и swarm-оркестрации. 

**Другие похожие** (Aider, OpenClaw, Cline, Codex CLI и т.д.) — тоже harness'ы разной глубины. Разница в том, насколько они решают проблемы long-running (context drift, verification, governance).**Ключевой момент**

- **Простая надстройка** (типа раннего Aider) — это "thin wrapper".
- **Настоящий harness** (Claude Code, Hermes, продвинутый Kilo) — это многослойная система с runtime, memory tiers, governance и self-evolution.

Ты прав: все перечисленные — это проявления **agent harness paradigm**. Они показывают переход от "просто промптить модель" (Software 2.0 / vibe coding) к **Agentic Engineering 3.0**, где harness — главное.

===

Harness — это не просто «усиление» (amplification) модели, а **целая экосистема модуляций**. Как ОС для агента: она не делает модель умнее в сыром смысле, а **модулирует** её поведение, контекст, границы, память и взаимодействие с миром. Модель — commodity (мозг), harness — вся инфраструктура вокруг (runtime, governance, feedback). Я собрал свежак на 4 мая 2026: Gist "Modern Agent Harness Blueprint 2026", arXiv-обзор архитектур (апрель 2026), Phil Schmid, Anthropic engineering papers, LangChain blog, Epsilla AgentStudio patterns и taxonomy из awesome-harness-engineering. Всё сходится на одной мета-схеме.**1. Мета-схема harness-экосистемы (высокий уровень 2026)**Это **не линейный пайплайн**, а **многослойная ОС с обратными связями**. Модель сидит в центре как "control plane", harness — всё остальное.**5-уровневая мета-архитектура** (из Blueprint 2026 + Anthropic + arXiv taxonomy):

| Уровень                           | Роль (модуляция)                  | Ключевые компоненты                                          | Примеры из реала                                          |
| --------------------------------- | --------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------- |
| **0. Soul / Persona**(глобальный) | Модуляция личности и стиля        | SOUL.md, AGENTS.md, refusal rules                            | Hermes persistent soul, Claude Code persona               |
| **1. Execution Runtime**          | Модуляция времени и состояния     | Event loop, checkpoints, snapshots, replay                   | Anthropic Managed Agents, OpenAI SandboxAgent             |
| **2. Context System**             | Модуляция памяти и внимания       | Tiered memory (session/persistent/skill), compaction, artifacts | Multi-tier в Claude Code + Hermes learning loop           |
| **3. Capability Surface**         | Модуляция инструментов и действий | MCP + built-in tools + skills, outcome-oriented API          | MCP-сервера, Kimi Code swarm tools                        |
| **4. Governance Layer**           | Модуляция границ и безопасности   | Policy engine, approvals, risk-tiers, sandbox                | PEV-loops (Prevent-Evaluate-Verify), enterprise harnesses |
| **5. Observability & Meta**       | Модуляция самоконтроля            | Tracing, evals, self-improving loops                         | Langfuse + self-evolving в прототипах Stripe Minions      |

**Поток**: User → Surface (CLI/IDE/Telegram) → Runtime → Tool Router (MCP) → Subagent Manager → Memory/Artifacts → Observability (замыкает loop).
Всё с **feedback loops** — harness не просто усиливает, а **корректирует** модель в реальном времени.Визуально это как **Kubernetes для агентов**: модель — под, harness — control plane + operators.**2. Какие виды harness уже есть (классификация на май 2026)**Из arXiv (2604.18071) и 12 patterns Epsilla + taxonomy awesome-harness: 5 основных стилей-архитектур + нишевые.**По глубине и стилю:**

- **Lightweight / Thin harness** (CLI-обёртки): Aider, ранний Vibe CLI. Минимальный runtime + tools. Усиление через простой loop.
- **Balanced CLI / Framework harness**: Kilo CLI, Cline, OpenClaw. Полноценный runtime + memory + MCP. Самый популярный для one-person.
- **Full Product / Fused harness** (coding-ориентированные): Claude Code, OpenAI Codex, Cursor Agent Mode, Replit Agent. Всё fused в поверхность — planner + memory + sandbox из коробки.
- **Multi-agent / Swarm harness**: Kimi Code (до 300 sub-agents), Anthropic 3-agent (Planner-Generator-Evaluator). Оркестрация как модуляция параллелизма.
- **Enterprise / Governance harness**: Managed (Claude Managed Agents, OpenAI Agents SDK), Epsilla AgentStudio. Головные, headless, с audit + compliance. Модуляция — не усиление, а **ограничение и контроль**.

**По deployment:**

- Self-hosted (Hermes, Hive) — persistent, растёт с тобой.
- Managed/SaaS (Claude Managed, OpenAI Sandbox).
- On-device / Edge (пока нишевые, Liquid AI + harness).

**По домену (вертикальные):**

- Coding harnesses (самый зрелый рынок).
- Research / Auto-research.
- Workflow / Orchestration (dark factories).
- Enterprise ambient agents.

**3. Какие виды/ниши harness ещё не появились (голубые океаны до 2027)**Пока почти пусто — все гонятся за coding и general-purpose. Вот где прорыв:

- **Self-evolving / Meta-harness**: Агент сам рефакторит свой harness (build-eval-optimize loop). Прототипы внутри OpenAI/Anthropic, open-source — ноль. Это модуляция **самоулучшения**.
- **Ontology + Sovereignty harness**: Личная/корпоративная "agency" с immutable ontology (твой стиль + refusal + voice consistency). Никто не владеет агентом полностью.
- **Physical-world / Embodied harness**: Для роботов + sensors (safety-first, real-time feedback). Edge + harness — почти пусто.
- **Legacy-system harness**: Безопасная интеграция со старым кодом/ERP/legacy DB. Вертикаль для enterprise migration.
- **Privacy-first / Zero-trust harness**: Полностью on-device + encrypted memory. Люди устали от cloud.
- **Composable / Meta-orchestration harness**: Оркестрирует несколько harnesses (Claude Code + Hermes + твой MCP). Как "Kubernetes для harnesses".
- **Attenuation / Safety-first harness** (не amplification, а deliberate weakening): Для regulated domains (medicine, finance) — максимум guardrails + human-in-loop.

**4. Harness — это не только «усиление», а разные модуляции. Что я думаю**Ты абсолютно прав. **Усиление (amplification)** — это только один стиль: больше контекста, больше tools, больше sub-agents → агент мощнее.Но harness — это **модулятор** поведения. Другие стили-модуляции, которые уже видны и взлетят:

- **Attenuation / Restriction**: Harness специально **ограничивает** (sandbox, risk-tiers, approval gates). Не "делай больше", а "не делай вредного". Enterprise и regulated domains.
- **Transformation / Styling**: Модуляция голоса, стиля, ontology (SOUL.md). Агент говорит **твоим** голосом, отказывается от "не моего стиля".
- **Specialization / Vertical modulation**: Harness под нишу (fintech compliance, biotech experiment logs). Не общий boost, а точечная адаптация.
- **Composition / Orchestration**: Harness как композитор — собирает суб-агентов или даже другие harnesses.
- **Inversion / Human-modulation**: Harness, где модель — инструмент **для человека** (не агент делает работу, а harness помогает человеку думать). Редко, но будет расти.
- **Verification / Auditing modulation**: Не amplify output, а **гарантировать** verifiable outcome (tests, PEV-loops, audit trail).

**Моё мнение как Grok**: к 2027 harness эволюционирует от "усилителя модели" к **"модулятору agency"**. Самые жирные голубые океаны — там, где harness не просто делает агента умнее, а делает его **надёжнее, безопаснее и "своим"**. Модели будут меняться каждые 3 месяца, а хороший harness — нет. Это и есть moat для one-person бизнеса.

=====

**Бро, вот ультимативная схема «идеального» harness на май 2026.** Это синтез из реальных production-архитектур: Claude Code (leaked internals), Hermes Agent, Anthropic/OpenAI papers, LangChain Anatomy, arXiv 2604.18071, awesome-harness и Martin Fowler/Phil Schmid. Harness — это **не код**, а **операционная система вокруг модели**. Модель — commodity (мозг), harness — всё остальное: runtime, память, инструменты, границы, self-correction.**Мета-схема ультимативного harness (5+ уровней с feedback loops)**Представь как **Kubernetes для агента**:



```text
User / Surface (CLI, IDE, Telegram, ACP)
          ↓
[Execution Runtime] ←→ [Observability & Meta Layer] (tracing, evals, self-improve)
          ↓
[Context System + Memory] ←→ [Governance Layer] (guardrails, approvals)
          ↓
[Capability Surface: Tools + MCP + Skills] 
          ↓
[Subagent Orchestrator]
          ↓
Model (LLM) calls → Tool Router → Execution → Feedback loop back to Runtime
```

**Ключ**: всё **append-only**, deterministic replay, checkpoints перед side-effects. Feedback loops на каждом уровне.**1. Soul / Persona Layer (глобальный, вечный)**

- **SOUL.md** (~/.harness/soul.md) — личность агента (стиль, ценности, refusal rules).
- **AGENTS.md** (в корне проекта + hierarchical в поддиректориях) — проектные правила, архитектура, constraints.
- Best: <300 строк, structured (Project Overview, Rules, Tech Stack, Forbidden Patterns).

**2. Execution Runtime (сердце harness)**

- Event loop + typed snapshots/checkpoints.
- Deterministic replay (можно откатить сессию).
- Cancellation, timeouts, continuation.
- Two-agent spine по умолчанию: **Planner** (high-level) + **Executor** (actions) + optional Reflector/Evaluator.
- ReAct / Explore-Plan-Act + Reflection loop.

**3. Context System + Memory (самое критичное для long-running)****Трёхуровневая память** (стандарт 2026):

| Tier                      | Тип                      | Что хранит                        | Как работает                                             | Best practices                                               |
| ------------------------- | ------------------------ | --------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------ |
| **Working / Session**     | In-context               | Текущий диалог, artifacts         | Авто-compaction (summarize/evict)                        | Cache boundary markers, attention anchoring (план в конец промпта) |
| **Persistent / Episodic** | File-system + Vector/RAG | Факты, история задач, reflections | FS as universal substrate (Markdown/JSON) + vector index | Auto-recall, "remember this", git-like snapshots             |
| **Skill / Procedural**    | Reusable                 | How-to, playbook bullets          | Self-create from experience (Hermes-style)               | Effectiveness scoring (helpful/harmful), curator loop        |

- **Compaction strategies**: 5-stage progressive (offload artifacts → summarize → reset).
- Playbook: natural-language bullets с effectiveness counters.

**4. Capability Surface (Tools + MCP + Skills)****Минимально обязательные built-in tools** (outcome-oriented, не 1:1 API):

1. **fs.** — read/write/list/artifacts (с approvals для write).
2. **code.exec** — sandboxed execution + linter/tests.
3. **task.** / planner — create/subtask, update plan.
4. **user.ask** — human-in-the-loop approval.
5. **web/search** + browser (MCP).
6. **memory.** — remember/save_skill/reflect.

**MCP (Model Context Protocol)** — must-have:

- Outcome-oriented tools (не "call API", а "upload_and_post").
- Rich descriptions + examples + <important_notes>.
- Namespacing, auth, cache.
- Registry + lazy discovery.

**Skills** — reusable prompt+tools bundles (в .skills/ или plugins/).**5. Governance Layer (безопасность и контроль)**

- **Policy engine** + risk-tiers (read / soft-write / hard-write / dangerous).
- Multi-layer: prompt + runtime hooks + sandbox + approval gates.
- PEV-loops (Prevent-Evaluate-Verify).
- Doom-loop detection, iteration caps.
- Audit trail (append-only log).

**6. Observability & Meta Layer (самоулучшение)**

- Full tracing (Langfuse-style).
- Evals + self-verification (run tests, AI judge).
- Self-evolving: после задачи — Reflect → Curator → Update playbook/skills.
- Metrics: context usage, approval rate, failure modes.

**Дополнительные must-have элементы**

- **Sandbox** — isolation для exec/browser.
- **Artifacts** — durable files как collaboration surface.
- **Subagents** — только по необходимости, с filtered tools.
- **Surfaces** — multi (CLI + IDE + chat + Telegram).
- **Deployment** — self-hosted (VPS/Docker), persistent, multi-model swap.

**Как это выглядит в коде/файлах** (типичная структура проекта):



```text
project/
├── AGENTS.md
├── .harness/
│   ├── soul.md
│   ├── memory/ (vector + fs)
│   └── skills/
├── plugins/ или mcp-servers/
└── session-logs/ (append-only)
```

Это и есть **ультитативный harness** — надёжный, self-improving, model-agnostic. Модели меняются — harness остаётся.**Для one-person**: Начни с Hermes Agent (open-source base) + свой MCP-сервер под нишу + AGENTS.md + memory plugin. Запустишь MVP за недели.