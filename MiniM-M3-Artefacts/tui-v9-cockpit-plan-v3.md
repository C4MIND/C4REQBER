# TUI v9 «THE COCKPIT» — План v3 (6-часовой, executable к утру)

**Дата:** 2026-06-10
**Дедлайн:** 10:00 утра (≈6ч 16м от старта 03:44)
**Автор:** Kilo CLI (MiniMax M3)
**Стиль:** PRD-as-executable-spec. Каждая задача = 1 handoff с acceptance criteria. Без иллюзий.

## 0. Что изменилось от v2

| v2 | v3 |
|---|---|
| 8-недельная дорожная карта | **6-часовая**, привязанная к твоему утру |
| "we'll add Charm/Huh/Harmonica" | **Каждый компонент = install + import + 1 use site + тест** |
| "sub-agents, может быть" | **3 параллельных sub-agent'а** (research / scaffold / test) с явными handoffs |
| "discovery burst animation" | **Конкретный файл, функция, что в ней, что возвращает** |
| "100+ игр в inspiration" | **Один killer game-feel**: matrix rain + burst particles (минимум), всё остальное = P2+ |
| "i18n для 7 языков" | **EN + RU ship-ready, остальные = структура готова, контент пуст** |
| Anti-patterns section | **Сохранена, убрана, как deflate — ничего нового не добавляем** |

## 1. Таймбоксы (hard limits, чтобы не свалиться в rabbit hole)

| Фаза | Название | Длительность | Дедлайн |
|---|---|---|---|
| **0** | Scaﬀold + зависимости | 30 мин | 04:15 |
| **1** | Minimal cockpit (1 feed + 3 cards) | 1.5 ч | 05:45 |
| **2** | Card types + SSE integration + i18n EN+RU | 2 ч | 07:45 |
| **3** | Game-feel effects (matrix rain, burst, cost ticker) | 1 ч | 08:45 |
| **4** | Snapshot tests + report | 45 мин | 09:30 |
| **5** | Buffer / fixes / final commit | 30 мин | 10:00 |

**Если фаза занимает больше — СТОП, документирую, иду дальше.** Не идеально — выполнимо.

## 2. Sub-agent strategy (чтобы параллелить)

В Kilo CLI я **сам — единственный исполнитель**, но я могу:
- Запускать `task` (general sub-agents) для **research** перед написанием кода
- Запускать фоновые `bash` для **тестов и снапшотов**
- Использовать `apify` для **поиска паттернов** (если застряну)

**Три параллельных трека** (в пределах моего токен-лимита):

```
Track A: me → код v9 (последовательно, ~3ч)
Track B: me → snapshot-test (parallel via bash background, ~30м)  
Track C: me → research по конкретным багам (по требованию, ~15м)
```

НЕ пытаюсь запустить 10 sub-agents параллельно — у меня нет изолированного token-контекста, и я их всё равно должен координировать. Только **3 трека** в пределах моей cognitive capacity.

## 3. ФАЗА 0: Scaﬀold (30 мин, до 04:15)

### Acceptance criteria

- [ ] `src/tui/v9/` директория создана
- [ ] `src/tui/v9/go.mod` с правильными зависимостями (charm.land/bubbletea/v2, charm.land/bubbles, charm.land/lipgloss, charm.land/harmonica, github.com/lrstanley/bubblezone)
- [ ] `src/tui/v9/cmd/c4tui-v9/main.go` — минимальный entry point (как v8, но `--tui-version v9`)
- [ ] `src/tui/v9/i18n/en.toml`, `ru.toml` — пустые (заполним в фазе 2)
- [ ] `src/tui/v9/Makefile` с targetами: `build`, `test`, `snapshot`
- [ ] `src/tui/v9/README.md` — 1 страница: что это, как запустить
- [ ] `go build ./cmd/c4tui-v9` — компилируется

### Шаги

1. `mkdir -p src/tui/v9/{cmd/c4tui-v9,internal,widgets,i18n,styles,tests/snapshots}`
2. Скопировать `src/tui/v8/go.mod` → `v9/go.mod`, заменить module path
3. `go mod tidy` для проверки
4. Скопировать `src/tui/v8/cmd/.../main.go` → `v9/cmd/.../main.go`, убрать splash для now
5. `go build` — должен скомпилироваться

### Что НЕ делаем в фазе 0

