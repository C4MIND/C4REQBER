package styles

import (
	"sync"
	"sync/atomic"

	"github.com/charmbracelet/lipgloss"
)

// Theme holds a complete color palette.
type Theme struct {
	Name       string
	Background lipgloss.Color
	Foreground lipgloss.Color
	Border     lipgloss.Color
	Primary    lipgloss.Color
	Secondary  lipgloss.Color
	Success    lipgloss.Color
	Warning    lipgloss.Color
	Error      lipgloss.Color
	Cyan       lipgloss.Color
	Yellow     lipgloss.Color
	Green      lipgloss.Color
	Purple     lipgloss.Color
	Pink       lipgloss.Color
	Red        lipgloss.Color
	Orange     lipgloss.Color
	Dim        lipgloss.Color
	Highlight  lipgloss.Color
	PanelBg    lipgloss.Color
	CursorBg   lipgloss.Color
}

// Built-in themes.
var (
	DarkTheme = Theme{
		Name:       "dark",
		Background: lipgloss.Color("#0f0f1e"),
		Foreground: lipgloss.Color("#cccccc"),
		Border:     lipgloss.Color("#1a1a2e"),
		Primary:    lipgloss.Color("#5A56E0"),
		Secondary:  lipgloss.Color("#8b5cf6"),
		Success:    lipgloss.Color("#4ADE80"),
		Warning:    lipgloss.Color("#FFD93D"),
		Error:      lipgloss.Color("#FF6B6B"),
		Cyan:       lipgloss.Color("#4ECDC4"),
		Yellow:     lipgloss.Color("#FFD93D"),
		Green:      lipgloss.Color("#4ADE80"),
		Purple:     lipgloss.Color("#8b5cf6"),
		Pink:       lipgloss.Color("#ec4899"),
		Red:        lipgloss.Color("#FF6B6B"),
		Orange:     lipgloss.Color("#f97316"),
		Dim:        lipgloss.Color("#888888"),
		Highlight:  lipgloss.Color("#ffffff"),
		PanelBg:    lipgloss.Color("#0f0f1e"),
		CursorBg:   lipgloss.Color("#1a1a2e"),
	}

	MatrixTheme = Theme{
		Name:       "matrix",
		Background: lipgloss.Color("#000000"),
		Foreground: lipgloss.Color("#00FF41"),
		Border:     lipgloss.Color("#008F11"), // was #003B00 — invisible on black
		Primary:    lipgloss.Color("#00FF41"),
		Secondary:  lipgloss.Color("#00CC33"),
		Success:    lipgloss.Color("#00FF41"),
		Warning:    lipgloss.Color("#FFD93D"),
		Error:      lipgloss.Color("#FF5555"),
		Cyan:       lipgloss.Color("#00FF41"),
		Yellow:     lipgloss.Color("#FFD93D"),
		Green:      lipgloss.Color("#00FF41"),
		Purple:     lipgloss.Color("#00CC33"),
		Pink:       lipgloss.Color("#00FF41"),
		Red:        lipgloss.Color("#FF5555"),
		Orange:     lipgloss.Color("#FFAA00"),
		Dim:        lipgloss.Color("#007A00"), // was #003B00 — too dark
		Highlight:  lipgloss.Color("#AAFFAA"),
		PanelBg:    lipgloss.Color("#001100"),
		CursorBg:   lipgloss.Color("#003B00"),
	}

	PaperTheme = Theme{
		Name:       "paper",
		Background: lipgloss.Color("#FAFAFA"),
		Foreground: lipgloss.Color("#333333"),
		Border:     lipgloss.Color("#DDDDDD"),
		Primary:    lipgloss.Color("#2563EB"),
		Secondary:  lipgloss.Color("#7C3AED"),
		Success:    lipgloss.Color("#16A34A"),
		Warning:    lipgloss.Color("#D97706"),
		Error:      lipgloss.Color("#DC2626"),
		Cyan:       lipgloss.Color("#0891B2"),
		Yellow:     lipgloss.Color("#D97706"),
		Green:      lipgloss.Color("#16A34A"),
		Purple:     lipgloss.Color("#7C3AED"),
		Pink:       lipgloss.Color("#DB2777"),
		Red:        lipgloss.Color("#DC2626"),
		Orange:     lipgloss.Color("#EA580C"),
		Dim:        lipgloss.Color("#9CA3AF"),
		Highlight:  lipgloss.Color("#000000"),
		PanelBg:    lipgloss.Color("#FFFFFF"),
		CursorBg:   lipgloss.Color("#E5E7EB"),
	}

	AllThemes = []Theme{DarkTheme, MatrixTheme, PaperTheme}
)

