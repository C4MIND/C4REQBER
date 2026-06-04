# C4REQBER GitSite Improvement Plan

## Audit Summary

| Category | Score | Critical Issues |
|----------|-------|-----------------|
| Design System Compliance | 4/10 | Colors, typography, tokens completely divergent from DESIGN.md |
| Accessibility (a11y) | 5/10 | Missing lang attr, no skip-link, poor focus states, flag-based lang switcher |
| Performance | 6/10 | Inline CSS/JS bloat, no lazy loading, render-blocking animations |
| SEO | 5/10 | No JSON-LD, no OG image, no sitemap, weak structured data |
| Mobile Responsiveness | 6/10 | Single breakpoint, tables overflow without hint, no touch menu |
| UX/Content | 5/10 | No navigation, no TOC, no examples, overwhelming tables, weak CTAs |
| Maintainability | 4/10 | Monolithic inline files, no build system, duplicated demo styles |

**Overall: 5.0/10** — Functional but unprofessional for a project of this caliber.

---

## Phase 1: Design System Alignment (Week 1)

### 1.1 Color Palette Unification
**Current:** Purple/violet (`#7c3aed`) primary contradicts DESIGN.md teal (`#4ECDC4`).
**Action:**
- Replace all `--accent: #7c3aed` with `--primary: #4ECDC4`
- Replace `--cyan: #06d6a0` with `--primary: #4ECDC4`
- Replace `--pink` with `--secondary: #FF6B6B`
- Replace `--amber` with `--accent: #FFD93D`
- Add `--primary-glow: rgba(78,205,196,0.15)`
- Update gradient-text to use `primary → secondary → accent` sequence
- Ensure all feature card hover glows use `--primary-glow`

### 1.2 Typography Alignment
**Current:** Uses `SF Mono`, `Fira Code` instead of mandated `JetBrains Mono`.
**Action:**
- Import `JetBrains Mono` from Google Fonts or serve locally
- Update `--mono` variable to `'JetBrains Mono', 'SF Mono', monospace`
- Apply `font-weight: 500` for mono (per DESIGN.md)
- Ensure `letter-spacing: 0` for mono text
- Verify `Inter` weights match DESIGN.md (400/500/600/700/800)

### 1.3 Border Radius Standardization
**Current:** `12px`, `20px` arbitrary values.
**Action:**
- Replace with DESIGN.md tokens: `sm: 6px`, `md: 10px`, `lg: 16px`
- Cards: `--radius-lg: 16px` (not 20px)
- Buttons/inputs: `--radius: 10px` (not 12px)
- Tags/badges: `6px`