- Не пишем splash
- Не пишем ничего про C4 cube, mode switcher, palette
- Не трогаем backend (он уже работает)

## 4. ФАЗА 1: Minimal Cockpit (1.5 ч, до 05:45)

### Acceptance criteria

- [ ] Single layout: 4 региона (header / feed / input / footer) — работает на 120×40
- [ ] Feed: пустой с placeholder "Type a discovery question and press Enter"
- [ ] Input: focused, Enter submit (пока echo в feed)
- [ ] Header: "C4REQBER v9" + lang + model badges (захардкоженно пока)
- [ ] Footer: "READY · $0.00" + keymap
- [ ] Esc / Ctrl+C quit работает
- [ ] `go test` PASS, snapshot test для View() — render'ит ожидаемую строку
- [ ] НЕ зависает на splash (сразу TUI)

### Файлы

| Файл | LOC | Назначение |
|---|---|---|
| `v9/main.go` | 100 | Entry, splash = nil, сразу TUI |
| `v9/update.go` | 80 | Один Update method: handle key, return model+cmd |
| `v9/view.go` | 200 | Compose 4-region: header (1) + feed (flex) + input (3) + footer (1) |
| `v9/model.go` | 80 | Single struct: Width, Height, Input (textarea), Feed []Card |
| `v9/layout.go` | 60 | Вычисляет region heights |
| `v9/widgets/feed.go` | 150 | Empty placeholder, добавление cards (append-only), auto-scroll-to-bottom |
| `v9/widgets/header.go` | 60 | Static: "● C4REQBER v9  F⟨1,1,0⟩  🇬🇧 DeepSeek  $0.00" |
| `v9/widgets/footer.go` | 60 | Static: "▶ READY · $0.00 · [Enter] Run  [?] Help  [Ctrl+C] Quit" |
| `v9/widgets/inputbar.go` | 120 | Wraps bubbles/textarea, Enter → SubmitMsg |
| `v9/internal/sanitize.go` | 50 | String sanitizer (reuse from v8) |

**Total P1: ~960 LOC** (много boilerplate, но это нормально для v1.0)

### Imports (минимум)

```go
import (
    "charm.land/bubbletea/v2"
    "charm.land/bubbles/v2/textarea"
    "charm.land/lipgloss/v2"
)
```

### Snapshot test (минимальный, сразу)

```go
// internal/snapshot_test.go
func TestViewEmptyState(t *testing.T) {
    m := newApp()
    m.width, m.height = 120, 40
    out := stripANSI(m.View())
    if !strings.Contains(out, "C4REQBER v9") { t.Fatal("missing header") }
    if !strings.Contains(out, "READY") { t.Fatal("missing footer") }
    if !strings.Contains(out, "Try: design a CRISPR") { t.Fatal("missing placeholder") }
}
```

## 5. ФАЗА 2: Cards + SSE + i18n (2 ч, до 07:45)

### Acceptance criteria

- [ ] 5 card types: Phase, Hypothesis, Paper, Code, Error
- [ ] Submit → POST `/api/v1/discover` → poll job → render Phase cards → render Hypothesis card on done
- [ ] Multi-source: на фазе B — хотя бы 1 paper card from `/v8/knowledge/search`
- [ ] Cost tracking: реальное значение из `estimated_cost` в response
- [ ] i18n: `T("key")` функция читает `en.toml` / `ru.toml`
- [ ] 20 EN строк переведены, 20 RU строк переведены (ты сам проверяешь/корректируешь)
- [ ] `go test` PASS, snapshot test рендерит hypothesis card

### Файлы (добавляются)

| Файл | LOC | Назначение |
|---|---|---|
| `v9/widgets/card_phase.go` | 80 | PhaseCard: title, status, progress bar, ETA |
| `v9/widgets/card_hypothesis.go` | 100 | HypothesisCard: title, confidence, derived_from, actions |
| `v9/widgets/card_paper.go` | 100 | PaperCard: title, authors, citations, DOI, [o][y] actions |
| `v9/widgets/card_code.go` | 80 | CodeOutputCard: engine, steps, ETA |
| `v9/widgets/card_error.go` | 60 | ErrorCard: red, message, retry button |
| `v9/i18n/i18n.go` | 80 | `T(key) string` функция, loads from toml |
| `v9/i18n/en.toml` | 50 | 20-30 строк фраз (header, footer, card labels, keymap, errors) |
| `v9/i18n/ru.toml` | 50 | Russian versions |
| `v9/i18n/i18n_test.go` | 40 | All keys present in both langs, no empty values |
| `v9/internal/api.go` | 150 | HTTP client: Submit, Poll, GetPapers, GetHypothesis |
| `v9/internal/sanitize.go` | 60 | (refactor from widgets) |

