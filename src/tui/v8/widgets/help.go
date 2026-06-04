package widgets

import (
	"strings"
	"time"

	"c4tui/config"
	"c4tui/styles"
	"github.com/charmbracelet/lipgloss"
)

var (
	helpCachedVersion uint64
	helpCollapsed     lipgloss.Style
	helpCyan          lipgloss.Style
	helpDim           lipgloss.Style
	helpYellow        lipgloss.Style
	helpGreen         lipgloss.Style
)

func syncHelpStyles() {
	v := styles.ThemeVersion()
	if helpCachedVersion == v {
		return
	}
	helpCachedVersion = v
	helpCollapsed = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)
	helpCyan = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
	helpDim = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	helpYellow = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)
	helpGreen = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Green)
}

// Help shows keyboard shortcuts.
type Help struct {
	Visible    bool
	cfg        config.Config
	tipIdx     int
	lastRotate time.Time
}

// NewHelp creates a help widget.
func NewHelp(cfg config.Config) Help {
	return Help{cfg: cfg}
}

// Toggle switches visibility.
func (h *Help) Toggle() {
	h.Visible = !h.Visible
}

var helpTips = []string{
	"Press ? for help, Shift+P for palette",
	"Ctrl+Enter runs the current mode",
	"Tab cycles C4 axes · Arrows navigate",
	"Shift+H cycles themes (dark/matrix/paper)",
	"The cube remembers every discovery...",
	"Z3^3: 27 states · 6 operators",
	"Shift+D opens the dashboard",
	"F2 toggles the chat panel",
}

func (h *Help) currentTip() string {
	if len(helpTips) == 0 {
		return ""
	}
	return helpTips[h.tipIdx%len(helpTips)]
}

// RotateTip advances to the next tip if enough time has passed.
func (h *Help) RotateTip() {
	if time.Since(h.lastRotate) < 8*time.Second {
		return
	}
	h.tipIdx++
	h.lastRotate = time.Now()
}

// View renders the help panel.
func (h Help) View(width int) string {
	syncHelpStyles()

	if !h.Visible {
		return helpCollapsed.Render("[?] " + h.currentTip())
	}

	lines := []string{
		lipgloss.JoinHorizontal(lipgloss.Left,
			helpYellow.Render("Pipeline: "),
			helpCyan.Render("Ctrl+Enter")+helpDim.Render(" run "),
			helpCyan.Render("Ctrl+D")+helpDim.Render(" discover "),
			helpCyan.Render("Ctrl+F")+helpDim.Render(" flash "),
			helpCyan.Render("Ctrl+T")+helpDim.Render(" turbo "),
		),
		lipgloss.JoinHorizontal(lipgloss.Left,
			helpGreen.Render("Tools: "),
			helpCyan.Render("Ctrl+S")+helpDim.Render(" search "),
			helpCyan.Render("Ctrl+V")+helpDim.Render(" verify "),
			helpYellow.Render("Overlays: "),
			helpCyan.Render("Shift+D")+helpDim.Render(" dash "),
			helpCyan.Render("Shift+P")+helpDim.Render(" palette "),
			helpCyan.Render("Shift+E")+helpDim.Render(" export "),
			helpCyan.Render("Shift+H")+helpDim.Render(" theme "),
		),
		lipgloss.JoinHorizontal(lipgloss.Left,
			helpDim.Render("Navigation: "),
			helpCyan.Render("Tab")+helpDim.Render(" axis "),
			helpCyan.Render("Arrows")+helpDim.Render(" move "),
			helpCyan.Render("F2")+helpDim.Render(" chat "),
			helpDim.Render("  Esc cancel  Ctrl+C quit"),
		),
	}
	content := strings.Join(lines, "\n")
	return styles.Panel(width, h.cfg.Layout.HelpHeight).Render(content)
}
