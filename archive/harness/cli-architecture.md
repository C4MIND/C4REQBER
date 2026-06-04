**1. Краткий анализ существующих CLI (2026)**Вот как они выглядят по UI/UX (фокус именно на интерфейсе, а не на моделях):

| CLI                        | Тип интерфейса                | Ключевые UI/UX фичи                                          | Сильные стороны визуализации                           | Слабости                     | Библиотека / подход           |
| -------------------------- | ----------------------------- | ------------------------------------------------------------ | ------------------------------------------------------ | ---------------------------- | ----------------------------- |
| **Claude Code**(Anthropic) | Чистый CLI + лёгкий TUI       | Streaming, markdown с цветами, progress/context bars (в кастомных обёртках), arrow-key навигация, Esc-interrupt | Простота, Unix-компонуемость, live token/context %     | Минималистично, мало панелей | Собственный + Rich-подобный   |
| **Kilo CLI** (Kilo Code)   | Полноценный TUI               | Live status bar, omnipresent input, slash-dropdown, @-context, overlays-панели, diff inline, snackbar permissions | Адаптив под размер терминала, unified view агента      | Зависит от IDE/CLI           | Bubble Tea / Charm            |
| **Vibe CLI**(Mistral)      | Современный интерактивный CLI | Autocomplete / и @, themes, persistent history, multi-line input, красивые темы | Красивый рендеринг, configurable UI                    | Базовый layout               | Современные term libs         |
| **Gemini CLI**(Google)     | Polished CLI → GUI-like       | Mouse support, smooth resize, новый rendering engine, интерактивный sub-shell (vim/htop внутри), /help shortcuts | Самый «графический» среди CLI, multimodal (images/PDF) | Иногда шумно                 | Собственный + mouse           |
| **Crush**(Charmbracelet)   | Glamourous TUI                | Bubble Tea + Lipgloss, ASCII-art, playful aesthetic, multi-session, LSP-context, inline diffs | Самый красивый и кросс-платформенный                   | Playful-стиль не всем        | Charm экосистема (Bubble Tea) |
| **Aider** (эталон OSS)     | Классический CLI + git-first  | Auto-commit messages, repomap, git diff visualization        | Git-native UX, transparency изменений                  | Минималистичный              | Python + простые libs         |

**Общий тренд 2026**: Все переходят от «просто текст» к **TUI** (Text User Interface). Основные библиотеки — **Bubble Tea** (Go, Charm) + Lipgloss/Bubbles (стили и компоненты), **Textual** (Python). Они дают Elm-подобную архитектуру (Model-View-Update), mouse, фокус, панели, анимации и адаптив.**2. Мета-структура CLI UI/UX (что вообще существует)**Можно разбить любой CLI на **6 слоёв**. Это и есть твоя мета-архитектура — бери и комбинируй:

1. **Input Layer** (как вводим)
   - Простой prompt → slash-команды с autocomplete + dropdown.
   - @file / @context / @project.
   - Multi-line (Ctrl+J / Shift+Enter).
   - Omnipresent input (всегда доступен, даже когда агент работает).
   - Voice / multimodal (редко, но Gemini уже тянет images).
2. **Output / Visualization Layer** (как показываем)
   - Streaming + markdown (цвета, код, таблицы).
   - Progress bars, spinners, live token/context %.
   - Inline diffs (цветные +/-/~).
   - ASCII/Unicode графики, trees, heatmaps.
   - Themes + Lipgloss-style styling.
3. **Interactive Controls Layer**
   - Keyboard-first (arrows, Esc, Ctrl).
   - Mouse support (Gemini 2025+).
   - Snackbars / modals для permissions (grant/deny/trust).
   - Overlays и contextual panels (управление контекстом, usage).
4. **Layout / Composition Layer** (как организуем пространство)
   - Single pane (классика).
   - Multi-pane TUI (status + chat + preview + tools).
   - Adaptive (меняется под размер терминала).
   - Full alt-screen mode (как vim/htop).
   - Sub-shells (запускай vim внутри своего CLI).
