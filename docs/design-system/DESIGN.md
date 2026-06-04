---
name: c4reqber
colors:
  background: "#0F1117"
  foreground: "#FFFFFF"
  surface-1: "#1A1B26"
  surface-2: "#222436"
  surface-3: "#2A2C3E"
  primary: "#4ECDC4"
  primary-glow: "rgba(78,205,196,0.15)"
  secondary: "#FF6B6B"
  accent: "#FFD93D"
  muted: "#6C7086"
  border: "#2E3042"
  success: "#4ADE80"
  warning: "#FBBF24"
  error: "#FF6B6B"
typography:
  display:
    fontFamily: Inter
    fontWeight: 800
    letterSpacing: -0.04em
  heading:
    fontFamily: Inter
    fontWeight: 700
    letterSpacing: -0.02em
  body:
    fontFamily: Inter
    fontWeight: 400
    lineHeight: 1.6
  mono:
    fontFamily: JetBrains Mono
    fontWeight: 500
    letterSpacing: 0
  label-caps:
    fontFamily: Inter
    fontWeight: 600
    fontSize: 0.75rem
    letterSpacing: 0.08em
    textTransform: uppercase
rounded:
  none: 0
  sm: 6px
  md: 10px
  lg: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  "2xl": 48px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    rounded: "{rounded.md}"
    padding: 12px 24px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    rounded: "{rounded.md}"
    padding: 12px 24px
    boxShadow: 0 0 24px "{colors.primary-glow}"
  card:
    backgroundColor: "{colors.surface-1}"
    borderColor: "{colors.border}"
    rounded: "{rounded.md}"
    padding: 24px
  card-hover:
    backgroundColor: "{colors.surface-1}"
    borderColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 24px
  input:
    backgroundColor: "{colors.surface-2}"
    borderColor: "{colors.border}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.sm}"
    padding: 10px 14px
  input-focus:
    backgroundColor: "{colors.surface-2}"
    borderColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    ringColor: "{colors.primary}"
    padding: 10px 14px
---

## Visual Theme & Atmosphere

**"Terminal Luxe" — a dark, computational cockpit with organic warmth.**

c4reqber is a scientific discovery engine. The interface must feel like a high-end research terminal: precise, powerful, and slightly futuristic. The primary teal (`#4ECDC4`) evokes bioluminescence and data visualization. The warm coral secondary (`#FF6B6B`) adds urgency. The gold accent (`#FFD93D`) signals discovery.

**GPU Dashboard (TUI Header):**
The [G] toggle in the TUI header exposes a live GPU dashboard showing all 5 physics engines (Newton, TorchSim, JaxSim, Schr, vast.ai). Engine status uses the success/warning/error colors mapped to active/idle/offline states. The dashboard bar sits below the mascot commentary line in the TUI header. Toggle key is `G`, with visual affordance `[G]` shown in muted text. TUI header layout: version + cube → LLM indicator → mascot line → GPU dashboard bar.

**Design Decision Rules:**
1. **Dark-first, always.** Light mode is a secondary concern. The default experience is the dark cockpit.
2. **Color is earned.** Only interactive elements, data, and discoveries get color. Everything else stays monochrome.
3. **Depth through layering, not shadows.** Three surface elevations (`surface-1/2/3`) create visual stacking without heavy drop-shadows. Save shadows for modals and overlays.
4. **Glow signals importance.** The primary color gets a glow effect on hover states — never on static elements.
5. **Monospace for data, Inter for prose.** JetBrains Mono for code/terminal/data displays. Inter for labels, headings, prose.
6. **Density is context-dependent.** The cockpit (Canvas) is spacious. The terminal is tight. The sidebar is compact. Don't apply the same density everywhere.
7. **Borders are always visible.** Use `border` token everywhere. Transparent borders in light mode are a mistake.

## Colors

