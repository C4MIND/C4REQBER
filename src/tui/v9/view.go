package tui

import (
	"fmt"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	zone "github.com/lrstanley/bubblezone/v2"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// init registers bubblezone for the package.
func init() { zone.NewGlobal() }

// View composes the regions.
func (m *model) View() tea.View {
	if m.width == 0 {
		v := tea.NewView("loading…")
		v.AltScreen = true
		return v
	}
	// v9.13.x: ALWAYS-VISIBLE base-layout panel between header and feed
	// (per user design intent). The 7 widgets form a fixed dashboard
	// that doesn't scroll away when discoveries are added.
	parts := []string{m.renderHeader()}
	if bp := m.renderBasePanel(); bp != "" {
		parts = append(parts, bp)
	}
	parts = append(parts, m.renderFeed(), m.renderInput(), m.renderFooter())
	regions := parts
	// v9.13 (§3.3): status bar (1 line, between footer and input).
	// Renders empty string at T0/T1 or when toggled off.
	if bar := m.renderStatusBar(); bar != "" {
		// Insert before the footer (between input and footer)
		regions = append(regions[:3], append([]string{bar}, regions[3:]...)...)
	}
	if m.showTelemetry {
		regions = append(regions, renderTelemetry(m.tel.Get(), m.width, m.llmTier.String(), m.colorProfile.String()))
	}
	body := strings.Join(regions, "\n")
	if m.wizard != nil && m.wizard.Active() {
		body = RenderWizard(m.width, m.height, m.wizard.Step())
	}
	if m.showHelp {
		body = HelpOverlayWith(m.width, m.height, m.keymap)
	}
	if m.dream != nil && m.dream.Active() && !m.showHelp {
		body = m.dream.Render(m.width, m.height)
	}
	// v9.10: settings menu overlay (Ctrl+,)
	if m.settingsVisible {
		rows := m.CurrentSettings()
		body = RenderSettingsMenuWith(rows, m.settingsCursor, m.width, m.height)
	}
	// v9.10: achievement fullscreen overlay
	if m.showAchievementOverlay && !m.showHelp && (m.wizard == nil || !m.wizard.Active()) {
		body = renderAchievementOverlay(m.achievements, m.width, m.height)
	}
	if m.burst.Active() {
		body = overlayRegion(body, m.burst.Render(), 0, 0, m.width)
	}
	// v9.13 (TI-SIM-02): capabilities overlay (Ctrl+Shift+C) — highest priority
	// transient panel. Drawn last so it covers everything else.
	if m.showCapabilities {
		body = capsim.RenderCapabilitiesOverlay(m.width, m.height, m.capsimReport)
	}
	if m.socialVisible {
		body = RenderSocialMenu(
			m.socialDrafts,
			m.socialDraftCursor,
			m.socialActionCursor,
			m.socialOutput,
			m.socialLoading,
			m.width,
			m.height,
		)
	}
	if m.setupVisible {
		body = RenderSetupHub(
			m.setupCategories,
			m.setupKeys,
			m.setupSelectedCategory,
			m.setupInCategory,
			m.setupEditing,
			m.setupCatCursor,
			m.setupKeyCursor,
			m.setupActionCursor,
			m.setupFocusActions,
			m.setupEditEnvName,
			m.setupEditValue,
			m.setupOutput,
			m.setupLoading,
			m.width,
			m.height,
		)
	}
	if m.agendaVisible {
		body = RenderAgendaMenu(
			m.agendaQuestions,
			m.agendaQCursor,
			m.agendaActionCursor,
			m.agendaFocusActions,
			m.agendaOutput,
			m.agendaLoading,
			m.width,
			m.height,
		)
	}
	if m.modelsVisible {
		body = RenderModelsMenu(
			m.modelsPhases,
			m.modelsCouncil,
			m.modelsView,
			m.modelsCursor,
			m.modelsCostTier,
			m.modelsEstCost,
			m.modelsOutput,
			m.modelsLoading,
			m.width,
			m.height,
		)
	}
	// v9.13 (§15): debug overlay (Ctrl+Shift+D) — also high priority
	if m.showDebug {
		body = RenderDebugOverlay(m.CollectDebugSnapshot())
	}
	// v9.13 (§16.2): command palette — drawn last, highest priority
	if m.paletteActive {
		body = RenderCommandPalette(m.paletteQuery, m.paletteMatches, m.paletteFocused, m.width, m.height)
	}
	v := tea.NewView(zone.Scan(body))
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion
	return v
}

func (m *model) renderHeader() string {
	pulse := "●"
	if m.running && m.tick%30 < 15 {
		pulse = "◉"
	}
	// v9.11.3: cache the wall-clock to avoid footer flicker. View()
	// runs at 60fps; without this cache the timestamp changed every
	// render frame, making the whole bottom strip look like it was
	// "прыгает, моргает" (blinking). Now we only refresh the cached
	// string when the second changes.
	now := time.Now()
	sec := now.Second()
	if m.cachedFooterClock == "" || sec != m.lastFooterSecond {
		m.cachedFooterClock = now.Format("15:04:05")
		m.lastFooterSecond = sec
	}
	// v9.12.3: use ASCII-only header to avoid lipgloss.Width() bugs
	// with Unicode characters (⟨⟩🇬🇧 caused gap calc errors, producing
	// overflow lines that the terminal wrapped — "CAREQBER" missing 4,
	// "F(1,1,0)" instead of F⟨1,1,0⟩, duplicated "DeepSeek $0.0000").
	// Simple padding to width via rune length, no lipgloss.Width.
	hdr := fmt.Sprintf(" %s C4REQBER v9  F<1,1,0>  [%s]  DeepSeek  $%.4f  %s",
		pulse, i18n.GetLang(), m.simSpendThisSession, m.cachedFooterClock)
	// v9.12.5: sub-timer when discovery is running
	if m.running && !m.startedAt.IsZero() {
		elapsed := time.Since(m.startedAt).Round(time.Second)
		if elapsed > 0 {
			hdr += fmt.Sprintf(" +%s", elapsed)
		}
	}
	// v9.13 (§11): theme-aware mode pill. The active mode gets a
	// colored box; the inactive ones get a faint outline.
	if m.theme != nil {
		activeMode := string(m.mode)
		// Append "[mode]" colored by the active mode
		hdr = m.theme.StyleBold("highlight").Render("[") +
			m.theme.StyleBold("success").Render(activeMode) +
			m.theme.StyleBold("highlight").Render("]") + " " + hdr
	}
	right := " " + string(m.mode) + " "
	if len(hdr)+len(right) < m.width {
		hdr += strings.Repeat(" ", m.width-len(hdr)-len(right))
	}
	return hdr + right
}

func (m *model) renderFeed() string {
	return m.vp.View()
}

// renderBasePanel renders the ALWAYS-VISIBLE base-layout widget panel
// (7 dashboard widgets: empty placeholder, tip, examples, status,
// shortcuts, modes, achievements). Truncated to basePanelH rows so
// the layout stays fixed regardless of terminal size.
func (m *model) renderBasePanel() string {
	if m.basePanelH <= 0 {
		return ""
	}
	raw := m.renderEmptyWidgets()
	lines := strings.Split(raw, "\n")
	// Truncate to allocated height (or pad with blanks to fill the region).
	if len(lines) > m.basePanelH {
		lines = lines[:m.basePanelH]
	} else if len(lines) < m.basePanelH {
		pad := make([]string, m.basePanelH-len(lines))
		for i := range pad {
			pad[i] = strings.Repeat(" ", m.width)
		}
		lines = append(lines, pad...)
	}
	return strings.Join(lines, "\n")
}

func (m *model) renderInput() string {
	return m.ta.View()
}

func (m *model) renderFooter() string {
	state := "▶ " + i18n.T("footer.ready")
	if m.running {
		state = "⏵ " + i18n.T("footer.running")
	}
	left := " " + state + " "
	// v9.12.5: show current phase in footer when running
	if m.running && m.jobID != "" && len(m.feed) > 0 {
		last := m.feed[len(m.feed)-1]
		if last.Kind == CardPhase && last.Title != "" {
			pct := int(last.Progress * 100)
			left = fmt.Sprintf(" %s [%s %d%%]", state, last.Title, pct)
		}
	}
	// Use the platform-resolved key labels instead of hardcoded "[Enter]"/"[Ctrl+C]".
	right := " [" + m.keymap.Label(ActRun) + "] " + i18n.T("keymap.run") +
		"  [" + m.keymap.Label(ActHelp) + "] " + i18n.T("keymap.help") +
		"  [" + m.keymap.Label(ActQuit) + "] " + i18n.T("keymap.quit") + " "
	if m.toast != "" {
		right = m.toast + "  " + right
	}
	// v9.12.3 + v9.13.x: pad by RUNE counts and slice by runes, never bytes.
	// Mixing `len(line)` (bytes) with `m.width` (rune columns) used to slice
	// mid-UTF-8 when `left` contained multi-byte glyphs (▶⏵), cutting the
	// right portion of the footer (e.g. "letter t missing" on the right edge).
	leftRunes := len([]rune(left))
	rightRunes := len([]rune(right))
	gap := m.width - leftRunes - rightRunes
	if gap < 1 {
		gap = 1
	}
	line := left + strings.Repeat(" ", gap) + right
	runes := []rune(line)
	if len(runes) < m.width {
		runes = append(runes, []rune(strings.Repeat(" ", m.width-len(runes)))...)
	} else if len(runes) > m.width {
		runes = runes[:m.width]
	}
	return string(runes)
}

func (m *model) layout() {
	// v9.13.x: use the new ComputeLayout engine with the always-visible
	// base-layout panel between header and feed (per user design intent).
	baseH := m.computeBasePanelHeight()
	l := ComputeLayout(m.width, m.height, m.showStatusBar, baseH)
	m.vp.SetWidth(l.Feed.W)
	m.vp.SetHeight(l.Feed.H)
	m.ta.SetWidth(l.Input.W)
	m.ta.SetHeight(l.Input.H)
	m.rain.SetSize(l.Feed.W, l.Feed.H)
	m.sparks.SetSize(l.Input.W, l.Input.H)
	m.basePanelH = baseH
}

// computeBasePanelHeight returns the desired height (in rows) of the
// always-visible base-layout widget panel. Adapts to terminal tier:
// small terminals hide the panel to keep the feed usable; large
// terminals show the full 7-widget dashboard.
func (m *model) computeBasePanelHeight() int {
	tierW := m.width
	if tierW < 100 {
		return 0 // T0: hide panel, keep feed
	}
	if tierW < 140 {
		return 16 // T1: compact panel
	}
	if tierW < 200 {
		return 22 // T2: standard panel
	}
	return 28 // T3: full panel
}

// overlayRegion paints overlay over base starting at line fromY.
func overlayRegion(base, overlay string, fromY, toY, width int) string {
	baseLines := strings.Split(base, "\n")
	overLines := strings.Split(overlay, "\n")
	for y := 0; y+fromY < toY && y < len(overLines); y++ {
		target := y + fromY
		if target >= len(baseLines) {
			break
		}
		over := pad(overLines[y], width)
		bs := pad(baseLines[target], width)
		out := make([]byte, len(bs))
		for i := 0; i < len(bs); i++ {
			if i < len(over) && over[i] != ' ' {
				out[i] = over[i]
			} else {
				out[i] = bs[i]
			}
		}
		baseLines[target] = string(out)
	}
	return strings.Join(baseLines, "\n")
}

func pad(s string, w int) string {
	if len(s) >= w {
		return s[:w]
	}
	return s + strings.Repeat(" ", w-len(s))
}

// renderCard formats one card. Cards are wrapped in bubblezone.Mark for mouse clicks.
// Pass verdictChips to render the chip row above the body of a CardHypothesis
// (per D-06). For non-hypothesis cards, pass empty string.
// `focused` adds a thicker border to indicate focus;
// `expanded` renders the full body and adds an expand/collapse hint.
func renderCard(c Card, width int, verdictChips string, focused, expanded bool) string {
	style := lipgloss.NewStyle().Width(width-2).Padding(0, 1)
	border := "│"
	if focused {
		border = "┃" // double-thick border on focus
	}
	if expanded {
		border = "║" // yet another border on expand
	}
	zoneID := fmt.Sprintf("card-%d", c.ID)
	var inner string
	switch c.Kind {
	case CardPhase:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6")).Render("▣ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Body)
		bar := progressBar(c.Progress, 20)
		// v9.11.8: multi-line body gets border per line (was concat with single border).
		bodyLines := strings.Split(body, "\n")
		if len(bodyLines) > 1 {
			for i, l := range bodyLines {
				bodyLines[i] = border + "  " + l
			}
			body = strings.Join(bodyLines, "\n")
			inner = border + " " + title + "  " + bar + "\n" + body
			break
		}
		inner = border + " " + title + "  " + bar + "\n" + border + "  " + body
	case CardHypothesis:
		badge := "  NEW"
		for _, kv := range c.Meta {
			if kv.Key == "restored" && kv.Value == "true" {
				badge = ""
				break
			}
		}
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("2")).Render("✦ " + c.Title + badge)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("↳ "+m.Key+": "+m.Value)
		}
		// D-06: verdict chip row when 1+ sims reference this hypothesis
		if verdictChips != "" {
			meta = "\n" + border + "  " + verdictChips + meta
		}
		inner = border + " " + title + "\n" + border + "  " + body + meta
	case CardPaper:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("📚 " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(m.Key+": "+m.Value)
		}
		inner = border + " " + title + "\n" + border + "  " + body + meta
	case CardCode:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("5")).Render("⚙ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		inner = border + " " + title + "\n" + border + "  " + body
	case CardSimulation:
		// NEW in v9.13 (TI-SIM-01). Status icon + engine + pattern + domain.
		icon := cards.StatusIcon(c.Sim.EngineStatus)
		if icon == "?" {
			icon = "⏣"
		}
		statusColor := "8"
		switch c.Sim.EngineStatus {
		case "available", "success":
			statusColor = "2"
		case "partial", "stub", "slow":
			statusColor = "3"
		case "unavailable", "error", "failed", "skipped":
			statusColor = "1"
		case "budget_exceeded":
			statusColor = "1"
		case "delegated", "delegated_to_cloud":
			statusColor = "6"
		}
		verdictIcon := cards.VerdictIcon(c.Sim.Verdict)
		titleLine := icon + " " + c.Sim.Engine + "  " + verdictIcon + " " + c.Sim.Pattern + "  " + c.Sim.Domain
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color(statusColor)).Render(titleLine)
		// Body — short summary (verdict + key metric + cost)
		verdictText := c.Sim.Verdict
		if verdictText == "" {
			verdictText = c.Sim.EngineStatus
		}
		costStr := fmt.Sprintf("$%.3f", c.Sim.CostUSD)
		body := fmt.Sprintf("verdict: %s · elapsed %dms · %s · %s", verdictText, c.Sim.ElapsedMS, costStr, c.Sim.BackendHost)
		bodyRendered := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(body)
		// Meta — fallback chain (what was tried)
		meta := ""
		for _, t := range c.Sim.PatternsTried {
			row := fmt.Sprintf("  %s %s", t.Engine, t.Status)
			if t.Reason != "" {
				row += " (" + t.Reason + ")"
			}
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(row)
		}
		// Action strip
		acts := cards.ActionsFor(c)
		actStr := ""
		for i, a := range acts {
			if i > 0 {
				actStr += " · "
			}
			actStr += "[" + a.Key + "] " + a.Label
		}
		if actStr != "" {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("↳ "+actStr)
		}
		inner = border + " " + title + "\n" + border + "  " + bodyRendered + meta
	case CardError:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("1")).Render("✗ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("9")).Render(c.Body)
		inner = border + " " + title + "\n" + border + "  " + body
	default:
		title := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		inner = border + " " + title + "\n" + border + "  " + body
	}
	// v9.13 (F-12): if expanded and FullBody is set, append it as
	// additional body lines. Wrap to width. If no FullBody, show a
	// hint that there's nothing more to read.
	if expanded && c.FullBody != "" {
		fb := c.FullBody
		// Word-wrap to width - 4 (border + padding)
		wrap := width - 4
		if wrap < 20 {
			wrap = 20
		}
		wrapped := wordWrap(fb, wrap)
		for _, line := range wrapped {
			inner += "\n" + border + "  " + line
		}
		// Add collapse hint at the end
		hint := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("[Enter or Esc to collapse]")
		inner += "\n" + border + "  " + hint
	}
	return zone.Mark(zoneID, style.Render(inner))
}

