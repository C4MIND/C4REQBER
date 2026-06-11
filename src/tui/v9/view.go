package tui

import (
	"fmt"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	zone "github.com/lrstanley/bubblezone/v2"

	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// init registers bubblezone for the package.
func init() { zone.NewGlobal() }

// View composes the 4 regions.
func (m *model) View() tea.View {
	if m.width == 0 {
		v := tea.NewView("loading…")
		v.AltScreen = true
		return v
	}
	regions := []string{
		m.renderHeader(),
		m.renderFeed(),
		m.renderInput(),
		m.renderFooter(),
	}
	if m.showTelemetry {
		regions = append(regions, renderTelemetry(m.tel.Get(), m.width, m.llmTier.String(), m.colorProfile.String()))
	}
	body := strings.Join(regions, "\n")
	if m.wizard != nil && m.wizard.Active() {
		body = RenderWizard(m.width, m.height)
	}
	if m.showHelp {
		body = HelpOverlay(m.width, m.height)
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
		body = renderAchievementOverlay(*m.achievements, m.width, m.height)
	}
	if m.burst.Active() {
		body = overlayRegion(body, m.burst.Render(), 0, 0, m.width)
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
		pulse, i18n.GetLang(), m.cost, m.cachedFooterClock)
	// v9.12.5: sub-timer when discovery is running
	if m.running && !m.startedAt.IsZero() {
		elapsed := time.Since(m.startedAt).Round(time.Second)
		if elapsed > 0 {
			hdr += fmt.Sprintf(" +%s", elapsed)
		}
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
	// v9.12.3: simple padding to width — lipgloss.Width() miscalculates
	// Unicode characters (▶⏵ etc.) causing overflow and terminal wrap.
	line := left + strings.Repeat(" ", max(1, m.width-len([]rune(left))-len([]rune(right)))) + right
	if len([]rune(line)) < m.width {
		line += strings.Repeat(" ", m.width-len([]rune(line)))
	}
	return line[:min(len(line), m.width)]
}

func (m *model) layout() {
	header, footer, input := 1, 1, 3
	feedH := m.height - header - footer - input
	if feedH < 5 {
		feedH = 5
	}
	m.vp.SetWidth(m.width)
	m.vp.SetHeight(feedH)
	m.ta.SetWidth(m.width)
	m.rain.SetSize(m.width, feedH)
	m.sparks.SetSize(m.width, input)
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
func renderCard(c Card, width int) string {
	style := lipgloss.NewStyle().Width(width-2).Padding(0, 1)
	border := "│"
	zoneID := fmt.Sprintf("card-%d", c.Time.UnixNano())
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
			return zone.Mark(zoneID, style.Render(border+" "+title+"  "+bar+"\n"+body))
		}
		return zone.Mark(zoneID, style.Render(border+" "+title+"  "+bar+"\n"+border+"  "+body))
	case CardHypothesis:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("2")).Render("✦ " + c.Title + "  NEW")
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("↳ "+m.Key+": "+m.Value)
		}
		return zone.Mark(zoneID, style.Render(border+" "+title+"\n"+border+"  "+body+meta))
	case CardPaper:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("📚 " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(m.Key+": "+m.Value)
		}
		return zone.Mark(zoneID, style.Render(border+" "+title+"\n"+border+"  "+body+meta))
	case CardCode:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("5")).Render("⚙ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		return zone.Mark(zoneID, style.Render(border+" "+title+"\n"+border+"  "+body))
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
		case "slow":
			statusColor = "3"
		case "unavailable":
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
		return zone.Mark(zoneID, style.Render(border+" "+title+"\n"+border+"  "+bodyRendered+meta))
	case CardError:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("1")).Render("✗ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("9")).Render(c.Body)
		return zone.Mark(zoneID, style.Render(border+" "+title+"\n"+border+"  "+body))
	default:
		title := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		return zone.Mark(zoneID, style.Render(border+" "+title+"\n"+border+"  "+body))
	}
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