| Token | Value | HSL | Role |
|-------|-------|-----|------|
| `background` | `#0F1117` | 240,33%,8% | Deep space — the canvas of cognition |
| `surface-1` | `#1A1B26` | 240,29%,14% | Card bodies, primary panels |
| `surface-2` | `#222436` | 240,24%,18% | Input fields, secondary panels |
| `surface-3` | `#2A2C3E` | 240,20%,22% | Hover states, elevated surfaces |
| `primary` | `#4ECDC4` | 174,57%,55% | **"Bioluminescent Teal"** — main interactive color |
| `secondary` | `#FF6B6B` | 0,100%,71% | **"Alert Coral"** — warnings, deletes, urgency |
| `accent` | `#FFD93D` | 50,100%,71% | **"Discovery Gold"** — highlights, badges, insights |
| `muted` | `#6C7086` | 240,10%,52% | Secondary text, disabled states |
| `border` | `#2E3042` | 240,18%,22% | Always visible borders |
| `success` | `#4ADE80` | 145,63%,49% | Confirmation, passed tests |
| `warning` | `#FBBF24` | 37,91%,55% | Caution states |
| `error` | `#FF6B6B` | 0,100%,71% | Errors, failures |

**Color allocation philosophy:** Teal is hoarded for primary actions and key data. Coral is reserved for destructive actions. Gold appears only at moments of discovery. Everything else stays in the `surface/border/muted` family. Never use primary color for non-interactive text — muted is for text, primary is for action.

### Cyberpunk Neon Noir (Terminal TUI Palette)

True-color ANSI palette used in `terminal_/cyberpunk_theme.py` for the full-screen TUI:

| Token | ANSI | Hex | Role |
|-------|------|-----|------|
| `FG_PRIMARY` | `\033[38;2;0;255;65m` | `#00FF41` | Matrix green — success, idle pulse |
| `FG_SECONDARY` | `\033[38;2;0;212;255m` | `#00D4FF` | Cyber blue — thinking, links |
| `FG_ACCENT` | `\033[38;2;255;184;0m` | `#FFB800` | Amber gold — discoveries, badges |
| `FG_WARNING` | `\033[38;2;255;184;0m` | `#FFB800` | Processing, caution |
| `FG_DANGER` | `\033[38;2;255;42;42m` | `#FF2A2A` | Error, contradiction, anomaly |
| `FG_GHOST` | `\033[38;2;42;42;62m` | `#2A2A3E` | Muted borders, inactive elements |
| `FG_MUTED` | `\033[38;2;120;120;140m` | `#78788C` | Secondary text |
| `BG_DARK` | `\033[48;2;10;10;18m` | `#0A0A12` | Deep background |
| `BG_PANEL` | `\033[48;2;20;20;35m` | `#141423` | Panel background |
| `BORDER` | `\033[38;2;60;60;90m` | `#3C3C5A` | Box borders |

**TUI-specific effects:**
- `BLINK` — thinking state indicator (ANSI 5)
- `BOLD` — headers and badges (ANSI 1)
- `DIM` — ghost text (ANSI 2)
- `REVERSE` — selected items (ANSI 7)
- Gradient builder — smooth color transitions for progress bars and sparklines
- Glow — simulated via alternating colors at 60fps in AnimationEngine

## Typography

| Role | Font | Weight | Size | Line Height | Letter Spacing |
|------|------|--------|------|-------------|-----------------|
| Display (H1) | Inter | 800 | 2rem–3.5rem | 1.1 | -0.04em |
| Heading (H2) | Inter | 700 | 1.25rem–1.75rem | 1.25 | -0.02em |
| Body | Inter | 400 | 0.875rem–1rem | 1.6 | 0 |
| Small / Caption | Inter | 500 | 0.75rem | 1.5 | 0 |
| Label (UPPERCASE) | Inter | 600 | 0.75rem | 1.4 | 0.08em |
| Code / Terminal | JetBrains Mono | 500 | 0.8125rem | 1.6 | 0 |
| Data / Numbers | JetBrains Mono | 600 | 0.875rem–2rem | 1.3 | -0.02em |

**Typography rules:**
- Never use Inter for code blocks, terminal output, or data displays — always JetBrains Mono.
- Uppercase labels use 0.08em letter-spacing — respect this or the UI looks sloppy.
- Line heights are tight for headings (1.1–1.25), comfortable for body (1.6). Don't mix.

## Layout & Spacing

**Spacing scale:**
- `xs` (4px): Icon-to-text gaps, inline separators
- `sm` (8px): Card padding, list item gaps
- `md` (16px): Section padding, component gaps
- `lg` (24px): Page section gaps
- `xl` (32px): Major section boundaries
- `2xl` (48px): Hero sections, page headers