**Total P2 additions: ~750 LOC**

### API integration (минимальный)

```go
// internal/api.go
type Client struct {
    baseURL string
    http    *http.Client
    token   string  // from auth
}

func (c *Client) Submit(query string) (jobID string, err error)
func (c *Client) Poll(jobID string) (status JobStatus, err error)
func (c *Client) Papers(query string) ([]Paper, err error)  // /v8/knowledge/search
```

**Auth**: используем тот же JWT flow что в v8 (register + login → JWT). Если у тебя уже есть user в DB, логинимся. Иначе создаём.

### i18n ключи (минимум, 20 шт)

```toml
# en.toml
"app.title" = "C4REQBER v9"
"app.lang" = "EN"
"app.model" = "DeepSeek"
"footer.ready" = "READY"
"footer.running" = "RUNNING"
"footer.done" = "COMPLETE"
"footer.cost" = "$0.00"
"keymap.run" = "Run"
"keymap.help" = "Help"
"keymap.quit" = "Quit"
"keymap.cancel" = "Cancel"
"phase.a" = "Framing"
"phase.b" = "Knowledge acquisition"
"phase.c" = "Gap analysis"
"phase.d" = "Hypothesis generation"
"phase.e" = "Simulation"
"phase.f" = "Dissertation"
"phase.g" = "Quality control"
"card.phase.status" = "in progress"
"card.hypothesis.confidence" = "confidence"
"card.paper.citations" = "citations"
"card.error.retry" = "Retry"
"placeholder.1" = "design a CRISPR guide RNA with minimal off-targets in T-cells"
"empty.feed" = "Type a discovery question and press Enter"
```

**RU версия** — ты (figuramax) переводишь руками 20 строк. **Критично:** ты ЛУЧШЕ любой LLM переведёшь «Hypothesis» → «Гипотеза», «Knowledge acquisition» → «Сбор знаний», «Quality control» → «Контроль качества». Не доверяю LLM-пайплайну для v9.0 — будет каша как в v8.

### Trade-offs (что отрезаем для v9.0)

- ❌ SSE streaming (делаем polling every 2s) — SSE можно в v9.1
- ❌ Multi-agent (только standard discover) — v9.2
- ❌ Discovery`flash`, `turbo`, `turbofactory` — v9.3
- ❌ Многоисточниковый knowledge search через SSE — v9.2
- ❌ Mouse click — v9.2
- ❌ Custom themes (только Dark) — v9.3
- ❌ i18n для 5 других языков (ZH/JA/DE/AR/HI) — отложено, см. `tui-v9-translation-stack-plan.md`

## 6. ФАЗА 3: Game-feel (1 ч, до 08:45)

### Acceptance criteria

- [ ] **Matrix rain** background в feed в idle state (subtle, 30% opacity, scrolls down)
- [ ] **Discovery burst particles** на quality ≥ 0.8 (50 particles, gravity 0.5, 2.5s lifetime)
- [ ] **Cost ticker** — `$0.42` updates real-time на каждый event
- [ ] **Pulsing badge** mode (DARK/DEFAULT) с smooth interpolation через Harmonica
- [ ] **Card spawn animation** — slide-in from right, 200ms ease-out (через Harmonica)
- [ ] Snapshot tests для burst particles

### Файлы

| Файл | LOC | Что |
|---|---|---|
| `v9/widgets/matrix_rain.go` | 80 | Matrix rain background (15-20 col chars falling) |
| `v9/widgets/burst.go` | 100 | Particle system для discovery celebration |
| `v9/widgets/cost_ticker.go` | 60 | Animated `$X.XX` counter |
| `v9/internal/animate.go` | 40 | Harmonica spring wrappers (EasingOutCubic, InOutQuad) |
| `v9/widgets/card_anim.go` | 50 | Card spawn animation (slide from right) |

**Total P3: ~330 LOC**

### Animation timing