// activeThemeValue holds the globally applied palette via atomic.Value.
var activeThemeValue atomic.Value

var themeMu sync.RWMutex

func init() {
	activeThemeValue.Store(DarkTheme)
}

// ActiveTheme returns the globally applied palette (lock-free read).
func ActiveTheme() Theme {
	return activeThemeValue.Load().(Theme)
}

// themeVersion increments atomically on every palette change.
// Widgets can cheaply detect theme switches without locking.
var themeVersion uint64

// Convenience color aliases (updated by syncColors).
var (
	Cyan       lipgloss.Color
	Yellow     lipgloss.Color
	Green      lipgloss.Color
	Purple     lipgloss.Color
	Pink       lipgloss.Color
	Red        lipgloss.Color
	Orange     lipgloss.Color
	Dim        lipgloss.Color
	BgDark     lipgloss.Color
	BorderDark lipgloss.Color
)

// Cached styles — rebuilt whenever the theme changes to avoid per-frame allocations.
var (
	panelBase     lipgloss.Style
	successStyle  lipgloss.Style
	errorStyle    lipgloss.Style
	warningStyle  lipgloss.Style
	titleStyle    lipgloss.Style
	subtitleStyle lipgloss.Style
	cyanStyle     lipgloss.Style
	yellowStyle   lipgloss.Style
	greenStyle    lipgloss.Style
	magentaStyle  lipgloss.Style
	borderStyle   lipgloss.Style
	primaryStyle  lipgloss.Style

	// Status bar cached styles
	statusModeBadgeStyle  lipgloss.Style
	statusFocusBadgeStyle lipgloss.Style
	statusPhaseBadgeStyle lipgloss.Style
	statusBindingsStyle   lipgloss.Style
	statusRightInfoStyle  lipgloss.Style
	statusContainerStyle  lipgloss.Style

	// Header cached styles
	researchSuccessStyle lipgloss.Style
	researchProblemStyle lipgloss.Style
	discoveryPulseStyle  lipgloss.Style
)

func init() { syncColors() }

// ThemeVersion returns the current theme generation counter.
func ThemeVersion() uint64 {
	return atomic.LoadUint64(&themeVersion)
}

func syncColorsUnlocked() {
	Cyan = ActiveTheme().Cyan
	Yellow = ActiveTheme().Yellow
	Green = ActiveTheme().Green
	Purple = ActiveTheme().Purple
	Pink = ActiveTheme().Pink
	Red = ActiveTheme().Red
	Orange = ActiveTheme().Orange
	Dim = ActiveTheme().Dim
	BgDark = ActiveTheme().Background
	BorderDark = ActiveTheme().Border

	panelBase = lipgloss.NewStyle().Padding(1).Border(lipgloss.RoundedBorder())
	successStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Success)
	errorStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Error)
	warningStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Warning)
	titleStyle = lipgloss.NewStyle().Bold(true).Foreground(ActiveTheme().Cyan)
	subtitleStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Dim)
	cyanStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Cyan)
	yellowStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Yellow)
	greenStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Green)
	magentaStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Pink)
	borderStyle = lipgloss.NewStyle().BorderForeground(ActiveTheme().Border)
	primaryStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Primary)

	statusModeBadgeStyle = lipgloss.NewStyle().Bold(true).Foreground(ActiveTheme().Background).Background(ActiveTheme().Cyan).Padding(0, 1)
	statusFocusBadgeStyle = lipgloss.NewStyle().Bold(true).Foreground(ActiveTheme().Background).Background(ActiveTheme().Primary).Padding(0, 1)
	statusPhaseBadgeStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Background).Background(ActiveTheme().Yellow).Bold(true).Padding(0, 1)
	statusBindingsStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Dim)
	statusRightInfoStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Dim)
	statusContainerStyle = lipgloss.NewStyle().Background(ActiveTheme().PanelBg)

	researchSuccessStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Success).Italic(true)
	researchProblemStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Red).Italic(true)
	discoveryPulseStyle = lipgloss.NewStyle().Foreground(ActiveTheme().Success).Bold(true)
}

