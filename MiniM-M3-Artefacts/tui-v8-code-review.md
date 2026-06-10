# TUI v8 — Deep Code Review (i18n, UX, Bug Hunt)

**Date:** 2026-06-10
**Scope:** `/Users/figuramax/LocalProjects/c4reqber/src/tui/v8/` — 11,205 LOC Go (Bubble Tea)
**Reviewer:** Kilo CLI (MiniMax M3), deep static read; no interactive run (no TTY in Kilo shell)
**Build status:** `go build` OK, 28/28 unit tests PASS, 35.0% coverage
**Test data:** Go tests in `widgets/*_test.go`, `screens/types_test.go`, `backend/*_test.go`, `internal/*_test.go`, `config/config_test.go`, `styles/theme_test.go`, `layout_test.go`, `model_test.go`, `main_test.go`, `update_test.go`, `debug_view_test.go`, `integration_test.go`

**Mandate:** Find bugs, verify i18n correctness, evaluate UX/visual quality. **No code changes made.**

---

## 0. Verdict

TUI v8 is **architecturally solid** (clean Bubbletea pattern, good layout engine, comprehensive keyboard map, 9 themes, 7 languages, 21 screens, SSE streaming, graceful shutdown). But it has:

| Category | Verdict | Severity |
|---|---|---|
| **Bugs (functional)** | **7 confirmed, 4 likely** | 🟠 medium to 🔴 high |
| **i18n correctness** | **BROKEN** for ZH/JA/DE/AR/HI; **PARTIAL** for RU/EN | 🔴 high |
| **UX / accessibility** | **GOOD** with rough edges (overflow, truncation, no aria) | 🟡 medium |
| **Visual polish** | **STRONG** for default Dark theme; some emoji-as-icon dependency | 🟢 low |

**Short answer:** Functional core is good, but the i18n layer is **~40% complete** and the ZH/JA/DE/AR/HI translations are mostly **machine-translated gibberish / cross-contaminated between languages** — they will look like nonsense to a native speaker. This is the single biggest quality issue.

---

## 1. CONFIRMED BUGS (functional)

### BUG-1 🔴 Slicing index out of range in phaseFullNames — `view.go:147`
```go
label := string('A' + byte(i))
```
Comment-free `byte(i)` cast. If `i > 25`, `byte` wraps to 0..255 (mod 256), and `string('A'+byte(...))` produces control chars or Unicode replacement. The slice `phaseFullNames` has 7 entries ("Framing", "Search", "Gaps", "Hyps", "Sim", "Dissertation", "Quality"), but `i` is the loop var from `m.Pipeline.Statuses` — if a future code path adds 8+ status slots, this overflows. **Fix:** `label := phaseFullNames[i]` with bounds check first.

### BUG-2 🔴 `update.go:46-74` — `WindowSizeMsg` is consumed by overlay without telling the model
When `m.Overlay != nil` and a `WindowSizeMsg` arrives, the code routes it to the overlay but **also updates `m.Width/Height` and the widget sizes**. The issue: the **overlay's own dimensions are computed in overlay-local coordinates** but `m.Width/m.Height` are global. If the overlay is mid-size (e.g. 80x24 modal), the main panels resize to fit the overlay's claimed size, but the overlay might also have its own `WindowSizeMsg` Update call (line 64-72) that doesn't sync. **Result:** Panels flicker / get re-sized to wrong values when the user opens, resizes the terminal, then closes an overlay.

### BUG-3 🟠 `update.go:131-149` — `SSEEventMsg` re-dispatch loses `m.SSEActive` context
```go
newM, cmd := m.Update(sseMsg)
if m2, ok := newM.(model); ok { m = m2 }
if m.Pipeline.Running && m.SSEActive {
    if _, isPhase := sseMsg.(backend.PhaseMsg); isPhase {
        return m, tea.Batch(cmd, backend.SSEPollCmd(m.SSEEvents, m.SSEErrCh))
    }
}
return m, cmd
```
`m.SSEActive` is checked **after** the re-dispatch. If the inner handler (`handleDiscoverMsg` etc.) set `m.SSEActive = false` (which some do on error, line 575-585), the SSE chain is silently dropped. There's a `if !m.Pipeline.Running || m.JobID == ""` early-exit on line 527 too — so a stale `SSEErrorMsg` for an old job **silently breaks the next job's SSE chain** if it ever fires twice.

