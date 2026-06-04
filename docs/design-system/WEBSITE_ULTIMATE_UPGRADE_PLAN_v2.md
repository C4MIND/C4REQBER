# C4REQBER GitSite — Ultimate Upgrade Plan v2

> **Status:** Post-Architecture Deep Dive  
> **Sources:** AGENTS.md, README.md, CHANGELOG.md, ARCHITECTURE_C4R.md, ARCHITECTURE_TUI_V8.md  
> **Constraint:** Living Quantum Mascot (bottom-left) is sacred — do not touch.

---

## Executive Summary

C4REQBER is a **cognitive-scientific discovery platform for humans and AI agents** that treats hypothesis generation as a formal, verifiable process. After deep analysis of all technical documentation, the current GitSite captures perhaps 30% of the project's actual depth. The site must evolve from a feature list into an **interactive demonstration of cognitive topology**.

| Category | Score | Gap |
|----------|-------|-----|
| Design System | 7/10 | Needs TUI v8 color sync (#00FF41 matrix green) |
| Accessibility | 7/10 | Missing aria-live, roles, high-contrast mode |
| Performance | 6/10 | No build system; 1800+ line inline file |
| SEO | 6/10 | Missing OG image, sitemap, FAQ schema |
| Mobile | 7/10 | Basic breakpoints; needs touch optimization |
| UX/Content | 5/10 | **Missing 20+ sections** documented in architecture |
| Visual Polish | 6/10 | Needs Data Flow viz, Cube viz, Pipeline viz |

**Overall: 6.3/10** — Solid foundation. Massive content gap.

---

## Part 0: Sacred Constraints

### 0.1 Living Quantum Mascot (DO NOT TOUCH)
- Position: fixed, bottom: 20px, left: 20px
- 3-frame ASCII cube animation (already fixed — right wall aligned)
- i18n comments cycling every 3s
- This is the project's soul. Preserve exactly.

### 0.2 Positioning Correction
**Current:** "Cognitive Exoskeleton for AI Agents"  
**Correct:** "Cognitive Exoskeleton for Humans and AI Agents"

The platform is explicitly designed for both:
- **Humans** use TUI, CLI, FastAPI web interface
- **AI Agents** connect via MCP server with 20+ tools
- Both share the same cognitive pipeline (C4 → QZRF → Knowledge → Simulation → Verification)

---

## Part 1: Architecture-Aware Content Gaps

### 1.1 The 7 Metamodels — Cognitive Engine Deep Dive
**Current:** Only C4-META mentioned. QZRF, MP, CDI, TOTE, MatrixDream, IMPACT invisible.
**Action:**
- Add section "7 Cognitive Metamodels" with interactive cards
- **C4 Space**: Z₃³ grid visualization (3×3×3 cube, 27 states)
- **QZRF**: Quantum Z-Operators — show Z-Shift, Z-Scale, Z-Agent, Z-Resonance
- **MP Rotation**: Multi-Perspective Engine — 9+ perspectives (scientific, engineering, philosophical, economic)
- **CDI**: Contradiction Detection & Integration — Detect → Analyze → Resolve
- **TOTE**: Test-Operate-Test-Exit loop — iterative refinement visualization
- **MatrixDream**: Latent space traversal — vector embedding, cross-domain analogies
- **IMPACT**: Entity-Relation Extraction — Identify → Map → Classify → Trace

Each card: icon + 2-sentence explanation + "Learn more" → links to ARCHITECTURE_C4R.md anchors

### 1.2 C4 Cube — Interactive 3×3×3 Visualization
**Current:** No visual representation of the cognitive coordinate system.
**Action:**
- Build CSS 3D cube (no Three.js) showing 27 states
- Axes: Time (Past/Present/Future), Scale (Concrete/Abstract/Meta), Agency (Self/Other/System)
- Hover per cell → show state label + cognitive mode description
- Example states:
  - `000` = Personal concrete memories
  - `111` = Current abstract collaboration
  - `222` = System-level future vision
- Add operator buttons: T (Time shift), S (Scale shift), A (Agency shift)
- Show Theorem 11: "Any state reachable in ≤3 steps"
- Link to `src/tui/cube_navigator.py` for navigation logic

### 1.3 Data Flow — Sanitize → C4 → Knowledge → Hypothesis → Simulation → Verify → Output
**Current:** No visual data flow diagram.
**Action:**
- Create animated SVG/Canvas flow diagram
- 7 stages with connecting arrows:
  1. **Sanitize** → strip HTML, normalize unicode, block injection
  2. **C4 Space** → fingerprint into Z₃³ coordinate
  3. **Knowledge + Cognitive** → 33 sources + QZRF/CDI analysis
  4. **Hypothesis Generation** → multi-agent debate
  5. **Simulation** (36 engines) + **Verification** (Lean4/Dafny/Z3)
  6. **Quality Gates** → 8-gate scoring
  7. **Output** → Dissertation / Article / Blueprint / Code / Verification Report
- Each stage clickable → expands with details, timing, example output
- Show parallel paths: Knowledge Search ↔ Cognitive Analysis (bidirectional)

### 1.4 Multi-Agent Debate — Analyst, Scientist, Critic, Synthesizer
**Current:** Not mentioned. This is a core differentiator.
**Action:**
- Section "4 Minds, 1 Discovery"
- **Analyst**: Breaks problem into entities, maps dependencies, ranks by centrality
- **Scientist**: Generates hypotheses via TRIZ, C4 navigation, literature gaps
- **Critic**: Nature reviewer persona, falsification engine, Platt's Strong Inference
- **Synthesizer**: Resolves contradictions (CDI), builds consensus, writes dissertation
- Visual: 4 avatar cards in debate formation, showing dialogue bubbles with example reasoning
- Show consensus meter (93.3% typical)

### 1.5 24 Scientist Paths — Competitive Moat
**Current:** Not mentioned. AGENTS.md says this is 2-4 years to replicate.
**Action:**
- Section "24 Paths of Discovery"
- Grid of scientist archetypes with C4 coordinates:
  - Einstein → (T1, S2, A2) — Abstract future system-thinking
  - Turing → (T1, S0, A1) — Present concrete other-directed
  - Darwin → (T0, S1, A2) — Past abstract system-level
  - Curie → (T1, S0, A0) — Present concrete self-experimentation
- Each path shows: coordinates → domain → famous discovery → how C4REQBER navigates it
- Animated path traversal: dot moves through Z₃³ space showing state transitions

### 1.6 162+ Simulation Patterns — Pattern Engine Map
**Current:** "36 engines" mentioned but not the pattern-to-engine mapping.
**Action:**
- Section "162+ Simulation Patterns"
- Interactive Pattern → Engine matcher
- Categories: CFD, MD, Quantum, Neuro, Climate, Robotics, Bio, Astro, etc.
- Show GPU vs CPU patterns, acceleration factors
- Example: `navier_stokes` → Newton (GPU) or OpenFOAM (P1)
- Example: `protein_folding` → OpenMM (GPU) or GROMACS (P1)
- Link to `src/simulations/pattern_engine_map.py`

### 1.7 TUI v8 — Terminal Experience Showcase
**Current:** No visual of the terminal interface.
**Action:**
- Section "The Terminal is the Interface"
- Animated terminal mockup showing:
  - ASCII C4 cube with arrow-key navigation (←↑↓→)
  - Living Quantum Mascot with thinking states
  - Gradient bars (█▊▋▌▍▎▏░) with cyan→magenta glow
  - Spark particles on keypress
  - Phase swoosh: `A ▁▂▃▄▅▆▇█████ B`
  - Night mode auto-toggle (after 23:00)
- Keyboard shortcuts cheat sheet (Tab, A, B, D, T, R, V, G, M, I, F)
- Show real `blast` commands with output:
  ```
  c4reqber ❯ blast solve "quantum biology in photosynthesis"
  [C4] State: F⟨Present, Abstract, Other⟩ (T=0, S=0, A=0)
  [TRIZ] Segmentation · Extraction · Local Quality
  [UCOS] 4-layer analysis complete
  ...
  ```

### 1.8 MCP Server — 20+ Tools for AI Agents
**Current:** Mentioned in stats, no detail.
**Action:**
- Section "Built for AI Agents — MCP Native"
- Show 20 tool cards in 4×5 grid:
  - `c4_solve`, `c4_search`, `c4_triz`, `c4_fingerprint`, `c4_verify`
  - `c4_prove`, `c4_transfer`, `c4_simulate`, `c4_bayesian`, `c4_causal`
  - `c4_export`, `c4_social`, `c4_autoresearch`, `c4_chain`, `c4_meta`
  - `blast_solve`, `blast_turbo`, `blast_flash`, `blast_turbofactory`, `blast_auto`
- Each card: tool name + 1-line description + JSON Schema badge
- Show integration code:
  ```json
  {"name": "c4_solve", "inputSchema": {...}, "outputSchema": {...}}
  ```
- `blast serve --mcp` command block with copy button
- Target audiences: Claude, Cursor, Continue.dev, Cline

### 1.9 Social Publishing — 9 Platforms
**Current:** Not mentioned. 17 modules, 5 poster implementations.
**Action:**
- Section "Publish Everywhere"
- Platform grid: arXiv, bioRxiv, Zenodo, Reddit, Discord, Slack, Telegram, Twitter/X, Bluesky
- Show workflow: Dissertation → LaTeX + BibTeX → Auto-upload → ORCID registration → Social blast
- Zenodo DOI badge, arXiv submission screenshot
- ORCID integration: "Link your researcher identity"

### 1.10 Paradigm Shift Results — Proof of Work
**Current:** Not shown. Real results exist in discovery/batch_v*/
**Action:**
- Section "Paradigm Shifts Detected"
- Card 1: Sleep as active maintenance → `ALREADY_SHIFTED` (100%)
  - Excerpt from generated dissertation
  - Verification: Lean4 proof skeleton + consensus meter
- Card 2: Language horizontal gene transfer → `SHIFTED` (66.67%)
  - Full article (4,985 chars, Russian)
  - 10 sources, Bayesian AUC: 0.32, uncertainty: 0.34
- Link to `discovery/batch_v6/`, `discovery/batch_v7/exports/`
- Badge: "Real results. Real citations. Real verification."

### 1.11 Security & Code Quality — Trust Architecture
**Current:** Badge only.
**Action:**
- Section "Hardened for Production"
- Metrics dashboard:
  - 0 CRITICAL / 0 HIGH / 55 MEDIUM / 14 LOW (Round 4 Audit)
  - 0 mypy errors across 1145 files
  - 0 ruff errors across `src/`
  - 594 tests passing
  - 222 total fixes across 4 rounds
- Security features grid:
  - Prompt injection: nonce delimiters + LaTeX escaping + HTML entity decoding
  - SSRF: Paper ID validation, redirects disabled
  - Subprocess: Shell metacharacter blocking, symlink guards
  - Path traversal: Confined to `~/.c4reqber`
  - Auth: JWT + HMAC, dev-mode bypass with token
- Timeline: v5.4.0 → v5.4.1 → v5.4.2 → v5.5.0 with fix counts

### 1.12 Graceful Degradation & Resilience
**Current:** Not mentioned. Core architecture principle.
**Action:**
- Section "Works Everywhere, Fails Nowhere"
- Show 3 principles from ARCHITECTURE_C4R.md:
  1. **Graceful degradation** — every component works standalone; failures cascade to safe defaults
  2. **Lazy loading** — GPU engines, Web3, telemetry load on demand
  3. **Developer-first** — dummy secrets with warnings; production via env vars
- Visual: Circuit breaker pattern diagram
- Examples:
  - GPU unavailable → automatic CPU fallback
  - API key missing → source works with reduced rate limits
  - Engine not installed → install hint + toy fallback
  - Lean4 not found → fallback to Z3 + proof skeleton

### 1.13 Output Examples Gallery — 6 Formats
**Current:** No examples.
**Action:**
- Section "What You Get" with tabbed interface
- Tabs: Dissertation | Article | Blueprint | Code | Verification Report | Whitepaper
- Each tab shows real generated output (truncated):
  - Dissertation: LaTeX preview with sections, citations, figures
  - Article: Markdown with headers, tables, references
  - Blueprint: API specification with endpoints, schemas
  - Code: Python implementation with docstrings
  - Verification Report: Lean4/Coq proof state
  - Whitepaper: Architecture document
- Auto-detection logic: keywords trigger format selection

### 1.14 Research Audiences — 6 Domains (Expanded)
**Current:** 5 cards exist but weak.
**Action:**
- Expand to 6 with concrete CLI examples per domain:
  - **Hard Science**: `blast solve "graphene superconductivity mechanism" --verify`
  - **Psychology**: `blast solve "CBT efficacy for treatment-resistant depression"`
  - **Clinical**: `blast solve "biomarker panel for early Alzheimer's detection"`
  - **Climate**: `blast solve "ocean acidification impact on coral microbiome"`
  - **Law**: `blast solve "regulatory arbitrage in cross-border fintech"`
  - **Economics**: `blast solve "behavioral nudge effectiveness in pension enrollment"`
- Each card: domain icon + example output snippet + relevant engine logos

### 1.15 How It Works — 12-Step Visual Pipeline
**Current:** Static phase table.
**Action:**
- Replace with interactive timeline:
  1. C4 Navigation (Z₃³ fingerprint)
  2. TRIZ Contradiction (40 principles)
  3. FRA Routing (situation fingerprint)
  4. UCOS 4-Layer Analysis
  5. QZRF Operators (14 operators)
  6. Gap Mining (124 papers, 12 gaps)
  7. Hypothesis Generation (LLM + TRIZ)
  8. Simulation (auto-select engine)
  9. Formal Verification (Lean4/Coq/Dafny)
  10. Novelty Validation (HARD GATE)
  11. Self-Critique (Nature reviewer)
  12. Quality Control (8-gate scoring)
- Each step: icon + duration estimate + expandable details
- Show parallel execution: steps 2-5 run concurrently
- Add "Run Demo" → simulates pipeline with progress bars

### 1.16 Extension Points — Developer API
**Current:** Not mentioned. Critical for OSS adoption.
**Action:**
- Section "Extend Everything"
- Show 7 extension points from architecture:
  1. **New knowledge source** → `src/knowledge/sources/`
  2. **New simulation engine** → `*_bridge.py` + `BaseSimulationAdapter`
  3. **New cognitive model** → `src/metamodels/`
  4. **New pipeline phase** → `_phase_*` method
  5. **New CLI command** → `src/cli/typer_*.py`
  6. **New API endpoint** → `src/api/routers/`
  7. **New MCP tool** → `src/mcp_server/blast_tools.py`
- Each point: code snippet + link to docs

---

## Part 2: Design System v2 — TUI v8 Color Sync

### 2.1 TUI v8 Color Palette (Add to existing)
Current site uses DESIGN.md teal (`#4ECDC4`). TUI v8 uses Matrix Green (`#00FF41`).
**Action:**
- Keep DESIGN.md as base, add TUI accent layer:
  - `--tui-primary: #00FF41` (Matrix Green) — for terminal/code elements
  - `--tui-secondary: #00D4FF` (Cyber Cyan) — for info states
  - `--tui-accent: #FF006E` (Neon Pink) — for highlights, badges
- Use TUI colors for: terminal blocks, code snippets, mascot glow, pipeline progress
- Keep DESIGN.md colors for: cards, buttons, backgrounds, text
- Result: "Brand colors for UI, TUI colors for code" — dual identity

### 2.2 Terminal Aesthetic Enhancement
**Action:**
- Terminal blocks: add left border accent `border-left: 2px solid var(--tui-primary)`
- Code syntax highlighting with TUI colors:
  - Keywords: `#00FF41`
  - Strings: `#00D4FF`
  - Comments: `#6C7086`
  - Functions: `#FFD93D`
- Add scanline effect (CSS `repeating-linear-gradient`) to terminal sections
- Cursor blink animation for terminal prompts
- Font: `JetBrains Mono` (already added) with `font-variant-ligatures: none`

### 2.3 Living Quantum Mascot Zone
**Action:**
- Keep mascot position and animation exactly as is
- Add subtle glow behind mascot: `box-shadow: 0 0 40px rgba(0,255,65,0.1)`
- Ensure mascot text uses `--tui-primary` color
- Mascot is the bridge between site aesthetic and TUI aesthetic

---

## Part 3: Layout & Component Fixes

### 3.1 Hero Section v2
**Action:**
- Update subtitle: "The cognitive exoskeleton for **humans and AI agents**."
- Add tagline: "27 states. 36 engines. 6 verifiers. 162+ patterns. One command."
- Terminal mockup showing actual `blast solve` output with TUI colors
- Live GitHub stars badge (shields.io dynamic)
- Scroll-down chevron with bounce animation
- CTA primary: "pip install c4reqber" (copy on click)
- CTA secondary: "See How It Works" (scrolls to pipeline)
- CTA tertiary: "MCP Docs" (for AI agents)

### 3.2 Stats Grid (Fixed ✓ — 2 rows × 3)
**Remaining:**
- Animate counters from 0 on scroll-into-view
- Add sparkline mini-chart per stat
- Consider 7th stat: "162+ Patterns" or "0 mypy Errors"

### 3.3 First Principles Grid (Fixed ✓ — 2×2)
**Remaining:**
- Replace emoji ❌ with Lucide `XCircle` SVG icons
- Add flip/accordion: click to reveal c4reqber solution
- Front: "No Simulation" → Back: "36 engines + PatternRunnerV2 auto-select"

### 3.4 Comparison Tables (Fixed ✓)
**Remaining:**
- Add filter chips: "All" | "Cognition" | "Verification" | "Simulation"
- Radar chart option for C4-META comparison (Chart.js or SVG)
- Highlight c4reqber column with `--tui-primary` glow

### 3.5 Navigation v2
**Action:**
- Links: Features | C4 Cube | Pipeline | MCP | TUI | Engines | Docs | GitHub
- Mobile: hamburger → slide-out drawer with backdrop
- Active section highlight via IntersectionObserver
- Hide-on-scroll-down, show-on-scroll-up
- Floating "Install" button that copies command

---

## Part 4: Technical Implementation

### 4.1 Build System (Vite)
```bash
npm init -y
npm install -D vite postcss autoprefixer
# src/styles/ — CSS with custom properties
# src/scripts/ — ES modules (i18n, animations, cube)
# npm run dev — HMR local dev
# npm run build — outputs to dist/
```

### 4.2 Critical CSS Extraction
- Inline above-fold CSS (~15KB)
- Defer non-critical CSS
- Preload fonts with `font-display: swap`

### 4.3 Interactive Components (Vanilla JS)
- **C4 Cube**: CSS 3D transforms, no library
- **Pipeline Timeline**: CSS animations + JS state machine
- **Pattern Matcher**: JS filtering, no framework
- **FAQ Accordion**: Native `<details>` + CSS
- **Tabbed Gallery**: JS class toggling
- **Counter Animation**: IntersectionObserver + requestAnimationFrame

### 4.4 Performance Targets
| Metric | Current | Target |
|--------|---------|--------|
| Lighthouse Performance | ~60 | 95+ |
| Lighthouse Accessibility | ~70 | 95+ |
| Lighthouse Best Practices | ~80 | 95+ |
| Lighthouse SEO | ~60 | 95+ |
| Time to Interactive | ~4s | <2s |
| First Contentful Paint | ~2s | <1s |

---

## Part 5: SEO & Meta Enhancement

### 5.1 Open Graph Image
- 1200×630px, dark background
- C4 cube ASCII art + "C4REQBER" + tagline
- TUI green (`#00FF41`) accent on black (`#0F1117`)

### 5.2 Structured Data
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "C4REQBER",
  "description": "Cognitive-scientific discovery platform for humans and AI agents. 27 cognitive states, 36 simulation engines, 6 formal verifiers, 33 knowledge sources.",
  "applicationCategory": "ScientificResearchApplication",
  "operatingSystem": ["macOS", "Linux"],
  "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
  "softwareVersion": "5.5.0",
  "programmingLanguage": "Python",
  "license": "https://www.gnu.org/licenses/agpl-3.0.html",
  "codeRepository": "https://github.com/c4reqber/c4reqber"
}
```

### 5.3 Additional Meta
- `theme-color: #0F1117` (mobile browser)
- `msapplication-TileColor: #00FF41`
- Canonical URL: `https://c4reqber.org`
- `robots.txt` + `sitemap.xml`

