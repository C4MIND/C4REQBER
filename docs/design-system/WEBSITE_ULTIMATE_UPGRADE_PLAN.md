# C4REQBER GitSite — Ultimate Upgrade Plan

## Audit Summary (v2)

| Category | Score | Status |
|----------|-------|--------|
| Design System Compliance | 7/10 | Colors/fonts fixed, but visual hierarchy needs work |
| Accessibility (a11y) | 7/10 | Skip-link, focus, semantic HTML added; still needs aria-live, roles |
| Performance | 6/10 | Inline CSS/JS bloat remains; no build system |
| SEO | 6/10 | JSON-LD added; missing OG image, sitemap, canonical |
| Mobile Responsiveness | 7/10 | Basic breakpoints added; needs more testing |
| UX/Content | 5/10 | Missing 15+ key sections; no interactive demo |
| Visual Polish | 6/10 | Tables fixed; cards need elevation rework; animations need refinement |

**Overall: 6.3/10** — functional foundation laid, but content and experience gap is massive.

---

## Part 1: Critical Content Gaps (Must Add)

### 1.1 C4 Cube Visualization — Hero Centerpiece
**Current:** No visual representation of the 27-state C4 topology.
**Action:**
- Create interactive 3×3×3 ASCII/Unicode cube visualization in hero or dedicated section
- Show 27 states labeled (T0-T2, S0-S2, A0-A2 combinations)
- Animate operator transitions (T, S, A) on hover/click
- Show Theorem 11 path visualization (diameter ≤ 3 undirected)
- Add tooltip per state explaining cognitive mode
- Use CSS 3D transforms for cube rotation (no Three.js dependency)
- Reference: `src/tui/cube_navigator.py` for state labels

### 1.2 24 Scientist Paths — Unique Moat
**Current:** Not mentioned anywhere.
**Action:**
- Add dedicated section "24 Scientist Paths" after C4 Architecture
- Show grid of paths: Einstein (T0,S1,A2), Turing (T1,S0,A1), etc.
- Each path = C4 coordinates + domain + example discovery
- Animated path traversal showing state transitions
- This is THE competitive moat (2-4 years to replicate)

### 1.3 How It Works — Visual Pipeline
**Current:** Tables only; no visual journey.
**Action:**
- Replace static phase table with interactive 12-step timeline
- Each step clickable → shows details, example output, time estimate
- Progress indicator showing typical pipeline duration
- Animated flow: A → B → C → D → E → F → G
- Add "Run Demo" button that simulates a discovery in real-time

### 1.4 MCP Server — For AI Agents
**Current:** Mentioned in stats, no detail.
**Action:**
- Dedicated section "Built for AI Agents" with MCP focus
- Show 20 tool cards with icons: c4_solve, c4_search, c4_verify, etc.
- JSON Schema preview snippet
- `blast serve --mcp` command block
- Integration examples: Claude, Cursor, Continue.dev
- Link to MCP_REGISTRY.md

### 1.5 TUI Terminal Experience
**Current:** No visual of the terminal interface.
**Action:**
- Add terminal mockup/screenshot section
- Show ASCII cube, mascot, gradient bars, particles
- Keyboard shortcuts cheat sheet (Tab, A, B, D, T, R, etc.)
- Animated typing effect showing real blast commands
- Night mode toggle preview

### 1.6 Social Publishing — 9 Platforms
**Current:** Not mentioned.
**Action:**
- Section "Publish Everywhere" with platform grid
- arXiv, bioRxiv, Zenodo, Reddit, Discord, Slack, Telegram, Twitter/X, Bluesky
- Show ORCID integration, LaTeX export, BibTeX generation
- Auto-upload workflow diagram

### 1.7 Paradigm Shift Results — Proof of Work
**Current:** Not shown.
**Action:**
- Section "Paradigm Shifts Detected" with real results
- Card 1: Sleep as active maintenance → ALREADY_SHIFTED (100%)
- Card 2: Language horizontal gene transfer → SHIFTED (66.67%)
- Show actual excerpts from generated dissertations
- Link to discovery/batch_v6/ and batch_v7/ exports
- This is PROOF the system works

### 1.8 Security & Code Quality — Trust Signals
**Current:** Badge only, no detail.
**Action:**
- Section "Hardened for Production"
- Security metrics: 0 CRITICAL, 0 HIGH, 55 MEDIUM, 14 LOW resolved
- Code quality: 0 mypy errors, 0 ruff errors, 594 tests
- Audit timeline: Round 1→2→3→4 with counts
- Security features grid: prompt injection hardening, SSRF protection, path traversal guards, LaTeX escaping, nonce delimiters
- License badge (AGPL-3.0) + commercial option