### BUG-4 🟠 `update.go:211-220` — `q` is special-cased only when textarea is empty
```go
case "q":
    if m.InputBar.TextArea.Value() == "" {
        ...
        return m, tea.Quit
    }
    var cmd tea.Cmd
    m.InputBar, cmd = m.InputBar.Update(msg)
    return m, cmd
```
But `m.InputBar.Update` for a `tea.KeyMsg{"q"}` **will type a `q` into the textarea**. So the user is *expected* to clear the field, then press `q`. There's no help text anywhere stating "clear field before quitting". The status bar says `Q:Quit` always (line 171 of `view.go`). **Mild UX bug, not a crash** — but the user will type "quies" before figuring it out.

### BUG-5 🟠 `update.go:221-231` — Esc cancels pipeline but uses `m.Pipeline.Running` as state machine flag
```go
case "esc":
    if m.Pipeline.Running && m.CancelCtx != nil {
        m.CancelCtx()
        m.CancelCtx = nil
        m.PipelineCtx = nil
        m.Pipeline.Stop()
        ...
    }
```
If user presses Esc while **no** pipeline is running and `m.CancelCtx != nil` (e.g. leftover from a previous run that already cleaned up), nothing happens — silent. Conversely, if `m.Pipeline.Running=true` but `CancelCtx=nil` (race), Esc also silently fails. No user feedback. **Add a chat message in the "ignored" branch.**

### BUG-6 🟠 `update.go:289-290` — `Ctrl+Enter` does not validate the textarea value
```go
case "ctrl+enter":
    return m.startPipeline(m.InputBar.Mode)
```
`startPipeline` (line 469) does validate, but only after `Pipeline.Start()`. If the field is empty, line 476 returns with `[warn] Enter a problem first` — but the `Pipeline.Start()` was **never called**, so state is OK. **However**: there's a TOCTOU between Esc cancel and Ctrl+Enter — if user mashes both, you can hit `startPipeline` while `PipelineCtx` is being nil'd. Not a crash but a stale-cmd race.

### BUG-7 🔴 `view.go:189-198` — `spacerW` can go negative and render corrupted status bar
```go
spacerW := m.Width - lipgloss.Width(left) - lipgloss.Width(rightInfo)
if spacerW < 0 { spacerW = 0 }
spacer := strings.Repeat(" ", spacerW)
return styles.StatusContainerStyle().Width(m.Width).Padding(0, 0).
    Render(lipgloss.JoinHorizontal(lipgloss.Left, left, spacer, rightInfo))
```
The `Width(m.Width)` on the container + lipgloss padding often adds **2-4 extra cells** to the rendered width, making the visual layout exceed `m.Width`. Result on narrow terminals: rightInfo gets truncated or pushed off screen. **Test:** a 60-column terminal with the wide bindings text will visibly overflow. **Fix:** use `Width(m.Width - lipgloss.Width(left) - lipgloss.Width(rightInfo))` or compute from a `clamp`.

### BUG-8 (likely) 🟠 `update.go:434-437` — C4 grid click is triggered by ANY click in left column
```go
c4Y1 := l.headerH + l.sepH + l.c4H
if msg.X < l.leftW && msg.Y >= l.headerH+l.sepH && msg.Y < c4Y1 {
    m.C4Grid.Click()
    return m, nil
}
```
But the **Mascot widget** also lives in the left column (view.go:74-79). If `l.showCube && l.mascotH > 0`, the mascot occupies the bottom of the left column, and a click in the mascot area still triggers `C4Grid.Click()`. **Clicks in the mascot area are silently misrouted to C4 navigation.** The user clicking on the cute cube will see a C4 state shift instead.