func syncColors() {
	themeMu.Lock()
	defer themeMu.Unlock()
	syncColorsUnlocked()
}

// SetTheme switches the active palette.
func SetTheme(t Theme) {
	themeMu.Lock()
	defer themeMu.Unlock()
	activeThemeValue.Store(t)
	atomic.AddUint64(&themeVersion, 1)
	syncColorsUnlocked()
}

// CycleTheme rotates to the next theme and returns it.
func CycleTheme() Theme {
	themeMu.Lock()
	defer themeMu.Unlock()
	current := ActiveTheme()
	for i, t := range AllThemes {
		if t.Name == current.Name {
			next := AllThemes[(i+1)%len(AllThemes)]
			activeThemeValue.Store(next)
			atomic.AddUint64(&themeVersion, 1)
			syncColorsUnlocked()
			return next
		}
	}
	activeThemeValue.Store(AllThemes[0])
	atomic.AddUint64(&themeVersion, 1)
	syncColorsUnlocked()
	return AllThemes[0]
}

// --- Style helpers using ActiveTheme ---

// Panel is a reusable container style with rounded corners.
// MaxHeight clamps content so the panel never exceeds its allocated cell vertically.
func Panel(width, height int) lipgloss.Style {
	return panelBase.
		Width(width).
		Height(height).
		MaxHeight(height).
		Background(ActiveTheme().PanelBg).
		BorderForeground(ActiveTheme().Border)
}

// Title style.
func Title() lipgloss.Style { return titleStyle }

// Subtitle style.
func Subtitle() lipgloss.Style { return subtitleStyle }

// Success / Warning / Error helpers.
func Success() lipgloss.Style { return successStyle }
func Warning() lipgloss.Style { return warningStyle }
func Error() lipgloss.Style   { return errorStyle }

// Color style helpers for chat lines.
func CyanStyle() lipgloss.Style    { return cyanStyle }
func YellowStyle() lipgloss.Style  { return yellowStyle }
func GreenStyle() lipgloss.Style   { return greenStyle }
func MagentaStyle() lipgloss.Style { return magentaStyle }

// Themed border style for overlays.
func BorderStyle() lipgloss.Style { return borderStyle }

// Themed primary (purple/blue accent).
func PrimaryStyle() lipgloss.Style { return primaryStyle }

// Status bar cached styles.
func StatusModeBadgeStyle() lipgloss.Style  { return statusModeBadgeStyle }
func StatusFocusBadgeStyle() lipgloss.Style { return statusFocusBadgeStyle }
func StatusPhaseBadgeStyle() lipgloss.Style { return statusPhaseBadgeStyle }
func StatusBindingsStyle() lipgloss.Style   { return statusBindingsStyle }
func StatusRightInfoStyle() lipgloss.Style  { return statusRightInfoStyle }
func StatusContainerStyle() lipgloss.Style  { return statusContainerStyle }

// Header cached styles.
func ResearchSuccessStyle() lipgloss.Style { return researchSuccessStyle }
func ResearchProblemStyle() lipgloss.Style { return researchProblemStyle }
func DiscoveryPulseStyle() lipgloss.Style  { return discoveryPulseStyle }