5. **Agent-specific UX Layer** (специфично для AI-агентов)
   - Live status агента (что сейчас делает: read → plan → edit → test).
   - Step-by-step transparency + undo (git-native или checkpoint).
   - Permission gating + trust levels.
   - Session persistence + multi-session switching.
   - Model switching mid-session без потери контекста.
6. **Customization / Extensibility Layer**
   - Config.toml / themes.
   - Плагины (MCP — Model Communication Protocol).
   - Scriptability (pipeable, composable с Unix).
   - Accessibility (high-contrast, screen-reader friendly).

**3. Что можно делать/добавлять в CLI (идеи за пределами текущего)**Вот **мета-уровень возможностей** — от «уже делают» до «никто ещё не делал в 2026». Именно сюда ты можешь запрыгнуть со своей harness-системой.**Уровень 1 (стандарт 2026)**: Всё вышеперечисленное.**Уровень 2 (можно добавить уже сегодня)**:

- **Динамические layout'ы** как в современном TUI: draggable panes (mouse + keyboard), collapsible panels.
- **Procedural visualization**: агент генерит не только код, но и **визуальные дашборды** внутри терминала (ascii-графики производительности, dependency graphs, flowcharts через Unicode).
- **State machine view**: реал-тайм дерево шагов агента (как GitHub Actions, но в терминале).
- **Hybrid input**: CLI + временный мини-GUI (например, harness открывает browser-preview только когда нужно показать UI-дизайн).
- **Memory visualization**: карта контекста с highlight'ом «что забыл агент».

**Уровень 3 (уникальные возможности для harness)**:

- **Harness-driven adaptive UI**: твоя harness-система сама решает, какой layout сейчас оптимален (в зависимости от задачи: deep-refactor → multi-pane; quick-chat → minimal).
- **Meta-commands**: /visualize workflow — агент сам рисует свой план в TUI.
- **Collaborative terminal**: несколько harness-сессий в одном терминале (split-screen для multi-agent).
- **Procedural theming**: тема меняется в зависимости от модели/задачи (Opus — тёмный серьёзный, Flash — яркий игривый).
- **Accessibility-first by design**: layers для voice-over, braille-графики, high-contrast auto-switch.
- **Time-travel UX**: история сессии как timeline, где можно «откатиться» визуально и перезапустить с другого шага.
- **Zero-friction permissions**: вместо snackbar — gesture-based (например, swipe в TUI или hold Esc).
- **Self-describing interface**: /meta показывает текущую архитектуру UI и предлагает улучшения (сам себе рефакторит интерфейс).

**Ограничения, которые нельзя игнорировать**:

- Терминал — это текст + Unicode + ANSI. Никаких настоящих изображений (кроме kitty graphics protocol или sixel, но это нишево).
- Зависимость от терминала пользователя (WezTerm/Alacritty/Kitty — лучшие).
- Производительность: сложный TUI жрёт CPU, если не оптимизировать.

**4. Рекомендации именно для твоей harness-системы**Чтобы сделать **уникальный** интерфейс:

1. **Начни с harness как ядра рендеринга**. Пусть harness — это не просто backend, а **UI engine** для терминала. Она динамически генерит layouts и компоненты под задачу.
2. **Выбери парадигму, которой нет ни у кого**:
   - «Flow-first» (всё как pipeline + visual nodes в TUI).
   - «Context-first» (главное — карта контекста, а чат вторичен).
   - «Harness-mode» — интерфейс, который сам себя адаптирует и объясняет, почему выбрал именно этот layout.
3. **Стек для реализации** (если на Go — Bubble Tea + Lipgloss; Python — Textual 2+). Или сделай свой минимальный layer поверх harness.
4. **Тестируй на трёх сценариях**:
   - Быстрый чат.
   - Глубокий рефакторинг большого проекта.
   - Multi-agent workflow.
5. **Правило уникальности**: если фича уже есть в Claude/Kilo/Crush/Gemini — спрашивай себя «как я могу сделать это в 10 раз удобнее или по-другому?».

**Бро, этот доклад — твой структурный blueprint.** Теперь у тебя есть полная карта: что делают все + что можно изобрести. Бери любой слой, миксуй с возможностями harness — и получишь интерфейс, которого реально ни у кого нет.