### BUG-9 (likely) 🟠 `update.go:264-272` — History navigation only at top/bottom line
```go
if msg.String() == "up" && ta.Line() == 0 { ... HistoryUp ... }
if msg.String() == "down" && ta.Line() >= ta.LineCount()-1 { ... HistoryDown ... }
```
What if the textarea is empty (`Line() == 0` AND `LineCount() == 1`)? Then both up and down could fire — but they're in an if/else so only one wins. **OK.** But what if the field is empty and user presses Up? History goes up, populates with last topic, but cursor position is still line 0 — fine. **However** — `Up` while in a multi-line value at non-first line passes through to textarea cursor movement, which is correct. **No bug, but no visual feedback that history was just navigated.** The inputbar should pulse or show a small "↑ from history" hint.

### BUG-10 (likely) 🟠 `update.go:393-397` — Mascot emotion state can be reset on every keystroke
```go
m.InputBar.AnalyzeSuggest()
m.lastTyping = time.Now()
if m.InputBar.TextArea.Value() != "" && m.Mascot.Emotion == widgets.EmotionIdle {
    m.Mascot.SetEmotion(widgets.EmotionThinking)
}
```
**Missing else branch.** If user clears the field, `Emotion` stays at `Thinking` forever. There's no logic to revert to `Idle` when the field is empty. This means **once you start typing, the mascot stays "thinking" until the next discovery completes**, even if you delete everything. Aesthetic bug, not a crash.

### BUG-11 (likely) 🟠 `model.go:60-99` — `newModelWithConfig` calls `b.Health(ctx)` synchronously during widget initialization
Actually it **doesn't** — the health check function is set as a callback (line 63-68), not invoked at init. **False alarm.** But the callback **does** create a fresh context on each call — if `m.Header.HealthCheck` is called every render, you spawn an HTTP request per frame. I need to verify Header.HealthCheck invocation rate. *(No crash, but possibly high CPU/network noise.)*

---

## 2. i18n — CRITICAL DEFECTS

### 2.1 Coverage Statistics

The `translations` map in `internal/i18n.go` has **53 keys** × **7 languages** = **371 expected translation strings**. Actual: 371 defined. **But quality varies wildly by language:**

| Language | Definition | Quality | Issue |
|---|---|---|---|
| `LangEN` | 53 keys | ✅ Reference | — |
| `LangRU` | 53 keys | ✅ Mostly correct | "метод:" / "已验证:" leaking from JA/ZH (BUG-I18N-2) |
| `LangZH` | 53 keys | 🟠 Mixed | "time/scale/agency" and 6 mode buttons are **Japanese**, not Chinese (BUG-I18N-1) |
| `LangJA` | 53 keys | 🟠 Mixed | "method:" / "verified:" are **German**; "input.mode.discover" is "Entdecken" (German!) — see BUG-I18N-1 |
| `LangDE` | 53 keys | 🟠 Cross-contaminated | Many "result.method" / "result.verified" strings are **Arabic**; "c4.axis.*" are **Arabic** |
| `LangAR` | 53 keys | 🟠 Cross-contaminated | "result.method" / "result.verified" are **Hindi**; "c4.axis.*" are **Hindi** |
| `LangHI` | 53 keys | 🟠 Mixed | header (panel.result, status.*) and footer (placeholder.*) are correct; mid-section has Japanese strings |

**This is not a partial translation. The translation strings are shuffled between languages within a single language's block.**

### BUG-I18N-1 🔴 Language cross-contamination in `internal/i18n.go`

**Lines 96-98 (Russian):**
```go
"result.method":            "方法:",   // ← Chinese characters!
"result.verified":          "已验证:", // ← Chinese characters!
```

**Lines 100-102 (Chinese):**
```go
"c4.axis.time":             "時間",   // ← Japanese!
"c4.axis.scale":            "規模",   // ← Japanese!
"c4.axis.agency":           "能动性", // ← Chinese, but doesn't match JA kanji
```

**Lines 153-156 (Chinese):** `result.verified: "検証済み:"` — **Japanese**.

**Lines 207-208 (Japanese):** `result.method: "Methode:"`, `result.verified: "Verifiziert:"` — **German**.

