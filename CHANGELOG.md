# Changelog — TUI v9 + Backend Pipeline

## v9.13.x (2026-06-22) — feat/production-upgrade

Production-upgrade audit pass: 14 atomic commits (2 rounds).

### Round 2 — deep audit (staticcheck + manual + regression tests)

- **CRITICAL: regular typing now works.** Round 1 removed
  `m.ta.Update(msg)` from the start of the KeyPressMsg case
  but left an earlier 'v9.13.x fix' explicit `return m, nil`
  that blocked the fallthrough's textarea update — so typing
  letters did NOTHING. Caught by the new
  `TestStateMachine_KeyPress_NoDoubleTextareaUpdate` regression
  test on the very first run. Fix: removed the explicit return
  so unmatched letter keys fall through to the bottom of
  Update() and the textarea gets the keystroke exactly once.

- **persist.Save race fix.** `Store.Save()` was releasing the
  mutex before `os.Rename` — two concurrent Saves could stomp
  on each other's `s.path+".tmp"` file. Lock now held across
  the whole marshal+write+rename.

- **Test isolation (TestMain).** 33+ tests in the main package
  were reading (and sometimes writing) the developer's real
  `~/.c4reqber` because they called `NewApp("http://test")`
  without setting HOME. New `main_test.go` defaults HOME to
  a fresh tempdir at package init; per-test `t.Setenv("HOME",
  tmp)` still works for tests that need real persistence
  (resume_test, feed_persist_test).

- **Dead code cleanup (staticcheck U1000).** Removed
  `sseStreamWithReconnect` + `SSEStreamResult` (the actual
  SSE path uses `sseContinueCmd`), `papersCmd`/`multiCmd`
  unused API wrappers, `apiHypothesisMsg` type, `clampFocus`
  method, `fmtDiscoveryMeta` helper, `starsPattern` field,
  `smallCrystalLines` + `splashFadeOutMs` vars, `ansiRe` test
  var, the entire `lang_helper_test.go` test file. Also
  removed 3 dead `var _ = X` keep-alive lines whose purpose
  never materialised.

- **Style fixes (staticcheck S1002/S1023/ST1013).**
  `ditherStyle.GetBold() == false` → `!ditherStyle.GetBold()`,
  `m.paletteActive == false` → `!m.paletteActive`,
  401 literal → `http.StatusUnauthorized`, 6 redundant
  `; break` at end of switch cases. Applied gofumpt
  (trailing commas in multi-line calls).

- **Benchmark.** `BenchmarkFeedStoreLoadRecent_Dedup`
  (141µs/op for 1000 entries with 50% dups, 2KB allocs)
  locks in the O(n) dedup performance.

### Round 1 — initial audit (5 correctness + 9 new tests + 5 packaging)

- **Achievement dedup across restarts.** Previously every
  TUI launch re-unlocked all previously-earned achievements,
  which re-appended achievement cards in the feed on every
  session and (more visibly) made the on-disk discovery
  counter explode.
  `AchievementSystem.LoadFromStore` now hydrates
  `Items[].Unlocked` from the persisted `Store` on `NewApp`,
  and `FeedStore.LoadRecent` self-heals the feed by deduping
  entries with the same `(Kind, Title)` (bookmarks are
  preserved).

- **Missing mutex on `CheckSimAchievements`.** v9.13.x added
  `sync.Mutex` to `Check()` but missed `CheckSimAchievements()`.
  Caught by the new `TestAchievementSystem_ConcurrentCheck` under
  `go test -race`. Both functions now hold `mu` for the full
  read-modify-write of `Items[].Unlocked`.

- **Per-achievement batching in `checkAchievements`.** Was
  calling `m.store.IncrementDiscovery()` and `m.store.Save()`
  once per unlocked achievement — a discovery that fired
  FirstDiscovery + QualityS + MultiPaper would increment the
  counter 3x and rewrite the state file 3x. Both are now
  batched into a single call per `checkAchievements` invocation
  (i.e. once per discovery completion).

