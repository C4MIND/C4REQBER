package widgets

import (
	"fmt"
	"strings"
	"time"

	"c4tui/config"
	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// C4State holds metadata for each of the 27 cognitive coordinates.
type C4State struct {
	Name        string
	Description string
}

// cubeColor returns a theme-aware color for a cognitive coordinate.
// Colors are grouped by (time, scale) plane; agency does not affect hue.
func cubeColor(t, s, a int) lipgloss.Color {
	_ = a
	switch {
	case t == 0 && s == 0:
		return styles.ActiveTheme().Cyan
	case t == 0 && s == 1:
		return styles.ActiveTheme().Secondary
	case t == 0 && s == 2:
		return styles.ActiveTheme().Primary
	case t == 1 && s == 0:
		return styles.ActiveTheme().Green
	case t == 1 && s == 1:
		return styles.ActiveTheme().Yellow
	case t == 1 && s == 2:
		return styles.ActiveTheme().Orange
	case t == 2 && s == 0:
		return styles.ActiveTheme().Purple
	case t == 2 && s == 1:
		return styles.ActiveTheme().Pink
	case t == 2 && s == 2:
		return styles.ActiveTheme().Red
	default:
		return styles.ActiveTheme().Dim
	}
}

// cubeStates maps (time, scale, agency) to rich metadata (v7 parity).
var cubeStates = map[[3]int]C4State{
	{0, 0, 0}: {"origin", "Beginning of cognition"},
	{0, 0, 1}: {"observe", "Observation"},
	{0, 0, 2}: {"abstract", "Abstraction"},
	{0, 1, 0}: {"analyze", "Analysis"},
	{0, 1, 1}: {"decompose", "Decomposition"},
	{0, 1, 2}: {"formalize", "Formalization"},
	{0, 2, 0}: {"structure", "Structuring"},
	{0, 2, 1}: {"model", "Modeling"},
	{0, 2, 2}: {"generalize", "Generalization"},
	{1, 0, 0}: {"understand", "Understanding"},
	{1, 0, 1}: {"contextualize", "Contextualization"},
	{1, 0, 2}: {"theorize", "Theorization"},
	{1, 1, 0}: {"synthesize", "Synthesis"},
	{1, 1, 1}: {"integrate", "Integration"},
	{1, 1, 2}: {"meta_analyze", "Meta-analysis"},
	{1, 2, 0}: {"design", "Design"},
	{1, 2, 1}: {"optimize", "Optimization"},
	{1, 2, 2}: {"architect", "Architecture"},
	{2, 0, 0}: {"question", "Doubt"},
	{2, 0, 1}: {"hypothesize", "Hypothesis"},
	{2, 0, 2}: {"abstract_deep", "Deep abstraction"},
	{2, 1, 0}: {"discover", "Discovery"},
	{2, 1, 1}: {"innovate", "Innovation"},
	{2, 1, 2}: {"insight", "Insight"},
	{2, 2, 0}: {"create", "Creation"},
	{2, 2, 1}: {"master", "Mastery"},
	{2, 2, 2}: {"emerge", "Emergence"},
}

var axisWords = [][]string{
	{"Past", "Present", "Future"},
	{"Concrete", "Abstract", "Meta"},
	{"Self", "Other", "System"},
}

// C4Grid represents the 3×3×3 cognitive state cube.
type C4Grid struct {
	State      [3]int // time, scale, agency
	ActiveAxis int    // 0=Time, 1=Scale, 2=Agency
	Path       []string
	PathIdx    int
	cfg        config.Config
	width      int
	height     int
	pulseTick  int // animation frame for active cell pulse

}

// NewC4Grid creates a grid at origin.
func NewC4Grid(cfg config.Config) C4Grid {
	return C4Grid{State: [3]int{1, 1, 0}, cfg: cfg}
}

// Init starts the pulse animation ticker.
func (g C4Grid) Init() tea.Cmd {
	return pulseTickCmd()
}

// SetSize updates panel dimensions.
func (g *C4Grid) SetSize(width, height int) {
	g.width = width
	g.height = height
}

// SetPath sets the C4 navigation path from the backend.
func (g *C4Grid) SetPath(path []string) {
	g.Path = path
	g.PathIdx = 0
	if len(path) > 0 {
		g.parseState(path[0])
	}
}

func (g *C4Grid) parseState(stateStr string) {
	var t, s, a int
	if _, err := fmt.Sscanf(stateStr, "C4State(T=%d, S=%d, A=%d)", &t, &s, &a); err == nil {
		if t >= 0 && t < 3 && s >= 0 && s < 3 && a >= 0 && a < 3 {
			g.State = [3]int{t, s, a}
		}
	}
}

// Update handles key navigation and pulse animation.
func (g C4Grid) Update(msg tea.Msg) (C4Grid, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "tab":
			g.ActiveAxis = (g.ActiveAxis + 1) % 3
		case "left":
			g.move(-1)
		case "right":
			g.move(1)
		case "up":
			g.move(1)
		case "down":
			g.move(-1)
		case "shift+up":
			g.State[2] = (g.State[2] + 1) % 3
		case "shift+down":
			g.State[2] = (g.State[2] + 2) % 3
		}
	case C4PulseTickMsg:
		g.pulseTick++
		return g, pulseTickCmd()
	}
	return g, nil
}