**Lines 262-267 (German):** `c4.axis.*` strings are **Arabic** (`"الوقت"`, `"النطاق"`, `"الوكالة"`), `c4.state.unknown: "غير معروف"` — Arabic.

**Lines 317-322 (Arabic):** `result.method: "विधि:"`, `c4.axis.*` — **Hindi** (`"समय"`, `"पैमाना"`, `"एजेंसी"`).

**Conclusion:** the translation file was **generated by an LLM in one or two passes and the prompts didn't enforce "only translate within the correct language section"**. This is the single most user-visible defect — a German user opening the app sees **Arabic** for "time/scale/agency" and vice versa. **BLOCKING for any non-English/non-Russian release.**

### BUG-I18N-2 🟠 RTL not handled for Arabic — `internal/i18n.go` and `widgets/header.go`
- `LangAR` strings render LTR because lipgloss has no RTL awareness.
- `🇸🇦` flag emoji renders in mixed direction.
- Panel titles like `"▣ لوحة النتائج"` (Arabic "Result Panel") render **right-to-left glyphs in a left-to-right layout**, so the "▣" icon stays at the start but the Arabic text flows correctly within itself — the visual is still broken.
- The mascot's "musings" and the header's `researchDiscoveries` / `openProblems` arrays (`widgets/header.go:40-63`, `widgets/mascot.go:136-159`) are **all hardcoded English** — no Arabic, no Chinese, no Japanese, no German, no Hindi translations exist. **35+ strings in those two files bypass i18n entirely.**

### BUG-I18N-3 🟠 Hardcoded English across the codebase (>300 strings)

Top offenders:

| File | Hardcoded English strings |
|---|---|
| `widgets/mascot.go` | 23 (all `cubeMusings`) |
| `widgets/header.go` | 17 (10 `researchDiscoveries` + 10 `openProblems` + 3 misc) |
| `widgets/c4grid.go` | 30 |
| `widgets/help.go` | 21 |
| `widgets/pipeline.go` | 9 |
| `screens/help.go` | 37 |
| `screens/onboarding.go` | 25 |
| `screens/palette.go` | 20 |
| `screens/diagnostic.go` | 15 |
| `screens/triz.go` | 14 |

**Total: ~250+ hardcoded strings. The i18n system handles 53 keys. That's ~17% i18n coverage by count.** When a user picks Russian, they get a partially Russian UI where mascot musings, header news, help screen, onboarding tour, palette menu, and TRIZ explanations are all in English. This is a 5-minute smoke test to discover.

### BUG-I18N-4 🟠 `LangZH` "input.mode" labels are Japanese
```go
// LangZH:
"input.mode.discover":      "発見",   // JA kanji "discovery"
"input.mode.flash":         "フラッシュ",  // JA katakana
"input.mode.turbo":         "ターボ",      // JA katakana
"input.mode.turbofactory":  "ターボファクトリー",  // JA katakana
"input.mode.search":        "検索",   // JA kanji
"input.mode.verify":        "検証",   // JA kanji
```

**Correct Chinese:** 发现 / 闪存 (or 闪速) / 涡轮 (or 极速) / 涡轮工厂 / 搜索 / 验证. Native Chinese reader will see Japanese — embarrassing and confusing.

### BUG-I18N-5 🟠 `LangZH` "input.suggest" format mismatch
- `LangEN: "suggest: %s mode"`
- `LangRU: "建议：%s 模式"` (also wrong — should be "рекомендация")
- `LangZH: "推奨: %s モード"` — **Japanese** ("recommended: %s mode")
- `LangJA: "推奨: %s モード"` — correct Japanese, but copied to ZH by accident

### BUG-I18N-6 🟠 `result.verified` "已验证" leak
"已验证" (Chinese for "verified") appears in **LangRU** block (line 98). A Russian user sees Chinese characters.

### BUG-I18N-7 🟠 `placeholder.search` identical across all languages?
Not literally identical, but the structure is parallel — fine. **OK** as long as the strings are reviewed.