- Card spawn: 200ms ease-out
- Mode switch: 150ms spring
- Burst: 2500ms lifetime, 50 particles
- Matrix rain: 16ms tick (~60fps), 0.05x scroll speed (subtle)
- Cost ticker: 100ms refresh (driven by Poll)

### Тест-стратегия

**Snapshot tests в `v9/tests/snapshots/`** — генерим golden output для:
- Empty state (1 файл)
- Phase card rendering (3 файла: running/done/error)
- Hypothesis card (1 файл)
- Paper card (1 файл)
- Discovery burst overlay (1 файл)

Каждый snapshot ~50 строк ANSI-stripped текста. **НЕ пытаемся сделать pixel-perfect** — только проверяем что КЛЮЧЕВЫЕ строки присутствуют.

## 7. ФАЗА 4: Tests + Report (45 мин, до 09:30)

### Acceptance criteria

- [ ] `go test ./...` PASS, coverage >40%
- [ ] Все snapshot tests PASS
- [ ] `make build` создаёт `bin/c4tui-v9`
- [ ] TUI запускается (мы не можем визуально проверить — нет TTY, но `go build` + tests PASS = ОК)
- [ ] `runs/c4tui-v9-smoke-{timestamp}.log` — заглушка лога запуска (smoke check)
- [ ] `REPORT-v9.md` — 2-страничный отчёт что готово

## 8. ФАЗА 5: Buffer (30 мин, до 10:00)

### Что делаем в буфере

- Фиксы бэйджи которые не влезли в предыдущие фазы
- Обновляем docstrings, README
- `git add . && git commit` с подробным message
- Финальный отчёт-протокол

### Что НЕ делаем в буфере

- Не добавляем новых фич
- Не переписываем с нуля
- Не запускаем полный e2e test (нет TTY)

## 9. Handoffs (как sub-agent'ы или bash помогают)

### Track A (main, ~3ч кода)

- Я сам пишу код
- Параллельно: `bash` background для `go build` и `go test` после каждого файла
- Если `go test` падает → fix immediately, не откладываю

### Track B (snapshot, ~30м, parallel)

После Фазы 4 (когда основной код готов), запускаю в фоне:
```bash
go test ./tests/snapshots/ -v -count=1 > /tmp/snapshots.log 2>&1 &
# Анализирую failures, фикшу
```

### Track C (research, по требованию, ~15м)

Если застрял с конкретной проблемой:
```bash
# sub-agent: "найди как сделать X в bubbletea v2"
# или apify: search "bubbletea v2 matrix rain example github"
```

**Не использую sub-agent для кода** — они склонны халтурить, как ты сказал. Я сам пишу каждый файл, проверяю компиляцию, тестирую.

## 10. Acceptance gates (чеклист на 10:00)

```
[v] Phase 0: структура + scaffold + go build ОК
[v] Phase 1: 4-region layout + input + feed empty + quit + tests PASS
[v] Phase 2: 5 card types + backend integration + i18n EN+RU (20 keys each)
[v] Phase 3: matrix rain + burst + cost ticker + pulse
[v] Phase 4: snapshot tests PASS, coverage >40%, build ОК
[v] Phase 5: коммит готов, REPORT-v9.md написан
[v] Bin: bin/c4tui-v9 собирается
[v] Git: commit `v9: minimal cockpit with feed, cards, i18n, game-feel`
[v] Report: runs/v9-{timestamp}/ с примерами render'а
```

## 11. Risk & cuts (если времени не хватит)

**Cut order (что отрезаем в первую очередь):**

1. **Cut P3 (game-feel)** — если Фаза 1+2 займут >4ч, пропускаем matrix rain/burst полностью. v9.0 без animations — это ок.
2. **Cut paper card** — если не успеваем, 4 cards вместо 5 (Phase, Hypothesis, Code, Error)
3. **Cut i18n** — если не успеваем, только EN. RU можно докинуть в v9.1
4. **Cut snapshot tests** — minimum 1 happy-path test вместо 8
5. **Cut report** — 1 страница вместо 2

**Что НЕ cut'аем:**

- Backend integration (Phase 2 core) — без этого v9 бесполезен
- 4-region layout (Phase 1 core) — без этого v9 не v9
- `go build` PASS — иначе ничего не работает
- `go test` PASS хотя бы minimum — иначе мы не знаем работает ли