- **Overlay featured the wrong achievement.** `ShowOverlay` was
  called with `unlocked[len-1].Name` (the most recent unlock)
  but the render function picked `unlocked[0]` (registry-order
  first, always `AchFirstDiscovery`). Result: even after
  unlocking MultiPaper, the overlay still announced "First
  Discovery". Both the render and the show path now use the
  most recent unlock.

- **NewAppFresh diverged from NewApp.** Was missing
  `saveHistory: true`, had a dead `zoneId := 0` leftover from
  an old refactor. Both fixed; `newModelSkeleton` extracted
  as the shared constructor.

### New tests (audit invariant locks)

- `TestAchievementSystem_LoadFromStore` (+3 variants): hydrate
  from store, nil-store, idempotent, no-re-unlock-after-load.
- `TestAchievementSystem_ConcurrentCheck`: 8-goroutine race
  on Check + CheckSimAchievements. Catches the bug in #2.
- `TestFeedStore_LoadRecent_Dedup` (+2 variants): basic dedup,
  bookmark preservation, dedup-window over-read.
- `TestFeedPath_Preferred`: when `~/.c4reqber` exists, the
  feed lives there (not `~/.config/c4reqber`).
- `TestStateMachine_CheckAchievements_IncrementsOnce`:
  asserts the on-disk `DiscoveryCount` is 1 after a multi-
  unlock check (catches the per-achievement Save bug).
- `TestStateMachine_CheckAchievements_OverlayUsesLastUnlock`
  + `TestAchievementOverlay_ShowsMostRecentUnlock`: assert
  the overlay features the most-recent unlock, not the first.
- `TestStateMachine_KeyPress_NoDoubleTextareaUpdate`:
  asserts typing 'a' results in ta.Value() == 'a' (catches
  the round-1 input-breaking regression in the critical-UX
  fix above).

### Packaging (mac/win desktop)

- **Version sync.** Three files claimed `5.6.0` while the Go
  TUI is `v9.13.0` (`mac/Info.plist`, `c4reqber-desktop.spec`,
  `win/build.iss`). All three bumped to `9.13.0`/`913` with
  cross-reference comments so future bumps update all four
  places (CHANGELOG is the 4th).
- **Windows arm64 added.** Inno Setup installer was x64-only;
  the Makefile `release-all` target now also produces
  `c4tui-v9-windows-arm64.exe` for Snapdragon / Surface Pro X.
- **Windows launcher.bat fixes.** `blast init` → `%~dp0blast.exe
  init` (PATH lookup was unreliable for installer-bundled exes).
  Added missing C4_LANG / C4_API_EMAIL / C4_API_PASSWORD env
  exports (email/password auth was silently failing on Windows).
  Mirrored the mac splash header byte-for-byte.
- **mac Info.plist** gains `LSApplicationCategoryType`,
  `CFBundleCopyright`, `NSHumanReadableCopyright`, `CFBundleDisplayName`.
- **Python launcher_entry** removed the dead `_get_desktop_version`
  function that always returned `"v9"`. Splash banner now reads
  the version from the actual bundled TUI via the new
  `tui_launcher.tui_v9_version()` helper.

## v9.13.0 (2026-06-12) — friendely-merge-tui-upgrade
all 9/9 test packages pass under `go test -race`, `go vet` clean.
Branch: `feat/production-upgrade` (local commits only, no push).

### Correctness fixes (from v9.13.x audit)

- **Achievement dedup across restarts.** Previously every TUI
  launch re-unlocked all previously-earned achievements, which
  re-appended achievement cards in the feed on every session and
  (more visibly) made the on-disk discovery counter explode.
  `AchievementSystem.LoadFromStore` now hydrates `Items[].Unlocked`
  from the persisted `Store` on `NewApp`, and `FeedStore.LoadRecent`
  self-heals the feed by deduping entries with the same
  `(Kind, Title)` (bookmarks are preserved).

- **Missing mutex on `CheckSimAchievements`.** v9.13.x added
  `sync.Mutex` to `Check()` but missed `CheckSimAchievements()`.
  Caught by the new `TestAchievementSystem_ConcurrentCheck` under
  `go test -race`. Both functions now hold `mu` for the full
  read-modify-write of `Items[].Unlocked`.

