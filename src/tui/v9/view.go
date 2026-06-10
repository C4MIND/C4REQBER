package tui

import (
	"fmt"
	"strings"
	"time"

	"charm.land/lipgloss/v2"
	tea "charm.land/bubbletea/v2"
	zone "github.com/lrstanley/bubblezone/v2"
)

// View composes the 4 regions.
func (m *model) View() tea.View {
	if m.width == 0 {
		v := tea.NewView("loading…")
		v.AltScreen = true
		return v
	}
	body := strings.Join([]string{
		m.renderHeader(),
		m.renderFeed(),
		m.renderInput(),
		m.renderFooter(),
	}, "\n")
	// Overlay effects: matrix rain only in TRUE empty state (no cards, no activity).
	// Once user has any content, rain hides — so real discoveries are never obscured.
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

// overlayRegion paints `overlay` over `base` starting at line `fromY`.
// Both strings are split by \n and overlaid cell by cell (overlay chars replace base if non-space).
func overlayRegion(base, overlay string, fromY, toY, width int) string {
	baseLines := strings.Split(base, "\n")
	overLines := strings.Split(overlay, "\n")
	for y := 0; y+fromY < toY && y < len(overLines); y++ {
		target := y + fromY
		if target >= len(baseLines) {
			break
		}
		over := pad(overLines[y], width)
		base := pad(baseLines[target], width)
		out := make([]byte, len(base))
		for i := 0; i < len(base); i++ {
			if i < len(over) && over[i] != ' ' {
				out[i] = over[i]
			} else {
				out[i] = base[i]
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

func (m *model) renderHeader() string {
	pulse := "●"
	if m.running && m.tick%30 < 15 {
		pulse = "◉"
	}
	left := fmt.Sprintf(" %s C4REQBER v9  F⟨1,1,0⟩  🇬🇧 EN  DeepSeek  $%.4f  %s", pulse, m.cost, time.Now().Format("15:04:05"))
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
	state := "▶ " + T("footer.ready")
	if m.running {
		state = "⏵ " + T("footer.running")
	}
	left := " " + state + " "
	right := " [Enter] " + T("keymap.run") + "  [?] " + T("keymap.help") + "  [Ctrl+C] " + T("keymap.quit") + " "
	if m.toast != "" {
		right = m.toast + "  " + right
	}
	gap := strings.Repeat(" ", max(1, m.width-lipgloss.Width(left)-lipgloss.Width(right)))
	return lipgloss.NewStyle().Width(m.width).Render(left + gap + right)
}

func (m *model) layout() {
	header := 1
	footer := 1
	input := 3
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

func (m *model) refreshView() {
	// (View is recomputed on every Update; no manual refresh needed)
}

// renderCard formats one card. Used by feed.
func renderCard(c Card, width int) string {
	style := lipgloss.NewStyle().Width(width - 2).Padding(0, 1)
	border := "│"
	switch c.Kind {
	case CardPhase:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6")).Render("▣ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Body)
		bar := progressBar(c.Progress, 20)
		return style.Render(border + " " + title + "  " + bar + "\n" + border + "  " + body)
	case CardHypothesis:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("2")).Render("✦ " + c.Title + "  NEW")
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("↳ "+m)
		}
		return style.Render(border + " " + title + "\n" + border + "  " + body + meta)
	case CardPaper:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("📚 " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		meta := ""
		for _, m := range c.Meta {
			meta += "\n" + border + "  " + lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(m)
		}
		return style.Render(border + " " + title + "\n" + border + "  " + body + meta)
	case CardCode:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("5")).Render("⚙ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		return style.Render(border + " " + title + "\n" + border + "  " + body)
	case CardError:
		title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("1")).Render("✗ " + c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("9")).Render(c.Body)
		return style.Render(border + " " + title + "\n" + border + "  " + body)
	default:
		title := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(c.Title)
		body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(c.Body)
		return style.Render(border + " " + title + "\n" + border + "  " + body)
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

var _ = tea.Quit // keep import alive