---

## Part 6: Mobile & Responsive

### 6.1 Breakpoints
- `320px`: Minimal — single column, compact nav
- `480px`: Small — 2-column stats, stacked cards
- `768px`: Tablet — hamburger nav, 2×2 grids
- `1024px`: Desktop — full nav, 3-column stats
- `1440px`: Wide — max-width container, larger type

### 6.2 Touch Optimization
- Min tap target: 44×44px
- Table horizontal scroll with fade hint
- CTA buttons: full-width on mobile
- Terminal blocks: horizontal scroll preserved

### 6.3 Reduced Motion
- Respect `prefers-reduced-motion`
- Disable orb animations, cube rotation
- Keep content accessible without motion

---

## Part 7: Content Rewrites

### 7.1 Hero
```
C4REQBER
The cognitive exoskeleton for humans and AI agents.

27 states · 36 engines · 6 verifiers · 162+ patterns · One command.

[ pip install c4reqber ]  [ See How It Works ]
```

### 7.2 Meta Description
```
C4REQBER — cognitive-scientific discovery platform. 27-state C4 topology, 
36 simulation engines, 6 formal verifiers, 33 knowledge sources, 20 MCP tools. 
For researchers and AI agents. AGPL-3.0.
```

### 7.3 Key Messages (Repeat Throughout)
1. "Not an LLM wrapper. A cognitive operating system."
2. "Your hypotheses don't just claim — they prove."
3. "From question to verified dissertation. One command."
4. "Built for humans. Accessible to AI agents."
5. "0 mypy errors. 0 CRITICAL findings. Production hardened."