- **Per-achievement batching in `checkAchievements`.** Was
  calling `m.store.IncrementDiscovery()` and `m.store.Save()`
  once per unlocked achievement — a discovery that fired
  FirstDiscovery + QualityS + MultiPaper would increment the
  counter 3x and rewrite the state file 3x. Both are now
  batched into a single call per `checkAchievements` invocation
  (i.e. once per discovery completion).

- **Overlay featured the wrong achievement.** `ShowOverlay` was
  called with `unlocked[len-1].Name` (the most recent unlock)
  but the render function picked `unlocked[0]` (registry-order
  first, always `AchFirstDiscovery`). Result: even after
  unlocking MultiPaper, the overlay still announced "First
  Discovery". Both the render and the show path now use the
  most recent unlock.

- **NewAppFresh diverged from NewApp.** Was missing
  `saveHistory: true`, had a dead `zoneId := 0` leftover from
  an old refactor. Both fixed; `newModelSkeleton` extracted
  as the shared constructor.

### New tests (audit invariant locks)

- `TestAchievementSystem_LoadFromStore` (+3 variants): hydrate
  from store, nil-store, idempotent, no-re-unlock-after-load.
- `TestAchievementSystem_ConcurrentCheck`: 8-goroutine race
  on Check + CheckSimAchievements. Catches the missing mutex.
- `TestFeedStore_LoadRecent_Dedup` (+2 variants): basic dedup,
  bookmark preservation, dedup-window over-read.
- `TestFeedPath_Preferred`: when `~/.c4reqber` exists, the
  feed lives there (not `~/.config/c4reqber`).
- `TestStateMachine_CheckAchievements_IncrementsOnce`:
  asserts the on-disk `DiscoveryCount` is 1 after a multi-
  unlock check (catches the per-achievement Save bug).
- `TestStateMachine_CheckAchievements_OverlayUsesLastUnlock`
  + `TestAchievementOverlay_ShowsMostRecentUnlock`: assert
  the overlay features the most-recent unlock, not the first.

### Packaging (mac/win desktop)

- **Version sync.** Three files claimed `5.6.0` while the Go
  TUI is `v9.13.0` (`mac/Info.plist`, `c4reqber-desktop.spec`,
  `win/build.iss`). All three bumped to `9.13.0`/`913` with
  cross-reference comments so future bumps update all four
  places (CHANGELOG is the 4th).
- **Windows arm64 added.** Inno Setup installer was x64-only;
  the Makefile `release-all` target now also produces
  `c4tui-v9-windows-arm64.exe` for Snapdragon / Surface Pro X.
- **Windows launcher.bat fixes.** `blast init` → `%~dp0blast.exe
  init` (PATH lookup was unreliable for installer-bundled exes).
  Added missing C4_LANG / C4_API_EMAIL / C4_API_PASSWORD env
  exports (email/password auth was silently failing on Windows).
  Mirrored the mac splash header byte-for-byte.
- **mac Info.plist** gains `LSApplicationCategoryType`,
  `CFBundleCopyright`, `NSHumanReadableCopyright`, `CFBundleDisplayName`.
- **Python launcher_entry** removed the dead `_get_desktop_version`
  function that always returned `"v9"`. Splash banner now reads
  the version from the actual bundled TUI via the new
  `tui_launcher.tui_v9_version()` helper.

## v9.13.0 (2026-06-12) — friendely-merge-tui-upgrade

TUI surface overhaul: simulation/verification engine capabilities are
now first-class. Every TUI element ties to a planned section. 27
atomic commits, +7302/-323 lines, 132 golden snapshots, 0 critical
bugs. Branch ready to merge into `friend-stack-merged`.

### §3 Information architecture — new panels + overlays

- **Status bar** (Ctrl+B, default ON at T2+): 1-line strip with
  connection state (●/◐/○), follow mode (▶/⏸), focused card
  N/total (▣), sim count this run (◆), capabilities summary (⏚).
  Renders between input and footer; suppressed at T0/T1.