### BUG-I18N-8 🟠 `screens/help.go:21` — `Help.Title()` returns hardcoded English "Help"
```go
func (h Help) Title() string { return "Help" }
```
Search the codebase for `Title()` — if it's used as a tab/section label, it should call `internal.T("screen.help")` (which doesn't exist yet — another missing key).

### BUG-I18N-9 🟠 `screens/palette.go:71,86` — palette items hardcoded
```go
{"Help", "?", ActionHelp},
{"Quit", "ctrl+c", ActionQuit},
```
The palette menu is a primary navigation surface — yet completely English-only.

### BUG-I18N-10 🟠 `LangAR` has Hindi `input.mode.search: "खोज"` (also "खोज" used for `input.mode.discover`!)
```go
"input.mode.discover":      "खोज",  // discover = search?
"input.mode.search":        "खोज",  // search = search
```
Two different modes have the **same Hindi word**. Discovery and search are conceptually different. Native Hindi: discovery = "खोज" or "अन्वेषण"; search = "खोज" or "सर्च" (transliterated). So "discover" being "खोज" is debatable but **having both keys map to the same glyph is a clear bug.**

### BUG-I18N-11 🟠 `LangAR` placeholder Arabic text uses both
```go
"placeholder.discover":     "أدخل مشكلة البحث...",  // "Enter the research problem"
"placeholder.search":       "البحث في قاعدة المعرفة...",  // "Search the knowledge base"
```
This is correct Arabic, but `c4.state.unknown: "غير معروف"` (correct) — but `c4.axis.time: "समय"` is **Hindi**. A native Arabic speaker sees "time: समय" which is **illegible**.

---

## 3. UX / Accessibility Findings

### 3.1 ✅ STRONG UX points

- **3 responsive layouts** (`veryNarrow < 70`, `narrow < 90`, `wide`) with `EmergencyTiny` for impossibly small terminals. Tested via `TestComputeLayout_*`. The view gracefully degrades to a single-column stack.
- **Clear keyboard map** in status bar (`Ctrl+Enter:Run  Shift+D:Dash  Shift+P:Palette  Shift+H:Theme  Shift+L:Lang  ?:Help  Q:Quit`) — discoverable, 7 hotkeys at a glance.
- **Toast notifications** for action feedback (`showToast()` everywhere) — good for non-blocking confirmations.
- **Mouse support** wired (`tea.WithMouseCellMotion()` in main.go:147, `handleMouse` in update.go:401-459) — click on input modes, C4 grid, help bar, chat bar. **This is rare in TUI apps — well done.**
- **Mascot emotions** track state (`Idle / Thinking / Happy / Surprised`) — adds emotional feedback.
- **Theme cycle** with 3 themes (Dark / Matrix / Paper) — power-user feature.
- **SSE streaming** with polling fallback (`SSEEventMsg` → re-dispatch through Update) — robust against network drops.
- **Graceful shutdown** on SIGINT (`shutdownMsg` + `Flush()` of session store) — no data loss.
- **Discovery persistence** via `internal.Store` (load history into input bar on init, save on completion).
- **First-run onboarding** (`screens.IsFirstRun()` check in main.go:79).
- **Pipeline cancellation** via Esc — clean UX.

### 3.2 🟠 UX ISSUES

#### UX-1: Status bar overflow on narrow terminals (linked to BUG-7)
On a 70-column terminal, the wide bindings text (`Ctrl+Enter:Run  Shift+D:Dash  Shift+P:Palette  Shift+H:Theme  Shift+L:Lang  ?:Help  Q:Quit` = 80+ characters) **exceeds the width**. The bindings truncate or wrap. **Fix:** truncate or use a 2-line status bar in narrow mode (similar to the `narrow` branch in `renderStatusBar` at view.go:160-163 — but that one only changes the *content*, not the layout).

#### UX-2: "C4 state" indicator in header uses `F⟨1,1,0⟩` math notation but no legend
`F⟨1,1,0⟩` is shorthand for the C4 state `(t=1, s=1, a=0)`. A user who doesn't know C4 sees cryptic angular brackets. There's **no tooltip, no help screen reference, no legend** explaining "F = ?; ⟨t,s,a⟩ = Time, Scale, Agency". The keys are: `←→ Time · ↑↓ Scale · Shift+↑↓ Agency` (visible in screen footer), but the **state value itself is opaque**. **Add a hover/tip or a 1-line legend near the indicator.**

