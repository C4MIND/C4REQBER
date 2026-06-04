package screens

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Onboarding is a 3-step first-run overlay.
type Onboarding struct {
	width  int
	height int
	step   int
	done   bool
}

// NewOnboarding creates the onboarding flow.
func NewOnboarding() Onboarding {
	return Onboarding{step: 0}
}

// IsFirstRun checks if onboarding has been completed.
func IsFirstRun() bool {
	home, err := os.UserHomeDir()
	if err != nil {
		return true // assume first run if we can't determine home directory
	}
	flag := filepath.Join(home, ".c4reqber", "onboarded")
	_, err = os.Stat(flag)
	return os.IsNotExist(err)
}

// MarkOnboarded writes the onboarded flag.
func MarkOnboarded() error {
	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}
	flag := filepath.Join(home, ".c4reqber", "onboarded")
	if err := os.MkdirAll(filepath.Dir(flag), 0755); err != nil {
		return err
	}
	return os.WriteFile(flag, []byte("1"), 0644)
}

func (o Onboarding) Title() string { return "Onboarding" }
func (o Onboarding) Done() bool    { return o.done }

func (o Onboarding) Init() tea.Cmd { return nil }

func (o Onboarding) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		o.width = msg.Width
		o.height = msg.Height
		return o, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q":
			_ = MarkOnboarded()
			o.done = true
			return o, nil
		case "s":
			// Skip onboarding entirely
			_ = MarkOnboarded()
			o.done = true
			return o, nil
		case "enter", "right", " ":
			o.step++
			if o.step > 2 {
				_ = MarkOnboarded()
				o.done = true
			}
			return o, nil
		case "left":
			if o.step > 0 {
				o.step--
			}
			return o, nil
		}
	}
	return o, nil
}

var onboardingCube = []string{
	"    ╭─────────╮",
	"   ╱         ╱│",
	"  ╱    ▣    ╱ │",
	" ╱         ╱  │",
	"╰─────────╯   │",
	"│    ▣    │   │",
	"│         │  ╱ ",
	"│    ▣    │ ╱  ",
	"╰─────────╯    ",
}

func (o Onboarding) View() string {
	if o.width == 0 {
		return ""
	}

	purple := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary)
	cyan := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
	yellow := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	green := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Green)

	cube := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan).Render(strings.Join(onboardingCube, "\n"))

	var content string
	switch o.step {
	case 0:
		content = lipgloss.JoinVertical(lipgloss.Center,
			cube,
			"",
			purple.Render("Welcome to C4REQBER v8"),
			"",
			yellow.Render("Cognitive Exoskeleton for Research"),
			"",
			dim.Render("Discover, verify, and synthesize knowledge"),
			dim.Render("using AI agents and structured reasoning."),
			"",
			green.Render("●")+" Discover  "+cyan.Render("◆")+" Verify  "+yellow.Render("▲")+" Synthesize",
			"",
			cyan.Render("Press Enter or → to continue"),
			dim.Render("(S to skip)"),
		)
	case 1:
		content = lipgloss.JoinVertical(lipgloss.Center,
			purple.Render("Key Bindings"),
			"",
			lipgloss.JoinHorizontal(lipgloss.Left,
				lipgloss.JoinVertical(lipgloss.Left,
					yellow.Render("Pipeline"),
					"",
					cyan.Render("Ctrl+Enter")+"  Start",
					cyan.Render("Ctrl+D")+"       Discover",
					cyan.Render("Ctrl+F")+"       Flash",
					cyan.Render("Ctrl+T")+"       Turbo",
					"",
					yellow.Render("Navigation"),
					"",
					cyan.Render("Tab")+"          Cycle C4 axis",
					cyan.Render("Arrows")+"       Move cursor",
					cyan.Render("F2")+"           Toggle chat",
				),
				"    ",
				lipgloss.JoinVertical(lipgloss.Left,
					yellow.Render("Overlays"),
					"",
					cyan.Render("Shift+D")+"      Dashboard",
					cyan.Render("Shift+P")+"      Palette",
					cyan.Render("Shift+E")+"      Export",
					cyan.Render("Shift+H")+"      Cycle theme",
					cyan.Render("?")+"            Help",
					"",
					yellow.Render("System"),
					"",
					cyan.Render("Esc")+"          Cancel / close",
					cyan.Render("Ctrl+C / q")+"   Quit",
				),
			),
			"",
			cyan.Render("Press Enter or → to continue"),
			dim.Render("(S to skip)"),
		)
	case 2:
		content = lipgloss.JoinVertical(lipgloss.Center,
			cube,
			"",
			purple.Render("You're Ready!"),
			"",
			yellow.Render("C4REQBER")+" — Your research companion",
			"",
			"Type a research problem and hit "+cyan.Render("Ctrl+Enter")+".",
			"",
			green.Render("The cube will guide your discovery."),
			"",
			cyan.Render("Press Enter to start exploring →"),
			dim.Render("(S to skip)"),
		)
	}

	// Step progress bar
	progressWidth := 30
	filled := int(float64(o.step+1) / 3.0 * float64(progressWidth))
	if filled > progressWidth {
		filled = progressWidth
	}
	var bar strings.Builder
	for i := 0; i < progressWidth; i++ {
		if i < filled {
			bar.WriteRune('█')
		} else {
			bar.WriteRune('░')
		}
	}
	progressBar := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Primary).Render(bar.String()[:filled]) +
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(bar.String()[filled:])
	stepLabel := dim.Render(fmt.Sprintf(" step %d/3 ", o.step+1))
	content += "\n\n" + lipgloss.JoinHorizontal(lipgloss.Center, progressBar, stepLabel)

	boxW := min(70, o.width-4)
	box := lipgloss.NewStyle().
		Width(boxW).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Primary).
		Background(styles.ActiveTheme().PanelBg).
		Render(content)

	return lipgloss.Place(
		o.width, o.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