---

## Part 8: Competitive Moat Visualization

### 8.1 Replication Barrier Chart
```
C4-META Z₃³ Topology     ████████████████████ 3-5 years
24 Scientist Paths       ████████████████░░░░ 2-4 years
Formal Verification      ██████████░░░░░░░░░░ 1-2 years
WASM Plugin Runtime      ████████████░░░░░░░░ 1-3 years
SystemAnalyzer           ████████░░░░░░░░░░░░ 1-2 years
```

### 8.2 "Why Not Just Use ChatGPT?" Section
- ChatGPT: generates text → no verification → no simulation → no citations
- c4reqber: generates hypothesis → simulates → verifies → cites → publishes
- Show side-by-side comparison with real output difference

---

## Part 9: Engine Roadmap — Planned Integrations

### 9.1 Extract Planned Engines from Table
**Current:** CESM and JuliaDiff are inside the Simulation Engines table with "Planned" status, cluttering the available-now view.
**Action:**
- Remove CESM and JuliaDiff rows from `comp-table` in Simulation Engines section
- Create new section "Engine Roadmap" after the engines table
- Display as beautiful cards/list (NOT a table):

```
┌─ Engine Roadmap ──────────────────────────────────────┐
│                                                        │
  🌍 Climate          CESM          Earth system modeling
  🔢 Math             JuliaDiff     Automatic differentiation
│                                                        │
│  Plus from v5.6/v5.7 roadmap:                         │
│  • FEniCSx / dolfinx FEM bridge                        │
│  • OpenMM protein dynamics                             │
│  • DeepChem drug discovery                             │
│  • PyMC / Bambi Bayesian stats                         │
│  • ArviZ Bayesian visualization                        │
│  • LangGraph state-machine agents                      │
│  • Unsloth local LLM fine-tuning                       │
│  • vLLM high-throughput inference                      │
│  • ChromaDB / LanceDB RAG layer                        │
│  • CrewAI multi-agent orchestration                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

- Style: `--bg-2` background, `--border` border, `--radius-lg` corners
- Each planned engine: domain icon + name + description + status badge "Planned"
- Group by domain (Climate, Math, Bio, ML, etc.)
- Add timeline hint: "v5.6 Q3 2026 | v5.7+ 2027"

---

## Part 10: Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Extract CSS/JS to files (Vite setup)
- [ ] Add all meta tags, OG image, manifest
- [ ] Fix remaining a11y issues (aria-live, roles)
- [ ] Add mobile hamburger menu
- [ ] Update all positioning copy: "humans and AI agents"

### Phase 2: Core Content (Week 2)
- [ ] Add C4 Cube 3×3×3 visualization (CSS 3D)
- [ ] Add Data Flow diagram (animated SVG)
- [ ] Add "How It Works" 12-step interactive pipeline
- [ ] Add Output Examples Gallery (6 formats)
- [ ] Expand FAQ to 10 questions

### Phase 3: Differentiators (Week 3)
- [ ] Add 7 Metamodels section
- [ ] Add Multi-Agent Debate visualization
- [ ] Add MCP Server 20-tool grid
- [ ] Add TUI Terminal Experience mockup
- [ ] Add Security & Quality dashboard
- [ ] Add Graceful Degradation section

### Phase 4: Proof & Community (Week 4)
- [ ] Add Paradigm Shift Results (batch_v6/v7)
- [ ] Add 24 Scientist Paths (or defer to v2)
- [ ] Add 162+ Simulation Patterns
- [ ] Add Social Publishing section
- [ ] Add Extension Points for developers

### Phase 5: Polish (Week 5)
- [ ] Animation audit (counters, orbs, scroll reveals)
- [ ] Performance optimization (Lighthouse 95+)
- [ ] Cross-browser testing
- [ ] Mobile testing
- [ ] Analytics setup (Plausible/Fathom)

---

## Part 10: Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Lighthouse Performance | 95+ | Chrome DevTools |
| Lighthouse Accessibility | 95+ | Chrome DevTools |
| Lighthouse SEO | 95+ | Chrome DevTools |
| Time to Interactive | <2s | WebPageTest |
| Scroll Depth to Pipeline | >80% | Analytics |
| CTA Click Rate | >5% | Analytics |
| Bounce Rate | <40% | Analytics |
| Mobile Viewport Score | 90+ | Lighthouse |

---

## Notes

- **Mascot is sacred.** Do not move, resize, or restyle. Only ensure it uses `--tui-primary` color.
- **Preserve terminal aesthetic.** This is the brand identity. Use TUI colors for code, DESIGN.md colors for UI.
- **i18n everything.** All new strings must be in the i18n system (7 languages).
- **AGPL-3.0 visibility.** License badge must be above fold. "Open source" is a key differentiator.
- **No enterprise SaaS positioning.** This is research-grade, terminal-first, BYOK.
- **Real data only.** All examples must reference actual files in the repo (discovery/batch_v*/).
- **The 12-step pipeline demo is the #1 conversion tool.** Make it prominent, make it interactive.