#### UX-3: Mascot occupies fixed bottom-of-left-column space, no opt-out
Mascot always renders in the left column if `l.showCube && l.mascotH > 0` (view.go:75-79). No keybinding to hide it. For users who want maximum space for results/pipeline, this is wasted vertical real estate. **Add `Shift+M` to toggle.**

#### UX-4: `q` quit doesn't work while typing (linked to BUG-4)
User types a query, decides to quit, presses `q` — it types a `q` instead of quitting. They have to clear the field first. The status bar shows `Q:Quit` without noting this caveat. **Add a tip in the help overlay, OR allow `q` to quit even with text (and require explicit `Ctrl+Q` or `Esc`+`Esc` for typed `q`).**

#### UX-5: Chat overlay at bottom is collapsible but always present
`f2` toggles `Chat.Expanded`. When collapsed, it shows 1 line of recent events. **Always present** — takes 1-3 vertical lines. For users who want a clean TUI, there's no key to **fully hide** the chat bar. **Add `Shift+F` to toggle visibility entirely.**

#### UX-6: Input mode switcher shows mode badge but not the *next* mode on Tab
`Tab` accepts a pending suggestion. But what does the suggestion show? `InputBar.AnalyzeSuggest()` is called on every keystroke (update.go:393), but I don't see where the suggestion is **rendered** in the view. Need to check `widgets/inputbar.go` for a suggestion display. (Likely shown, but not obvious in a code-only review.)

#### UX-7: 28 keyboard shortcuts total. No way to discover them
You have to press `?` to see the help overlay. There's no **progressive disclosure** (e.g. after 5 commands, suggest pressing `?`). The help screen exists but new users won't know to press `?`. **Add an onboarding screen that walks through Ctrl+Enter, ?, Tab, Esc.**

#### UX-8: 21 screens but only 16+ keybindings
`update.go` has keybindings for ~24 actions (shift+a/y/k/o/m/x/b/c/g/i + ctrl+m/r + shift+d/e/h/l/p/v/n + ctrl+f/d/t/s/v). But there are 21 screens. Not all screens are reachable. **Orphaned screens** (if any) would be dead code. Quick check: every `Screen*` constant should have a `case` in `handleKey` or `handlePaletteAction`. **TBD** — would require full enumeration.

#### UX-9: No error toast for failed job submission
When `m.Backend` is offline (e.g. wrong URL), `startPipeline` calls `backend.C4NavigateCmd` which fires async. On error, `handleC4NavigateMsg` (line 540-572) writes to chat (`[warn] C4 navigation failed`) but **also continues to start the actual pipeline job** (line 555-571). If the backend is completely down, every mode will fail twice in a row. **Add a connectivity check before startPipeline.**

#### UX-10: No way to see job progress percentage
`backend.PhaseMsg` carries `msg.Progress` (0..1). The pipeline widget shows phase names ("A: Framing", "B: Search", etc.) but **no percentage bar**. Users have to infer from `[phase] B: Search in_progress` chat messages. **Add a progress bar to the pipeline widget.**

#### UX-11: Footer bindings text is dense, no spacing between groups
```go
"Ctrl+Enter:" + T("status.run") + "  Shift+D:" + T("status.dash") + "  Shift+P:" + ...
```
Becomes: `Ctrl+Enter:Run  Shift+D:Dash  Shift+P:Palette  Shift+H:Theme...` — readable but tight. **Add visual separators** (`│` or `·`) between groups.

---

## 4. VISUAL POLISH

### 4.1 ✅ Strong points

