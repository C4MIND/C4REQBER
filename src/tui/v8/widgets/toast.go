package widgets

import (
	"time"

	"c4tui/styles"
	"github.com/charmbracelet/lipgloss"
)

var (
	toastCachedVersion uint64
	toastSuccess       lipgloss.Style
	toastWarn          lipgloss.Style
	toastError         lipgloss.Style
	toastInfo          lipgloss.Style
)

func syncToastStyles() {
	v := styles.ThemeVersion()
	if toastCachedVersion == v {
		return
	}
	toastCachedVersion = v
	// Rounded, shadow-like toast with padding for premium feel
	toastSuccess = lipgloss.NewStyle().
		Padding(0, 2).
		Background(styles.ActiveTheme().Success).
		Foreground(styles.ActiveTheme().Background).
		Bold(true).
		Align(lipgloss.Right).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Success)
	toastWarn = lipgloss.NewStyle().
		Padding(0, 2).
		Background(styles.ActiveTheme().Yellow).
		Foreground(styles.ActiveTheme().Background).
		Bold(true).
		Align(lipgloss.Right).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Yellow)
	toastError = lipgloss.NewStyle().
		Padding(0, 2).
		Background(styles.ActiveTheme().Red).
		Foreground(styles.ActiveTheme().Background).
		Bold(true).
		Align(lipgloss.Right).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Red)
	toastInfo = lipgloss.NewStyle().
		Padding(0, 2).
		Background(styles.ActiveTheme().Cyan).
		Foreground(styles.ActiveTheme().Background).
		Bold(true).
		Align(lipgloss.Right).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Cyan)
}

// Toast is an ephemeral notification banner.
type Toast struct {
	Message   string
	Kind      string // info, success, warn, error
	ShownAt   time.Time
	expiresAt time.Time
	width     int
}

// NewToast creates an empty toast.
func NewToast() Toast {
	return Toast{}
}

// Show sets a new toast message.
func (t *Toast) Show(msg, kind string) {
	t.Message = msg
	t.Kind = kind
	t.ShownAt = time.Now()
	t.expiresAt = time.Now().Add(3 * time.Second)
}

// Visible returns true if the toast should be rendered.
func (t Toast) Visible() bool {
	return t.Message != "" && time.Now().Before(t.expiresAt)
}

// View renders the toast if active.
func (t Toast) View(width int) string {
	if !t.Visible() {
		return ""
	}
	w := t.width
	if w == 0 {
		w = width
	}
	syncToastStyles()
	var base lipgloss.Style
	switch t.Kind {
	case "success":
		base = toastSuccess
	case "warn":
		base = toastWarn
	case "error":
		base = toastError
	default:
		base = toastInfo
	}
	return base.Width(w).Render(t.Message)
}