- **Debug overlay** (Ctrl+Shift+D / `:debug`): full TUI state
  dump — viewport size, tick rate, SSE event history, feed
  stats (cards/bookmarks/zones), sim counters (run/total/cost/
  caps), memory estimate, current toast.
- **Command palette** (`:` / `:pal`): fuzzy-matches 35+ commands
  across 7 categories (App/Mode/Sim/Theme/Feed/Language/Help).
  Subsequence + prefix-bonus scorer; alphanumeric boundary
  detection. ↑/↓ to navigate, Enter to run, Esc to close, type to
  filter. Bindings in `commands/palette.go` + `registry.go`.

### §4 Adaptive layout — T0/T1/T2/T3 tiers

- New `ComputeLayout(w, h, showStatusBar)` pure function in
  `layout.go`. Width picks tier; height demotes (200×20 → T1,
  200×10 → T0). T3 adds a 32-col right rail.
- Status bar predicate now uses the layout engine instead of a
  hard-coded `if width < 100` check. Same rule, same place.
- 6 unit tests: tier, height-demotion, feed-never-below-3-rows.

### §5 Card system — CardSimulation kind, engine-aware actions

- Lifted Card into its own `cards` package. New `cards.State`
  (Active/Done/Errored/Focused/Expanded), `cards.SimFields`
  (engine/status/domain/pattern/verdict/cost/install-hint/
  fallback-chain/hypothesis-link), and monotonic `cards.NextID()`.
- Per-kind default action set: Hypothesis (`y e r s b`), Paper
  (`y o a s b`), Sim (`y e b` + status-dependent `i`/`f`/`o`).
- Per-particle fade in `effects.Burst` (was using `b.parts[0]`).
- Pooled grid in `effects.Rain` and `Burst` (was reallocating
  every frame; ~720k allocs/sec saved at 200×60×60fps).

### §6 Navigation

- j/k navigate cards (was unused after the c/j rename in v9.12).
- g g / G focus first / last card.
- 4 new actions in keymap: FocusPrev, FocusNext, FocusFirst, FocusLast.
- Old `j` (copy as JSON) rebinds to `Ctrl+J` to free up j.

### §7 Backend integration — typed SSE decoder wired

- New `api.TypedEvent` (12 canonical event types per §7.4):
  phase_progress, phase_change, paper_discovered, token_stream,
  cost_update, warning, log, sim_started, sim_finished, sim_skipped,
  sim_budget_exceeded, complete, failed, cancelled.
- New `api.DecodeTypedEvent(data)` + `api.LegacyExtract(data)`.
- `update.go` routes events through the typed decoder. New handlers:
  `handlePhaseEvent`, `handleSimEvent`, `handleCompleteEvent`,
  `handleFailedEvent`, `handleLegacyPhase` (safety net).
- `handleSimEvent` auto-links the sim to the most recent
  CardHypothesis if no explicit HypothesisID is set.

### §8 Streaming — fixed, typed

- extractResultFromSSEData replaced with LegacyExtract (typed).
- Cost update events now drive `m.simSpendThisSession` via
  `m.ApplySimCost(usd)`. The fake `tick/60*0.001` ticker is gone
  (was F-15 partial).
- (Full reconnect supervisor is the remaining §8 piece; deferred
  to v9.14 because the polling fallback works.)

### §9 Input

- `c` now copies the **focused** card (was always the last one).
- `i` on an unavailable CardSimulation toasts the install hint
  (e.g. `conda install -c conda-forge fenics-dolfinx`).
- `f` on a skipped CardSimulation toasts the fallback chain.
- `o` on an image-evidence CardSimulation opens the plot URL via
  the OS default browser (macOS: `open`, Linux: `xdg-open`,
  Windows: `rundll32`).
- New cross-platform helper `openURL(u)` in `card_helpers.go`.

### §10 Persistence — feed.jsonl + input history + resume

- New `persist.FeedStore` (append-only jsonl, ~50 lines) at
  `~/.config/c4reqber/tui-v9-feed.jsonl`. Atomic append via
  O_APPEND. LoadRecent(n) returns most-recent-first.
  Prune() keeps all bookmarked + last N normal entries.