### 1.9 Output Examples Gallery
**Current:** No examples.
**Action:**
- Section "What You Get" with 6 format tabs
- Dissertation: preview of generated LaTeX
- Article: Markdown preview
- Blueprint: specification preview
- Code: Python snippet
- Verification Report: Lean4/Coq proof skeleton
- Whitepaper: architecture document preview

### 1.10 Research Audiences — 6 Domains
**Current:** 5 cards exist but weak.
**Action:**
- Expand to 6 with concrete examples per domain
- Hard Science: show actual simulation (GROMACS run)
- Psychology: show CBT meta-analysis pipeline
- Clinical: show RCT design + ClinicalTrials.gov query
- Climate: show WRF + GBIF integration
- Law: show precedent analysis
- Add domain-specific CLI examples

---

## Part 2: Design & Visual System Upgrades

### 2.1 Color System Refinement
**Current:** Applied DESIGN.md but needs fine-tuning.
**Action:**
- Add `--border: #2E3042` token (currently missing, uses raw rgba)
- Darken hero orbs: opacity .15→.10 for less visual noise
- Add subtle noise texture overlay (CSS `background-image` with SVG noise)
- Implement `::selection` color: `background: var(--primary); color: var(--bg)`
- Code blocks: add syntax highlighting classes (token-keyword, token-string, etc.)

### 2.2 Typography Polish
**Action:**
- Hero title: `letter-spacing: -0.03em` for tighter, more impactful headline
- Section labels: `font-weight: 600; letter-spacing: 0.15em`
- Body text: max-width 65ch for readability
- Feature card titles: `color: var(--fg)` not `#c4b5fd` (inconsistent)
- Terminal blocks: ensure `font-variant-ligatures: none` for code clarity

### 2.3 Spacing & Rhythm
**Action:**
- Implement 8px grid system: all spacing multiples of 8px
- Section padding: 120px desktop, 80px tablet, 60px mobile
- Container max-width: 1200px (current) → consider 1140px for tighter focus
- Card padding: 32px (current) → 28px for better density
- Gap consistency: 20px between cards, 32px between sections

### 2.4 Animation & Motion
**Action:**
- Hero orbs: slower drift (currently static), add `transform: translate()` animation
- Scroll reveal: stagger delay 100ms per card (currently 80ms)
- Feature card hover: `translateY(-4px)` + border glow (keep)
- Stat counters: animate from 0 on scroll-into-view
- Pipeline timeline: auto-play demo on page load (with pause button)
- Mascot: keep 3-frame animation, but add "thinking" state on user scroll

### 2.5 Dark Mode Enhancement
**Action:**
- Add subtle `box-shadow` inset on body for depth
- Card backgrounds: use `surface-1`, `surface-2`, `surface-3` consistently
- Terminal blocks: add left border accent `border-left: 2px solid var(--primary)`
- Table rows: zebra striping with `--bg-2` / `--bg-3` alternation

---

## Part 3: Layout & Component Fixes

### 3.1 Hero Section
**Action:**
- Add typed.js effect for subtitle: "Turn any research question into..."
- Add live GitHub stars badge (shields.io dynamic)
- Add terminal window mockup showing actual blast output
- Secondary CTA: "Read the Docs" → links to ARCHITECTURE_C4R.md
- Add scroll-down chevron with bounce animation
- Hero height: `min-height: 100vh` with `padding-top: 56px` for navbar offset

### 3.2 Navigation
**Action:**
- Add mobile hamburger menu (currently hidden below 768px)
- Mobile menu: slide-out drawer with backdrop blur
- Add active state for current section (highlight in navbar)
- Sticky navbar with hide-on-scroll-down, show-on-scroll-up behavior
- Add "Install" button that copies `pip install c4reqber` to clipboard

### 3.3 Stats Grid (Fixed ✓)
**Status:** 2 rows × 3 columns on desktop, 2 columns on mobile.
**Remaining:**
- Add `counter-up` animation on scroll
- Consider adding sparkline or mini-chart per stat

### 3.4 Feature Cards (First Principles)
**Status:** 2×2 grid fixed.
**Remaining:**
- Replace emoji ❌ with SVG icons (Lucide: `XCircle`, `AlertTriangle`)
- Add "Solution" flip card: front = problem, back = how c4reqber solves it
- Or use accordion: click to reveal solution