// wordWrap wraps s to maxRunes runes per line, breaking on whitespace
// where possible. Pure function.
func wordWrap(s string, maxRunes int) []string {
	if maxRunes <= 0 {
		return []string{s}
	}
	words := strings.Fields(s)
	if len(words) == 0 {
		return nil
	}
	var lines []string
	cur := ""
	for _, w := range words {
		if len(cur) == 0 {
			cur = w
		} else if len([]rune(cur))+1+len([]rune(w)) <= maxRunes {
			cur += " " + w
		} else {
			lines = append(lines, cur)
			cur = w
		}
	}
	if cur != "" {
		lines = append(lines, cur)
	}
	return lines
}

func progressBar(p float64, width int) string {
	if p < 0 {
		p = 0
	}
	if p > 1 {
		p = 1
	}
	filled := int(p * float64(width))
	// v9.12.5: gradient bar — use █▊▋▌▍▎▏ for the boundary cell
	var body string
	if filled >= width {
		body = strings.Repeat("█", width)
	} else if filled <= 0 {
		body = strings.Repeat("░", width)
	} else {
		tail := (p*float64(width) - float64(filled))
		gradient := "░"
		switch {
		case tail > 0.8:
			gradient = "▊"
		case tail > 0.6:
			gradient = "▋"
		case tail > 0.4:
			gradient = "▌"
		case tail > 0.2:
			gradient = "▍"
		default:
			gradient = "▏"
		}
		body = strings.Repeat("█", filled) + gradient + strings.Repeat("░", max(0, width-filled-1))
	}
	return "[" + body + "]"
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