func (g *C4Grid) move(delta int) {
	g.State[g.ActiveAxis] = (g.State[g.ActiveAxis] + delta + 3) % 3
}

// Click advances the current axis by one (wraps around).
func (g *C4Grid) Click() {
	g.move(1)
}

// cellColored returns the styled symbol for a coordinate using pre-created base styles.
func (g C4Grid) cellColored(t, s, a int, activeBase, highlightBase, dimStyle lipgloss.Style) string {
	active := (g.State[0] == t && g.State[1] == s && g.State[2] == a)
	color := cubeColor(t, s, a)

	if active {
		// Pulse animation: cycle through symbols every 8 ticks
		pulseSymbols := []string{"■", "◆", "▲", "◆"}
		sym := pulseSymbols[g.pulseTick%len(pulseSymbols)]
		return activeBase.Foreground(color).Render(sym)
	}
	// Adjacent highlight
	dist := abs(t-g.State[0]) + abs(s-g.State[1]) + abs(a-g.State[2])
	if dist == 1 {
		return highlightBase.Foreground(color).Render("▣")
	}
	return dimStyle.Render("□")
}

// info renders the state info panel (name, description, axes).
func (g C4Grid) info() string {
	st := g.State
	state, ok := cubeStates[st]
	if !ok {
		state = C4State{Name: internal.T("c4.state.unknown"), Description: ""}
	}
	color := cubeColor(st[0], st[1], st[2])

	// Clamp public fields to valid bounds to prevent panics from external mutation.
	t, s, a := st[0], st[1], st[2]
	if t < 0 || t > 2 {
		t = 1
	}
	if s < 0 || s > 2 {
		s = 1
	}
	if a < 0 || a > 2 {
		a = 0
	}
	timeWord := axisWords[0][t]
	scaleWord := axisWords[1][s]
	agencyWord := axisWords[2][a]

	activeAxis := g.ActiveAxis % 3
	if activeAxis < 0 {
		activeAxis += 3
	}
	axes := []string{
		"←→ " + internal.T("c4.axis.time"),
		"↑↓ " + internal.T("c4.axis.scale"),
		"Shift+↑↓ " + internal.T("c4.axis.agency"),
	}

	// Pre-create styles once per call.
	yellowBold := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow).Bold(true)
	dimStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	nameStyle := lipgloss.NewStyle().Foreground(color).Bold(true)
	dimItalic := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)

	axes[activeAxis] = yellowBold.Render(axes[activeAxis])
	for i := range axes {
		if i != activeAxis {
			axes[i] = dimStyle.Render(axes[i])
		}
	}

	nameLine := nameStyle.Render(state.Name)
	descLine := dimItalic.Render(state.Description)
	wordsLine := dimStyle.Render(fmt.Sprintf("%s · %s · %s", timeWord, scaleWord, agencyWord))
	axesLine := strings.Join(axes, "  ·  ")

	return lipgloss.JoinVertical(lipgloss.Left,
		nameLine,
		descLine,
		wordsLine,
		axesLine,
	)
}

// View renders the colored ASCII cube + info panel.
func (g C4Grid) View(width int) string {
	w := g.width
	if w == 0 {
		w = width
	}

	// Pre-create base styles once per frame — cell only calls .Foreground() on them.
	activeBase := lipgloss.NewStyle().Bold(true)
	highlightBase := lipgloss.NewStyle()
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(styles.ActiveTheme().Dim))

	var cubeLines []string
	for a := 2; a >= 0; a-- {
		cubeLines = append(cubeLines, fmt.Sprintf("  (a=%d)  %s %s %s", a,
			g.cellColored(0, 0, a, activeBase, highlightBase, dimStyle),
			g.cellColored(0, 1, a, activeBase, highlightBase, dimStyle),
			g.cellColored(0, 2, a, activeBase, highlightBase, dimStyle)))
		cubeLines = append(cubeLines, fmt.Sprintf("         %s %s %s",
			g.cellColored(1, 0, a, activeBase, highlightBase, dimStyle),
			g.cellColored(1, 1, a, activeBase, highlightBase, dimStyle),
			g.cellColored(1, 2, a, activeBase, highlightBase, dimStyle)))
		cubeLines = append(cubeLines, fmt.Sprintf("         %s %s %s",
			g.cellColored(2, 0, a, activeBase, highlightBase, dimStyle),
			g.cellColored(2, 1, a, activeBase, highlightBase, dimStyle),
			g.cellColored(2, 2, a, activeBase, highlightBase, dimStyle)))
		if a > 0 {
			cubeLines = append(cubeLines, "")
		}
	}

	// Path indicator
	if len(g.Path) > 0 {
		cubeLines = append(cubeLines, "")
		cubeLines = append(cubeLines, lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(
			fmt.Sprintf("path: %d steps", len(g.Path))),
		)
	}

	content := lipgloss.JoinVertical(lipgloss.Left,
		lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("▣ C4 Frame"),
		"",
		strings.Join(cubeLines, "\n"),
		"",
		g.info(),
	)

	return styles.Panel(w, g.height).Render(content)
}

func abs(a int) int {
	if a < 0 {
		return -a
	}
	return a
}

// C4PulseTickMsg triggers the active cell pulse animation.
type C4PulseTickMsg struct{}

func pulseTickCmd() tea.Cmd {
	return tea.Tick(250*time.Millisecond, func(_ time.Time) tea.Msg {
		return C4PulseTickMsg{}
	})
}