### 3.5 Comparison Tables
**Status:** Fixed sticky columns, proper borders.
**Remaining:**
- Add filter buttons: "All", "Cognition", "Verification", "Simulation"
- Highlight c4reqber column persistently with subtle glow
- Add tooltip explaining each feature on hover
- Consider converting to interactive radar chart for C4-META comparison

### 3.6 Pricing Cards
**Action:**
- Add "most popular" badge with subtle pulse
- Show cost breakdown per phase (A-G) on expand
- Add calculator: "I run X pipelines/month → $Y"
- Local tier: emphasize "$0/run" with Apple Silicon badge

### 3.7 FAQ Section (Added ✓)
**Remaining:**
- Add search/filter input for FAQ
- Add "Was this helpful?" thumbs up/down per answer
- Expand to 10 questions covering: installation, GPU, verification, LLM choice, data privacy, citation format, export options, troubleshooting

---

## Part 4: Technical & Performance

### 4.1 Build System
**Action:**
- Add Vite build: `npm init -y && npm install -D vite`
- Extract CSS to `src/styles/` with PostCSS
- Extract JS to `src/scripts/` with ES modules
- Add `npm run build` → outputs to `dist/`
- Add `npm run dev` for local development with HMR
- Keep single-file fallback for GitHub Pages compatibility

### 4.2 Asset Optimization
**Action:**
- Create SVG sprite sheet for all icons (30+ icons)
- Lazy-load below-fold images with `loading="lazy"`
- Preload critical fonts: `Inter` wght@400;600;800, `JetBrains Mono` wght@400;500
- Add `font-display: swap` to all @font-face
- Inline critical CSS for above-fold content

### 4.3 Accessibility (a11y)
**Action:**
- Add `aria-live="polite"` to language switcher output
- Add `role="tablist"` / `role="tab"` for format gallery
- Ensure all tables have `<caption>` elements
- Add `aria-expanded` to FAQ details elements
- Color-blind friendly indicators: don't rely on color alone for win/partial/none
- Test with keyboard-only navigation (Tab, Enter, Space, Arrow keys)
- Add `prefers-contrast: high` media query support

### 4.4 SEO & Meta
**Action:**
- Create Open Graph image (1200×630): C4 cube + project name + tagline
- Add `og:image`, `twitter:image` meta tags
- Create `sitemap.xml` with all sections as anchors
- Create `robots.txt`
- Add canonical URL: `https://c4reqber.org`
- Add `manifest.json` for PWA (theme-color, icons, display: standalone)
- Structured data: add `FAQPage` schema for FAQ section
- Add `BreadcrumbList` schema

### 4.5 Analytics & Monitoring
**Action:**
- Add Plausible or Fathom analytics (privacy-first, no cookies)
- Track: section scroll depth, CTA clicks, language switches, demo plays
- Add `data-track` attributes to all CTAs

---

## Part 5: Content Rewrites

### 5.1 Hero Copy
**Current:** "Turn any research question into a paradigm-shifting dissertation. One command."
**Improved:**
```
The cognitive exoskeleton for AI agents.
27 states. 36 engines. 6 verifiers. One command.
```
Sub: `blast solve "your hypothesis"` → generates verified dissertation with citations

### 5.2 Value Proposition Clarity
**Action:**
- Lead every section with concrete numbers, not abstractions
- "Not an LLM wrapper" → "A cognitive operating system with formal math"
- Replace buzzwords with specifics: "cognitive topology" → "27 discrete states in Z₃³ space"

### 5.3 Social Proof
**Action:**
- Add "Trusted by researchers at" with university logos (with permission)
- Add GitHub activity graph (contributors, commits, stars timeline)
- Add "Used in" section: research labs, indie scientists, AI companies
- Add testimonials (even 2-3 from beta users dramatically increases trust)

### 5.4 i18n Completeness
**Action:**
- Fix corrupted Hindi Unicode (रण��ीति → रणनीति)
- Add French (FR), Spanish (ES), Portuguese (PT), Korean (KO)
- Extract all strings to `locales/en.json`, `locales/ru.json`, etc.
- Add RTL layout verification for Arabic

---

## Part 6: New Sections to Add