## 12. Файловая структура (финальная)

```
src/tui/v9/
├── README.md                          # 1 page
├── Makefile                            # build, test, snapshot
├── go.mod
├── go.sum
├── cmd/c4tui-v9/main.go                # 100 LOC
├── update.go                           # 100 LOC
├── view.go                             # 220 LOC
├── model.go                            # 100 LOC
├── layout.go                           # 60 LOC
├── internal/
│   ├── api.go                          # 150 LOC (HTTP client)
│   ├── sanitize.go                     # 60 LOC
│   └── animate.go                      # 50 LOC (Harmonica wrappers)
├── widgets/
│   ├── feed.go                         # 150 LOC
│   ├── header.go                       # 60 LOC
│   ├── footer.go                       # 60 LOC
│   ├── inputbar.go                     # 120 LOC
│   ├── matrix_rain.go                  # 80 LOC (P3)
│   ├── burst.go                        # 100 LOC (P3)
│   ├── cost_ticker.go                  # 60 LOC (P3)
│   ├── card_phase.go                   # 80 LOC
│   ├── card_hypothesis.go              # 100 LOC
│   ├── card_paper.go                   # 100 LOC
│   ├── card_code.go                    # 80 LOC
│   ├── card_error.go                   # 60 LOC
│   └── card_anim.go                    # 50 LOC (P3)
├── i18n/
│   ├── en.toml                         # 50 LOC
│   ├── ru.toml                         # 50 LOC
│   ├── i18n.go                         # 80 LOC
│   └── i18n_test.go                    # 40 LOC
├── styles/
│   └── theme.go                        # 80 LOC
└── tests/
    └── snapshots/
        ├── empty_test.go               # 40 LOC
        ├── phase_card_test.go          # 60 LOC
        └── hypothesis_card_test.go     # 50 LOC
```

**Total estimated:** ~2,300 LOC + 300 LOC tests + 200 LOC docs/configs

## 13. Что v9 НЕ делает (явно режем для 6-часового scope)

- ❌ Splashing animation (instant render, 50ms)
- ❌ 21 экран-оверлеев (palette inline, как `:` mode)
- ❌ SSE streaming (polling every 2s, ок для 6ч)
- ❌ Mouse click zones (только keyboard)
- ❌ Multiple themes (Dark only)
- ❌ Многоисточниковый knowledge (single OpenAlex через /v8/knowledge/search)
- ❌ 7 languages i18n (EN+RU только)
- ❌ Discovery modes (только discover)
- ❌ Verification (Lean4/Coq) UI (mention в output, без UI flow)
- ❌ Auto-export (mention в footer, без real export)

**Эти фичи в v9.1 / v9.2** согласно §10 v2-плана (но мы теперь живём по v3).

## 14. Команды для запуска (после твоего "погнали")

```bash
cd /Users/figuramax/LocalProjects/c4reqber
mkdir -p src/tui/v9/{cmd/c4tui-v9,internal,widgets,i18n,styles,tests/snapshots}
# Затем копирую v8 go.mod, заменяю module path
# ... и дальше по плану
```

## 15. Метрики успеха (definition of done)

| Метрика | Цель | Как измерить |
|---|---|---|
| `go build` PASS | 100% | `go build ./...` exit 0 |
| `go test` PASS | 100% | `go test ./...` exit 0 |
| Test coverage | >40% | `go test -cover` |
| Backend integration | POST → render hypothesis card | Manual test через curl |
| EN+RU i18n | 20 keys × 2 langs | `T("phase.a")` returns "Framing" / "Сбор знаний" |
| Game-feel | matrix rain + burst работают | Snapshot tests + manual check (если возможно) |
| Total LOC | 2,300 ± 20% | `wc -l src/tui/v9/**/*.go` |

## 16. Чего я НЕ буду делать (как ИИ с токен-лимитом)

- ❌ Запускать 10+ sub-agent'ов параллельно
- ❌ Пытаться написать идеальный код с первого раза
- ❌ Спорить с тобой про design choices
- ❌ Переписывать v2 план (только пере-приоритизирую)
- ❌ Ждать твоего одобрения на каждый файл (если укладываюсь в timebox — иду)
- ❌ Добавлять новые фичи не из плана

**Спасибо за то что ценишь моё время. Кодим.**

---

*Если ты читаешь это — план v3 готов. Погнали?*