### 1.4 Surface Elevation
**Current:** Uses drop shadows heavily.
**Action:**
- Adopt surface elevation model: `surface-1` (#1A1B26) → `surface-2` (#222436) → `surface-3` (#2A2C3E)
- Remove heavy `box-shadow: 0 20px 60px...` from cards
- Use `border: 1px solid var(--border)` (#2E3042) for all cards
- Apply hover glow (`shadow-[0_0_24px_rgba(78,205,196,0.15)]`) ONLY on interactive elements

---

## Phase 2: Architecture & Maintainability (Week 1-2)

### 2.1 Extract Stylesheets
**Current:** 500+ lines of inline CSS in `index.html`.
**Action:**
- Create `docs/assets/css/c4r.css` — design tokens + reset + utilities
- Create `docs/assets/css/components.css` — cards, buttons, tables, terminal blocks
- Create `docs/assets/css/sections.css` — hero, stats, features, footer
- Create `docs/assets/css/responsive.css` — all media queries
- Use CSS custom properties matching DESIGN.md tokens exactly

### 2.2 Extract JavaScript
**Current:** 700+ lines of inline JS.
**Action:**
- Create `docs/assets/js/i18n.js` — translation system
- Create `docs/assets/js/animations.js` — scroll reveal, mascot, pipeline
- Create `docs/assets/js/utils.js` — copyCode, observers, helpers
- Create `docs/assets/js/demo.js` — interactive demo (merge with existing)

### 2.3 Unify Demo + Main Site
**Current:** Two separate designs (`index.html` vs `demo/index.html`).
**Action:**
- Merge demo.css into main stylesheet
- Move pipeline demo as an embeddable section in main page
- Create shared component library
- Delete duplicate code, maintain single source of truth

### 2.4 Build System (Optional but Recommended)
**Action:**
- Add lightweight build with Vite or Parcel
- Minify CSS/JS for production
- Enable CSS purging for unused styles
- Add `npm run build:site` script

---

## Phase 3: Accessibility (a11y) Overhaul (Week 2)

### 3.1 Semantic HTML Fixes
**Action:**
- Add `lang` attribute to `<html>` server-side (not just JS)
- Add `<a href="#main" class="skip-link">Skip to content</a>`
- Wrap content in `<main id="main">`
- Convert feature cards to `<article>` or `<li>` within `<ul>`
- Add `aria-label` to all icon-only buttons (lang switcher)
- Add `role="table"`, `scope="col"`, `scope="row"` to comparison tables
- Add `<caption>` to all data tables

### 3.2 Focus Management
**Action:**
- Implement `:focus-visible` styles for all interactive elements
- Ensure focus ring uses `--primary` color with 2px offset
- Add `tabindex="0"` to scrollable table containers
- Trap focus in modals/overlays (if added)

### 3.3 Color Contrast
**Action:**
- Verify all text meets WCAG AA (4.5:1 for normal, 3:1 for large)
- `--fg-3: #555570` on `--bg: #0a0a0f` = 3.8:1 → adjust to `#6C7086`
- Ensure `.tag` text has sufficient contrast
- Add `prefers-reduced-motion` media query disabling animations

### 3.4 Language Switcher Redesign
**Action:**
- Replace flag emoji with ISO 639-1 language codes (EN, RU, ZH)
- Flags represent countries, not languages — bad UX for multilingual users
- Use text labels: "English", "Русский", "中文"
- Add `aria-expanded`, `aria-haspopup` if converting to dropdown

---

## Phase 4: UX & Content Improvements (Week 2-3)

### 4.1 Navigation System
**Action:**
- Add sticky top navbar with:
  - Logo + project name
  - Anchor links: Features, Demo, Pipeline, Engines, Pricing, Docs
  - CTA button "Install"
  - Mobile hamburger menu with slide-out drawer
- Add scroll progress indicator at top
- Add "Back to top" floating button (appears after 500px scroll)

### 4.2 Hero Section Redesign
**Action:**
- Reduce title size on mobile (currently `clamp(48px, 8vw, 96px)`)
- Add typed.js or custom typewriter effect for subtitle
- Replace static badge with live GitHub stars badge (shields.io API)
- Add hero video/terminal mockup showing actual CLI output
- Add social proof: "Used by researchers at [logos]"
- Add scroll-down chevron animation

### 4.3 Interactive Demo Integration
**Action:**
- Embed 12-step pipeline demo directly into main page (not separate)
- Add "Try it" section with live terminal simulation
- Show actual output examples from real runs
- Add copy-to-clipboard for all code snippets (already exists, verify working)

### 4.4 Comparison Tables Redesign
**Action:**
- Break monolithic tables into accordion/collapsible sections
- Add filter/search across comparison features
- Highlight C4REQBER column persistently
- Add tooltips explaining each feature
- Consider radar chart visualization for cognitive architecture comparison

### 4.5 Add Missing Content Sections
**Action:**
- **How It Works**: 3-step visual process (Input → C4 Process → Output)
- **Output Examples**: Gallery of generated dissertations, blueprints, code
- **Testimonials**: Quotes from beta users (even 2-3 adds credibility)
- **FAQ**: 5-7 common questions with collapsible answers
- **Trusted By**: University/research institution logos (with permission)
- **Blog/News**: Link to latest discoveries or releases
- **Community**: Discord/Matrix/Forum links, contribution stats

### 4.6 Call-to-Action Strategy
**Action:**
- Add CTA after every major section (not just hero and footer)
- Primary CTA: "pip install c4reqber" (copy on click)
- Secondary CTA: "Read the Docs", "View on GitHub"
- Tertiary CTA: "Try Live Demo" (scrolls to pipeline)
- Add sticky bottom bar on mobile with install command

---

## Phase 5: Performance Optimization (Week 3)

### 5.1 Critical Rendering Path
**Action:**
- Inline critical CSS (above-fold) only
- Defer non-critical CSS with `media="print" onload="this.media='all'"`
- Preload `Inter` and `JetBrains Mono` font files
- Add `font-display: swap` for all fonts

### 5.2 Animation Optimization
**Action:**
- Replace `background-position` grid animation with `transform` (GPU-accelerated)
- Use `will-change: transform` on animated elements
- Reduce orb blur from `80px` to `60px` on mobile
- Disable complex animations when `prefers-reduced-motion: reduce`

### 5.3 Lazy Loading
**Action:**
- Add `loading="lazy"` to all below-fold images (when added)
- Lazy-load demo section JS until visible
- Defer i18n data loading for non-default languages

### 5.4 Asset Optimization
**Action:**
- Convert SVG icons to sprite sheet
- Minify all CSS/JS
- Add brotli/gzip compression via server config
- Cache static assets for 1 year

---

## Phase 6: SEO & Discoverability (Week 3)

### 6.1 Structured Data
**Action:**
- Add JSON-LD `SoftwareApplication` schema
- Add `Organization` schema with logo, url, sameAs links
- Add `FAQPage` schema for FAQ section
- Add `HowTo` schema for quickstart steps
- Include: name, description, applicationCategory, operatingSystem, offers (free)

### 6.2 Meta Tags Enhancement
**Action:**
- Add Open Graph image (1200×630px, brand colors)
- Add Twitter Card summary_large_image
- Add canonical URL tag
- Add theme-color meta for mobile browsers
- Add msapplication-TileColor for Windows

### 6.3 Technical SEO
**Action:**
- Create `docs/sitemap.xml` with all pages
- Create `docs/robots.txt` allowing all, pointing to sitemap
- Add `manifest.json` for PWA capabilities
- Ensure all anchor links are crawlable
- Add breadcrumb structured data

---

## Phase 7: Content Audit & Enhancement (Week 3-4)

### 7.1 Messaging Refinement
**Current:** "Turn any research question into a paradigm-shifting dissertation" — vague.
**Action:**
- Lead with concrete value: "Generate verified research hypotheses in 3 commands"
- Add quantified benefits: "10x faster literature review", "36 simulation engines"
- Use problem-agitation-solution framework in hero

### 7.2 i18n Completeness
**Current:** 7 languages but some translations truncated (Hindi text shows "रण��ीति").
**Action:**
- Fix corrupted Unicode in Hindi translations
- Add French (FR), Spanish (ES), Portuguese (PT) — major research languages
- Extract all strings to JSON files for easier community translation
- Add RTL support verification for Arabic

### 7.3 Visual Assets
**Action:**
- Create hero illustration: C4 cube visualization in brand colors
- Create architecture diagram showing 27-state cube
- Add engine logos grid (with permission/fair use)
- Create OG image template
- Add favicon in multiple sizes (16, 32, 180, 192, 512)

---

## Phase 8: Testing & Validation (Week 4)

### 8.1 Automated Testing
**Action:**
- Add Lighthouse CI to GitHub/GitLab pipeline
- Set budgets: Performance ≥90, Accessibility ≥95, Best Practices ≥95, SEO ≥90
- Add axe-core automated a11y testing
- Add Playwright visual regression tests for key pages

### 8.2 Cross-Browser Testing
**Action:**
- Test on: Chrome, Firefox, Safari, Edge (last 2 versions)
- Test mobile: iOS Safari, Chrome Android
- Verify all animations work without jank

### 8.3 User Testing
**Action:**
- Recruit 3-5 researchers for 15-min usability tests
- Tasks: Install C4REQBER, find pricing, understand C4 architecture
- Measure: time-on-task, error rate, SUS score

---

## Implementation Priority Matrix

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| P0 | Fix DESIGN.md color compliance | Low | High |
| P0 | Add semantic HTML + skip-link | Low | High |
| P0 | Fix lang attribute + a11y labels | Low | High |
| P1 | Extract CSS/JS to files | Medium | High |
| P1 | Add navigation + TOC | Medium | High |
| P1 | Unify demo + main site styles | Medium | High |
| P2 | Add JSON-LD + OG image | Low | Medium |
| P2 | Redesign comparison tables | Medium | High |
| P2 | Add output examples gallery | Medium | High |
| P3 | Performance optimizations | Medium | Medium |
| P3 | Add FAQ + testimonials | Medium | Medium |
| P3 | Lighthouse CI integration | Low | Medium |
| P4 | Build system (Vite) | High | Low |
| P4 | Additional languages | Medium | Low |

---

## Success Metrics

After implementation, target:
- **Lighthouse Score:** 95+ across all categories
- **Design Compliance:** 100% adherence to DESIGN.md tokens
- **Accessibility:** WCAG 2.1 AA compliant
- **Mobile UX:** Smooth navigation, readable tables, tap targets ≥44px
- **SEO:** Top 10 for "cognitive exoskeleton AI research"

---

## Notes

- Keep the mascot — it's distinctive and aligns with TUI personality
- Preserve terminal/code aesthetic — core brand identity
- The 12-step pipeline demo is a key differentiator — make it prominent
- Avoid generic SaaS landing page templates — maintain "research terminal" feel
- All changes must respect AGPL-3.0 licensing visibility