**Layout rules:**
1. Max content width: `max-w-7xl` (1280px) for dashboards, `max-w-4xl` (896px) for forms
2. Sidebar width: 272px collapsed, 320px expanded
3. Terminal height: 40% of viewport when open
4. Widget grid: 4 columns on desktop, 2 on tablet, 1 on mobile
5. Floating elements: always `top-4 left-4 right-4` spacing from viewport edges

## Elevation & Depth

| Level | Token | Usage | Effect |
|-------|-------|-------|--------|
| 0 | `background` | Canvas | Flat, no shadow |
| 1 | `surface-1` | Cards, panels | Subtle `border` only |
| 2 | `surface-2` | Inputs, popovers | `border` + minor darkening |
| 3 | `surface-3` | Hover, tooltips | `border` + `bg-surface-3` |
| Overlay | `backdrop-blur-md` | Modals, dialogs | `bg-black/60` + blur + shadow |

**Rationale:** Shadows in dark themes look muddy. Use surface elevation (lighter backgrounds) instead of shadows for depth. Save shadows only for modals and overlays where the dark backdrop creates natural contrast.

## Shapes

| Token | Value | Usage |
|-------|-------|-------|
| `none` | 0 | Terminal, code blocks, dividers |
| `sm` | 6px | Inputs, tags, badges, small cards |
| `md` | 10px | Cards, buttons, panels, modals |
| `lg` | 16px | Large cards, hero sections |
| `full` | 9999px | Avatars, pills, toggle switches |

## Components (Key Patterns)

### Terminal Widget
- Background: `surface-1`, borderless
- Header: `surface-2` with 3 colored dots (red/yellow/green) + monospace title
- Body: `JetBrains Mono`, text-primary for prompts, text-muted for output, text-primary for highlights
- Width: full container, height: min 300px

### Chat Interface  
- Background: `surface-1`
- Input: `surface-2` with teal focus ring
- Messages: User bubbles `primary/10`, AI bubbles `surface-2`
- Minimum height: 400px (fix current ~200px issue)
- Empty state: "Ask a research question..." prompt

### Widget Grid (Canvas)
- Cards: `surface-1` with `border`
- Drag handle: visible on hover
- Resize: 2x2 minimum, 4x4 maximum grid units
- Empty state: 3 suggested widgets with "Add Widget" button

## Do's and Don'ts

**Do:**
- Use `text-muted-foreground` for secondary text — never `text-gray-400` or raw hex
- Add `cursor-pointer` to all interactive cards, widgets, and buttons
- Use `transition-colors duration-200` for hover states
- Show visual feedback on ALL hoverable elements
- Use the primary glow effect (`shadow-[0_0_24px_rgba(78,205,196,0.15)]`) on hover for primary cards
- Keep borders visible in both dark and light mode

**Don't:**
- Use raw hex colors — always reference CSS custom properties or Tailwind tokens
- Use scale transforms on hover (causes layout shift)
- Mix Inter and monospace in the same text block
- Use emoji as UI icons — use SVG icons (Heroicons/Lucide) instead
- Apply `bg-white/10` in light mode (invisible)
- Skip hover states — every interactive element must have one

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| 320px–768px | Single column, collapsed sidebar, full-width terminal, mobile nav |
| 768px–1024px | 2-column widget grid, collapsible sidebar |
| 1024px+ | Full layout: sidebar + workspace + terminal + right panel |

Rules:
- Sidebar collapses to hamburger below 768px
- Terminal becomes full-screen on mobile
- Widgets stack vertically < 768px
- All touch targets ≥ 44px on mobile

## Agent Prompt Guide

**For AI agents building UI with this design system:**

1. Always use CSS custom properties and Tailwind semantic classes from this document.
2. The primary color is `var(--primary)` or `text-primary`/`bg-primary`/`border-primary` in Tailwind.
3. Never hardcode `#4ECDC4` — use token references.
4. Surface elevation goes: card → popover → tooltip → modal.
5. Border colors: always `var(--border)` / `border-border`.
6. Text hierarchy: `text-foreground` > `text-muted-foreground` > `text-muted`.
7. For hover effects: add `hover:border-primary` + `hover:shadow-[0_0_24px_var(--primary-glow)]` on cards, `hover:bg-surface-3` on inputs.
8. All interactive elements must have `cursor-pointer` and at least one hover visual change.
9. Terminal/code blocks use `font-mono` (JetBrains Mono). Everything else uses `font-sans` (Inter).
10. Empty states show a muted icon + descriptive text. Never show nothing.
