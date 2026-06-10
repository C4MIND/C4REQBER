# Changelog — TUI v9 + Backend Pipeline

## v9.12.6 (2026-06-11) — Current HEAD
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