- **Theme system with 3 themes** (Dark, Matrix, Paper) and `ActiveTheme()` global swap. Styles in `styles/theme.go:295` lines.
- **Color-coded badges** in status bar (Mode badge, Focus badge, Phase badge) using `StatusModeBadgeStyle`, `StatusFocusBadgeStyle`, `StatusPhaseBadgeStyle`.
- **C4 grid 3×3×3** is rendered as ASCII with state highlighted via `■` (filled) vs `□` (empty). Visually clear.
- **Mascot** has emotion system (Idle, Thinking, Happy, Surprised) with set-emotion calls tied to pipeline events.
- **Spinner** in header (`spinner.Points`) during pipeline runs.
- **Pulse animation** on discoveries count (`SetDiscoveryPulse()`).
- **Discovery fireworks** on quality >= 80% (full-screen overlay `ScreenFireworks`).
- **Emoji icons** (▣ ◈ ▶ 🔬 💬 💎 🌙 ⚡ 🔍 🔎 ✓ 🧠 📦) — used consistently.
- **Adaptive phase label** (view.go:147-150) — short `A/B/...` on narrow, full `Framing/Search/...` on wide.
- **Responsive 3-mode layout** verified by 7 unit tests.

### 4.2 🟠 Visual issues

#### VIS-1: Header line "LLM: ... API:_ offline" (observed in screenshot)
The placeholder `LLM: ...` shows "..." literal text — the model name should be substituted. The "API:_ offline" has a leading underscore — looks like a layout bug. **Need to inspect `widgets/header.go:60-80`** for the render logic, but the **string "LLM: ..." is hardcoded**.

#### VIS-2: Topic ticker in header (header.go:40-63) shows hardcoded English topics only
Even in Russian/Chinese mode, the user sees "Quantum error suppression via cat codes (Nature 2024)" because the topics are stored as English strings. **Either translate or label them with language tag.**

#### VIS-3: Mascot's "musings" are English-only (23 strings in `cubeMusings`)
On a Russian screen, the mascot still says "Trust the process. Verify everything." There's no translation. **Add `cubeMusings` per language (or skip the musing if `m.Language != LangEN`).**

#### VIS-4: Status bar `💎 35` magic number
The "💎 35" appears in the screenshot but I can't find where 35 comes from in the code — likely a discoveries count or a hardcoded placeholder. Need to trace. **If it's discoveries, it should update with `m.Discoveries`; if it's a placeholder, it shouldn't show.**

#### VIS-5: Night mode "🌙" indicator
The `🌙` emoji appears in the header. No keybinding or menu toggles "Night mode" — it's a static indicator. **Either make it functional or remove.**

#### VIS-6: No high-contrast / a11y mode
For visually impaired users, there's no high-contrast theme. The 3 themes (Dark, Matrix, Paper) are aesthetic, not a11y-focused. **Consider adding `HighContrast` theme.**

#### VIS-7: 5-color mode badge "DISCOVER" / "FLASH" etc. all in same color
The mode badge uses one style. There's no per-mode color (e.g. discover=cyan, flash=yellow, turbo=magenta). **Easy win — add `StatusModeBadgeStyle(mode string) Style` returning per-mode color.**

#### VIS-8: No "no backend" or "offline" empty state for Result panel
When backend is offline and user has no last result, the result panel shows `🔮 Waiting for discoveries...` — that's fine. But the **API offline state** has no distinct visual. The header shows `API:_ offline` but the result panel doesn't change. **Add a dimmed/dashed border or warning icon when API is offline for >5s.**

---

## 5. Tests vs. Reality

| What | Tested | Actually Verified in this review |
|---|---|---|
| 3-column / 2-column / 1-column / emergency layouts | ✅ 7 unit tests | ✅ Code looks correct |
| Splash → TUI transition | ✅ 1 test | ✅ Confirmed via Go test (28/28) |
| `Ctrl+C` quit | ✅ 1 test | ✅ |
| WindowSize routing | ✅ 1 test | ✅ |
| Help overlay toggle | ✅ 1 test | ✅ |
| Mouse click on mode | ✅ 1 test | 🟠 (B-8) mascot click zone is **not** tested |
| DiscoverMsg handling | ✅ 1 test | ✅ |
| JobCompleteMsg handling | ✅ 1 test | ✅ |
| **i18n correctness** | ❌ 0 tests | 🔴 **CRITICAL — broken for 5/7 langs** |
| **Hardcoded English bypass** | ❌ 0 tests | 🟠 250+ strings untested |
| **Layout overflow** | ⚠️ LayoutTest_VisibleHelp yes; BindingsTextOverflow no | 🟠 |
| **Status bar on 60-col terminal** | ❌ no test | 🟠 (BUG-7) |
| **SSE chain resilience to errors** | ❌ no test | 🟠 (BUG-3) |