| Priority | Section | Why |
|----------|---------|-----|
| P0 | C4 Cube Visualization | Unique differentiator, instant "wow" factor |
| P0 | How It Works (visual pipeline) | Explains the product in 30 seconds |
| P0 | Output Examples Gallery | Shows tangible value |
| P0 | Security & Quality | Trust signals for enterprise users |
| P1 | MCP Server for AI Agents | Growing market, 20 tools is strong |
| P1 | TUI Terminal Demo | Terminal-first identity |
| P1 | 24 Scientist Paths | Unique moat, 2-4yr replication barrier |
| P1 | Paradigm Shift Results | Proof the system actually works |
| P1 | Social Publishing | 9 platforms, no competitor has this |
| P2 | 7 Metamodels | Deep technical credibility |
| P2 | Code Quality Dashboard | Developer trust |
| P2 | Research Audiences (expanded) | Domain-specific landing |
| P2 | Blog/News feed | SEO + community |
| P2 | Community/Discord links | User retention |

---

## Part 7: Mobile-Specific Improvements

### 7.1 Touch Targets
- All interactive elements: min 44×44px
- Navbar links: 48px height on mobile
- FAQ summary: full-width tap target

### 7.2 Mobile Layout
- Hero: stack title → subtitle → CTAs vertically
- Stats: 2 columns (already done)
- Feature cards: single column (already done)
- Tables: horizontal scroll with scroll hint (fade on left edge)
- Pricing: horizontal scroll or stacked cards
- Comparison tables: convert to accordion on mobile

### 7.3 Performance
- Reduce orb blur from 80px to 40px on mobile
- Disable grid animation on mobile (battery)
- Reduce particle count in mascot by 50%
- Use `content-visibility: auto` for below-fold sections

---

## Part 8: A/B Test Candidates

1. **Hero CTA:** "pip install c4reqber" vs "See Demo" vs "Read Docs"
2. **Social proof placement:** Above fold vs after features
3. **Comparison table format:** Table vs radar chart vs accordion
4. **Pricing display:** Per-run vs per-month calculator
5. **Mascot visibility:** Always on vs scroll-reveal

---

## Implementation Roadmap

### Sprint 1 (Week 1): Foundation
- [ ] Extract CSS/JS to files (Vite setup)
- [ ] Add all missing meta tags, OG image, manifest
- [ ] Fix all remaining a11y issues
- [ ] Add mobile hamburger menu
- [ ] Add output examples gallery

### Sprint 2 (Week 2): Content
- [ ] Add C4 Cube visualization section
- [ ] Add "How It Works" interactive pipeline
- [ ] Add Security & Code Quality section
- [ ] Add MCP Server section
- [ ] Expand FAQ to 10 questions

### Sprint 3 (Week 3): Polish
- [ ] Add TUI terminal demo section
- [ ] Add Paradigm Shift Results
- [ ] Add Social Publishing section
- [ ] Add 24 Scientist Paths (or defer to v2)
- [ ] Animation polish (counters, orbs, scroll reveals)

### Sprint 4 (Week 4): Launch
- [ ] Performance audit (Lighthouse 95+)
- [ ] Cross-browser testing (Chrome, Safari, Firefox)
- [ ] Mobile testing (iOS Safari, Chrome Android)
- [ ] SEO audit (structured data, sitemap)
- [ ] Analytics setup

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Lighthouse Performance | ~60 | 95+ |
| Lighthouse Accessibility | ~70 | 95+ |
| Lighthouse Best Practices | ~80 | 95+ |
| Lighthouse SEO | ~60 | 95+ |
| Mobile viewport score | ~50 | 90+ |
| Time to Interactive | ~4s | <2s |
| Bounce rate | — | <40% |
| Scroll depth to Features | — | >80% |
| CTA click rate | — | >5% |

---

## Competitive Benchmarks

Study these for inspiration:
- **Vercel.com** — clean dark mode, terminal aesthetic
- **Linear.app** — subtle animations, premium feel
- **GitHub.com** — social proof, activity graphs
- **Anthropic.com** — scientific credibility, clear hierarchy
- **Supabase.com** — developer-focused, feature grids
- **PostHog.com** — transparent, metrics-forward

---

## Notes

- Preserve terminal/code aesthetic — it's core brand identity
- Mascot stays (already fixed)
- All new sections must respect i18n system
- AGPL-3.0 badge must be visible above fold
- "No data retention · BYOK · Self-hostable" is a key trust message
- The 12-step pipeline demo is the #1 conversion tool — make it prominent