- New `persist.InputHistory` (~50 lines) at
  `~/.config/c4reqber/tui-v9-input-history.json`. MRU with dedup
  on add. Capped at 200 entries.
- `appendCard` now writes to feed.jsonl (best-effort, _ = ignores
  errors so a broken disk doesn't block the UI).
- `NewApp` restores the last 50 cards from feed.jsonl before
  appending the empty placeholder. Toast: `restored N cards from
  last session`. (Bug fix: initial empty-placeholder was
  double-appended on restore; reordered.)
- Input history saved on every submit (Enter).

### §11 Theming — real colorMap integration

- New `Theme` helper (`theme.go`): pre-built `lipgloss.Style` per
  semantic name. `CardKindStyle(kind)` and
  `ConnectionStyle(state)` encode the per-kind/per-state visual
  rules.
- New **solarized-dark** profile added to the 6 existing profiles
  (warm low-blue palette, easy on eyes for 30+ minute sessions).
  Cycle order: default → hc → prot → deut → trit → mono →
  **solarized** → default.
- Theme rebuilds on every profile change (`m.theme = NewTheme(m.colorProfile)`).
- Header now prefixes active mode in a theme-colored pill:
  `[DISCOVER]` (success green).
- Status bar uses theme.ConnectionStyle for the conn dot.

### §12 Effects

- `Rain.Render` no longer allocates a `height×width` grid every
  frame; pools a single grid and reuses it. Early-exit when no
  drops are on screen (no allocation at all).
- `Burst.Render` no longer uses `b.parts[0]` for every cell's
  fade — each particle now computes its own fade. Pooled grid too.
- **New: `VerdictPulse` effect.** When a sim_finished event
  arrives with a verdict, the corresponding CardSimulation gets
  a 1.5s colored border pulse: green (supports), red (refutes),
  yellow (inconclusive). Triangle envelope 0→1→0.
- New `motion/budget.go` will respect reduced-motion setting in v9.14.

### §13 i18n parity — 100% across 7 langs

- Re-ran `i18n/pipeline/regen_i18n.py` over the 7 `.toml` files.
  Result: **178 keys × 7 languages = 1246 translation units, 100%
  parity**. The pipeline script is now the canonical source of
  truth; the generated `i18n.go` is committed.
- 69 new keys added during the v9.13 cycle: settings.sim_*,
  sim.action.*, sim.capabilities.title, achievement.sim_* (×4
  names + ×4 descs), and others.
- Russian, German, ZH, JA, AR, HI are translated to varying
  quality (RU best, others via initial pipeline pass + manual).
  Future translation passes should edit .toml + re-run pipeline.

### §14 Splash + Wizard

- **F-13 bug fixed**: `wizard.go:99` had `currentWizardStep =
  func() int { return 0 }` — the wizard never advanced past
  step 0 regardless of what m.wizard.step was. Refactored to
  pass step explicitly: `RenderWizard(width, height, step int)`.
  All 3 wizard steps now render correctly.
- Splash unchanged in this release (4s skip-after-3-launches
  is the new behavior; same `crystal → dissolve → idle` flow).

### §15 Debug overlay — covered above (§3)

### §16 Settings + Command palette — covered above (§3)

Settings row additions (settings_menu.go):
- settings.sim_preference: auto / cpu_only / off
- settings.sim_cost_limit: $5.00 default
- settings.sim_spend: live running total
- settings.capabilities_status: capsim.ShortSummary(r)

These are read-only displays in the current implementation; the
inline-edit picker is a v9.14 feature (the row type system in
settings needs a real form widget, not just a label).

### §17 Achievements — 4 new sim-specific

- AchSimExplorer: 5+ different sim engines ran successfully.
- AchSimSaver (Devil's Advocate): got a refutes_hypothesis verdict.
- AchSimChef (Fallback Chef): 3+ sim cards with status skipped
  or unavailable (fallback chain invoked).
- AchSimDelegate (Cloud Native): at least one sim delegated
  to cloud (vast.ai).

Total: 11 achievements (was 7). New `AchievementSystem.CheckSimAchievements(feed)` walks the feed and unlocks per the 4 rules.

### §18 Golden snapshots — 132 total (target was 96)

- Generator in `golden_snapshots_test.go` (renamed from
  `golden_gen.go` to fix Go's `_gen.go` test-exclusion bug).
- 6 device fixtures × 22 scenarios = **132 golden files**, all
  stable across 5/5 consecutive test runs.
- 22 scenarios: empty / hypothesis / multi-paper / sim / error
  / expanded / focused / focused-expanded / full-hypothesis /
  verdict-chips / sim-supports / sim-refutes / sim-inconclusive /
  sim-skipped / bookmark / palette / help-shown / settings-open /
  achievement-shown / mixed-feed / capsim / debug.
- Time-of-day fields normalized to `<CLOCK>` placeholder so
  renders are stable across runs.
- Coarse ANSI strip (drops `\x1b`, keeps per-character). Output
  is byte-stable but visually ugly when cat'd; a proper ANSI
  parser is a follow-up.
- Update workflow: `UPDATE=1 go test -run TestGoldenSnapshotsAll`.

### §19 Roadmap — 8 sprints

The 7-sprint plan was extended to 8 (S4b added for the sim
surface). All 8 sprints done in a single sustained session of
~10 hours (Sprint 1 through Sprint 7 + polish + tests + docs).

### §20 Decision log — extended

Six new design decisions documented (D-01 through D-06):
- D-01: CardSimulation is a first-class card kind
- D-02: Capabilities are a first-class overlay (Ctrl+Shift+C)
- D-03: Engine unavailability is a first-class state (CardSimulation
  with status="unavailable" + install hint + i action)
- D-04: Fallback chains are explicit (PatternEngineMap.FALLBACK_CHAIN)
- D-05: Sim card actions are engine-aware (per §23.6)
- D-06: Verdict chips on hypothesis cards (✓/✗/? color-coded)

### §22-25 Simulation surface — fully realized

- CardSimulation kind is rendered in feed with status icon, engine,
  pattern, domain, verdict, cost, fallback chain, install hint.
- Capabilities overlay (Ctrl+Shift+C) shows 32 engines + 27
  verifiers, grouped by 12 domains, with install hints for
  unavailable engines.
- Opening the capabilities overlay appends 1 summary
  CardSimulation + up to 6 per-engine unavailable cards to the
  feed (D-03 fully realized).
- Verdict chips on hypothesis cards link to linked sims.
- 4 new sim achievements.

### Real bugs fixed

- `wizard.go:99`: wizard step never advanced (F-13 / audit B8).
- `effects.Rain.Render`: 720k allocs/sec at 200×60×60fps → 0.
- `effects.Burst.Render`: per-cell fade used `b.parts[0]` →
  per-particle fade.
- `NewApp`: empty placeholder double-appended on restore →
  reordered (restore first, then placeholder if no restored cards).
- `persist.InputHistory.Add`: deadlock via `Add → save → Lock` →
  save() now expects caller to hold the lock.
- `TestCtrlY_CyclesLLMTier`: HOME pollution from earlier debug
  sessions caused flaky failures → `t.Setenv("HOME", tmp)`.

### Test stats

- 13 new test files (cards, capsim, layout, sim_summary, verdict_chips,
  status_bar, theme, sim_handlers, palette, expansion, achievement,
  cost, golden_snapshots, feed_persist, persistence in persist/).
- ~60 new unit tests added. All targeted runs pass 3+/3 in batch.
- 132 golden snapshot files, stable 5/5 consecutive.
- Pre-existing flakiness in `TestHelp_RenderContainsTitle`,
  `TestTipShortcuts_PlatformAware`, `TestGoldenEmptyState_*`,
  `TestAchievementOverlay_*` confirmed independent of these
  changes (verified via git worktree on friend-stack-merged HEAD
  before any of my changes).

### Branch

`friendely-merge-tui-upgrade` — 27 commits ahead of
`friend-stack-merged`, ready to push to GitLab and open the MR.

---

## v9.12.6 (2026-06-11) — prior HEAD
- **Phase C chunked 7× parallel**: 386 papers → 73.5s (was 300s+)
- **Phase F LLM retry**: try/except → fallback to original hypothesis
- **Two-mode dissertation**: `human` (clean paper) / `explain` (with tech appendix)
- **Full citation traceability**: numbered refs [1]..[N], DOI, BibTeX
- **Per-stage LLM routing**: A=local → D=premium → G=cheap
- **UI/UX**: gradient progress bar █▊▋▌▍▎▏, sub-timer (`+2m34s`), phase in footer
- **Bugfix**: `_pick_centroids` order mismatch (as_completed → dict keyed by index)

## v9.12.0 (2026-06-10)
- **Discovery submit FIXED**: `_ = submitCmd` → `return m, cmd` (HTTP request now fires!)
- **Auth chain errors**: `_ = Health/Register/Login` → chained error propagation
- **SSE streaming**: `m.sseEvents` was never assigned → now continuous stream
- **Header/footer Unicode**: `⟨⟩🇬🇧` caused lipgloss.Width overflow → ASCII-safe `len([]rune())`
- **Store.Save() errors**: 4 silent `_ = store.Save()` → toasts on failure
- **Backend register 500**: IntegrityError (duplicate email) → 200 with existing user
- **Citation chaser crash**: DOI with parentheses `(03)` → skip invalid IDs
- **Semantic Scholar rate limit**: S2 disabled in orchestrator + citation chaser
- **i18n**: 300+ context fixes for ZH/JA/DE/AR/HI (was machine translation garbage)

## v9.11.0 (2026-06-10)
- **Platform-aware KeyMap**: Cmd+L on macOS, Ctrl+L on Linux — no system conflicts
- **22 new tests for KeyMap**

## v9.10.3 (2026-06-10)
- **Splash polish**: subtitle, motto, Russian easter egg, colored "Shift paradigms"
- **C4R symmetry**: C and R now 18 chars wide, walls 4 chars

## v9.10.0 (2026-06-10)
- **BioAurora**: bio-cognitive wave color morphing (3 sine waves, sub-1Hz)
- **Achievement overlay**: fullscreen unlock animation
- **Settings menu**: Ctrl+, → ↑/↓ navigate → Enter select
- **128 i18n keys × 7 languages**

## v9.9.0 (2026-06-10)
- **Splash screen**: 3-phase crystal → dissolve → waiting
- **CLI subcommands**: --demo, --story, --stats, --history, --version
- **Color profiles**: 6 profiles (default, HC, protanopia, deuteranopia, tritanopia, monochrome)

## v9.8.0 (2026-06-10)
- **Settings persistence**: tier/profile/lang saved to `~/.config/c4reqber/tui-v9-state.json`
- **SSE reconnect**: exponential backoff on stream disconnection
- **First-run wizard**: 3-step setup on first launch

## v9.7.0 (2026-06-10)
- **Per-stage LLM routing**: C1=deepseek ($0.001), C2=qwen-72b ($0.012), C3=claude-3.5 ($0.045)
- **Color profiles**: 6 accessibility profiles for color-blindness

## v9.6.0 (2026-06-10)
- **Env config**: `C4_API_URL`, `C4_TIER` environment variables
- **Help overlay**: `?` key shows platform-specific keymap
- **History persistence**: Ctrl+C saves telemetry to JSON
- **First-run wizard**: 3-step welcome + keys + demo/real choice

## v9.5.0 — v9.0.0
- Initial TUI v9 implementation: single-screen feed-driven discovery UI
- 4-region layout (header, feed, input, footer)
- 5 card types (CardEmpty, CardPhase, CardHypothesis, CardPaper, CardError)
- 5 game-feel effects (Rain, Burst, Slide, Typewriter, Sparkles)
- 7 languages (en, ru, zh, ja, de, ar, hi)
- Achievement system (7 kinds)
- Dream mode (idle visual effects)
- Headless probe binary for CI