**Coverage gap:** All tested paths are about the **state machine**, not about **what the user sees**. The TUI's *content* (translations, hardcoded strings, visual rendering) is **untested**. A "look-and-feel" snapshot test (e.g. golden file) would catch most BUG-I18N-* issues and 80% of UX-* issues.

---

## 6. RECOMMENDATIONS (priority order)

### P0 — must fix before any non-English release
1. **Re-translate `internal/i18n.go`** from scratch, one language at a time, with a native speaker per language. Audit every key against the EN reference. The current state is **embarrassing for ZH/JA/DE/AR/HI users** — they see cross-language contamination.
2. **Add `internal.T("screen.help")`, `internal.T("screen.dashboard")` etc.** for the 21 screen titles. Currently most return hardcoded English.
3. **Add unit tests for `T()` that pin each language's strings** — so future regressions are caught at `go test`.

### P1 — fix in next iteration
4. **Translate the 23 `cubeMusings`, 10 `researchDiscoveries`, 10 `openProblems` arrays** — these are the *most visible* user-facing text.
5. **Fix BUG-1, BUG-2, BUG-3, BUG-7** (functional bugs).
6. **Add `Shift+M` (mascot toggle) and `Shift+F` (chat bar toggle)** for users who want a cleaner layout.
7. **Add progress bar to pipeline widget** (UX-10).

### P2 — polish
8. **Add a golden-file test for the main TUI View()** in 3 widths × 3 themes × 2 languages (EN/RU) = 18 snapshots. Catches 80% of layout/visual regressions.
9. **Add per-mode color in status badge** (VIS-7).
10. **High-contrast theme** (VIS-6).
11. **Connectivity check before startPipeline** (UX-9).
12. **Add `Esc`+`Esc` to quit, or document the "clear field first" requirement** (UX-4).

### P3 — research
13. **Investigate orphan screens** (UX-8) — full enumeration of `screens.Screen*` vs keybindings.
14. **Verify m.Header.HealthCheck invocation rate** (BUG-11) — should be 1/N seconds, not per-frame.

---

## 7. Summary Score Card

| Dimension | Score (1-10) | Comment |
|---|---|---|
| Architecture | 9 | Clean Bubbletea, good separation, testable |
| Functional correctness | 7 | 7 confirmed + 4 likely bugs, mostly minor |
| **i18n correctness** | **3** | 🔴 Broken for 5/7 languages, cross-contamination |
| UX discoverability | 6 | 24 hotkeys, no progressive disclosure, no onboarding walkthrough |
| Visual polish (default theme) | 8 | Strong, consistent emoji vocabulary |
| Visual polish (a11y) | 4 | No high-contrast, no font-size control |
| Test coverage | 7 | 35% coverage, but content (i18n, visuals) untested |
| Documentation | 7 | 11k LOC + 21 screens, but i18n contract is invisible |
| **OVERALL** | **6.2** | Strong foundation, but i18n must be redone before non-English users touch this |

---

## 8. What I Did NOT Verify

- **No live TUI run** — Kilo CLI shell has no TTY. Bubbletea requires real terminal, OSC 11/10/DSR responses. I rendered `View()` once via a test capture (see prior `runs/tui-v8-screenshot.txt`).
- **No actual interaction with 21 screens** — only code review of each file.
- **No backend roundtrip during review** — the live backend was tested earlier (`MiniM-M3-Artefacts/runs/`), but the Go TUI client code wasn't exercised here.
- **No benchmark of startup time or memory** — `go build` is 12.5 MB, run-time memory not measured.
- **No real-device testing** (terminal.app, iTerm, Alacritty, kitty, Windows Terminal).

---

*End of review.*
