package tui

import (
	"fmt"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	zone "github.com/lrstanley/bubblezone/v2"

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
	if rain := m.rain.Render(); rain != "" && !m.burst.Active() && len(m.feed) == 0 {
		body = overlayRegion(body, rain, 1, m.height-4, m.width)
	}
	if m.burst.Active() {
		body = overlayRegion(body, m.burst.Render(), 0, 0, m.width)
	}
	if spark := m.sparks.Render(); spark != "" {
		body = overlayRegion(body, spark, m.height-4, m.height-1, m.width)
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
	left := fmt.Sprintf(" %s C4REQBER v9  F⟨1,1,0⟩  🇬🇧 %s  DeepSeek  $%.4f  %s",
		pulse, i18n.GetLang(), m.cost, m.cachedFooterClock)
	right := " " + string(m.mode) + " "
	gap := strings.Repeat(" ", max(1, m.width-lipgloss.Width(left)-lipgloss.Width(right)))
	return lipgloss.NewStyle().Width(m.width).Render(left + gap + right)
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
	// Use the platform-resolved key labels instead of hardcoded "[Enter]"/"[Ctrl+C]".
	right := " [" + m.keymap.Label(ActRun) + "] " + i18n.T("keymap.run") +
		"  [" + m.keymap.Label(ActHelp) + "] " + i18n.T("keymap.help") +
		"  [" + m.keymap.Label(ActQuit) + "] " + i18n.T("keymap.quit") + " "
	if m.toast != "" {
		right = m.toast + "  " + right
	}
	gap := strings.Repeat(" ", max(1, m.width-lipgloss.Width(left)-lipgloss.Width(right)))
	return lipgloss.NewStyle().Width(m.width).Render(left + gap + right)
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
	style := lipgloss.NewStyle().Width(width - 2).Padding(0, 1)
	border := "│"
	zoneID := fmt.Sprintf("card-%d", c.Time.UnixNano())
	switch c.Kind {
	case CardPhase:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6")).Render("▣ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Body)
		bar := progressBar(c.Progress, 20)
		return zone.Mark(zoneID, style.Render(border + " " + title + "  " + bar + "\n" + border + "  " + body))
	case CardHypothesis:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("2")).Render("✦ " + c.Title + "  NEW")
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("↳ "+m)
		}
		return zone.Mark(zoneID, style.Render(border + " " + title + "\n" + border + "  " + body + meta))
	case CardPaper:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("📚 " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(m)
		}
		return zone.Mark(zoneID, style.Render(border + " " + title + "\n" + border + "  " + body + meta))
	case CardCode:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("5")).Render("⚙ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		return zone.Mark(zoneID, style.Render(border + " " + title + "\n" + border + "  " + body))
	case CardError:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("1")).Render("✗ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("9")).Render(c.Body)
		return zone.Mark(zoneID, style.Render(border + " " + title + "\n" + border + "  " + body))
	default:
		title := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		return zone.Mark(zoneID, style.Render(border + " " + title + "\n" + border + "  " + body))
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
	return "[" + strings.Repeat("█", filled) + strings.Repeat("░", width-filled) + "]"
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
