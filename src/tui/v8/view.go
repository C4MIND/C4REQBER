package main

import (
	"strconv"
	"strings"

	"c4tui/internal"
	"c4tui/styles"
	"github.com/charmbracelet/lipgloss"
)

// phaseFullNames is cached to avoid re-allocating the slice every frame.
var phaseFullNames = []string{"Framing", "Search", "Gaps", "Hyps", "Sim", "Dissertation", "Quality"}

// cached header separator to avoid strings.Repeat on every frame.
var (
	cachedSep      string
	cachedSepW     int
	cachedSepStyle lipgloss.Style
	cachedSepTheme uint64
)

// View composes all widgets into the final screen.
func (m model) View() string {
	if m.Width == 0 || m.Height == 0 {
		return "Loading..."
	}

	// Render active overlay full-screen.
	if m.Overlay != nil {
		return m.Overlay.View()
	}

	l := m.computeLayout()

	// Top: header + separator
	header := m.Header.View(m.Width)
	sep := cachedHeaderSeparator(m.Width)

	// Compose body based on responsive mode
	var body string
	if l.veryNarrow {
		// Single column stack: C4 → Input → Pipeline → Result → Mascot (if any)
		var sections []string
		sections = append(sections, m.C4Grid.View(l.leftW))
		sections = append(sections, m.InputBar.View(l.midW))
		sections = append(sections, m.Pipeline.View(l.midW))
		sections = append(sections, m.Result.View(l.rightW))
		if l.showCube && l.mascotH > 0 {
			sections = append(sections, m.Mascot.View(l.leftW))
		}
		body = lipgloss.JoinVertical(lipgloss.Left, sections...)
	} else if l.narrow {
		// Two-column: left = C4+Mascot, right = Input+Pipeline+Result
		left := lipgloss.JoinVertical(lipgloss.Left,
			m.C4Grid.View(l.leftW),
		)
		if l.showCube && l.mascotH > 0 {
			left = lipgloss.JoinVertical(lipgloss.Left,
				left,
				m.Mascot.View(l.leftW),
			)
		}
		right := lipgloss.JoinVertical(lipgloss.Left,
			m.InputBar.View(l.rightW),
			m.Pipeline.View(l.rightW),
			m.Result.View(l.rightW),
		)
		body = lipgloss.JoinHorizontal(lipgloss.Top, left, right)
	} else {
		// Three-column: left = C4+Mascot, mid = Input+Pipeline, right = Result
		left := lipgloss.JoinVertical(lipgloss.Left,
			m.C4Grid.View(l.leftW),
		)
		if l.showCube && l.mascotH > 0 {
			left = lipgloss.JoinVertical(lipgloss.Left,
				left,
				m.Mascot.View(l.leftW),
			)
		}
		mid := lipgloss.JoinVertical(lipgloss.Left,
			m.InputBar.View(l.midW),
			m.Pipeline.View(l.midW),
		)
		right := m.Result.View(l.rightW)
		body = lipgloss.JoinHorizontal(lipgloss.Top, left, mid, right)
	}

	// Toast — render as floating overlay instead of inline
	toast := m.Toast.View(m.Width)

	// Bottom: help + chat + status bar
	help := m.Help.View(m.Width)
	chat := m.Chat.View(m.Width)
	statusBar := m.renderStatusBar(l)

	// Compose main stack
	stack := []string{header, sep, body}
	if toast != "" {
		stack = append(stack, toast)
	}
	if help != "" {
		stack = append(stack, help)
	}
	if chat != "" {
		stack = append(stack, chat)
	}
	stack = append(stack, statusBar)

	return lipgloss.JoinVertical(lipgloss.Left, stack...)
}

func cachedHeaderSeparator(width int) string {
	if width == cachedSepW {
		return cachedSep
	}
	cachedSepW = width
	if width < 2 {
		cachedSep = ""
		return cachedSep
	}
	v := styles.ThemeVersion()
	if cachedSepTheme != v {
		cachedSepTheme = v
		cachedSepStyle = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Border)
	}
	line := strings.Repeat("─", width)
	cachedSep = cachedSepStyle.Render(line)
	return cachedSep
}

func (m model) renderStatusBar(l layout) string {
	modeBadge := styles.StatusModeBadgeStyle().Render(" " + strings.ToUpper(m.InputBar.Mode) + " ")

	// Focus indicator
	focusLabel := "INPUT"
	if m.InputBar.TextArea.Value() == "" {
		focusLabel = "C4"
	}
	focusBadge := styles.StatusFocusBadgeStyle().Render(" " + focusLabel + " ")

	// Pipeline phase indicator
	var phaseBadge string
	if m.Pipeline.Running {
		for i, s := range m.Pipeline.Statuses {
			if s == "●" {
				label := string('A' + byte(i))
				if m.Width >= 100 {
					label = phaseFullNames[i]
				}
				phaseBadge = styles.StatusPhaseBadgeStyle().Render(label)
				break
			}
		}
	}

	// Adaptive bindings text
	var bindings string
	bindingsStyle := styles.StatusBindingsStyle()
	if l.narrow {
		bindings = bindingsStyle.Render(
			internal.T("status.run") + " " + internal.T("status.palette") + " " + internal.T("status.quit"),
		)
	} else {
		bindings = bindingsStyle.Render(
			"Ctrl+Enter:" + internal.T("status.run") +
				"  Shift+D:" + internal.T("status.dash") +
				"  Shift+P:" + internal.T("status.palette") +
				"  Shift+H:" + internal.T("status.theme") +
				"  Shift+L:" + internal.T("status.lang") +
				"  ?:Help  Q:" + internal.T("status.quit"),
		)
	}

	// Right side: dimensions only when wide enough
	var rightInfo string
	if m.Width >= 70 {
		dims := " " + strconv.Itoa(m.Width) + "x" + strconv.Itoa(m.Height) + " "
		rightInfo = styles.StatusRightInfoStyle().Render(dims)
	}

	var leftParts []string
	leftParts = append(leftParts, modeBadge)
	leftParts = append(leftParts, " ", focusBadge)
	if phaseBadge != "" {
		leftParts = append(leftParts, " ", phaseBadge)
	}
	leftParts = append(leftParts, "  ", bindings)
	left := lipgloss.JoinHorizontal(lipgloss.Left, leftParts...)

	spacerW := m.Width - lipgloss.Width(left) - lipgloss.Width(rightInfo)
	if spacerW < 0 {
		spacerW = 0
	}
	spacer := strings.Repeat(" ", spacerW)

	return styles.StatusContainerStyle().Width(m.Width).Padding(0, 0).
		Render(lipgloss.JoinHorizontal(lipgloss.Left, left, spacer, rightInfo))
}
