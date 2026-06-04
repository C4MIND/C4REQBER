package screens

import (
	"fmt"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// TRIZ shows contradiction-based recommendations.
type TRIZ struct {
	width      int
	height     int
	cursor     int
	principles []trizPrinciple
	done       bool
}

type trizPrinciple struct {
	num  int
	name string
	desc string
}

// NewTRIZ creates a TRIZ bridge overlay.
func NewTRIZ() TRIZ {
	return TRIZ{
		principles: []trizPrinciple{
			{1, "Segmentation", "Divide an object into independent parts."},
			{2, "Taking out", "Separate an interfering part or property."},
			{3, "Local quality", "Change an object's structure from uniform to non-uniform."},
			{4, "Asymmetry", "Change the shape of an object from symmetrical to asymmetrical."},
			{5, "Merging", "Bring closer together identical or similar objects."},
			{6, "Universality", "Make a part or object perform multiple functions."},
			{7, "Nested doll", "Place one object inside another."},
			{8, "Anti-weight", "Merge with another object that provides lift."},
			{9, "Preliminary anti-action", "Perform the reverse action beforehand."},
			{10, "Preliminary action", "Perform required changes in advance."},
			{15, "Dynamics", "Make an object or environment adjust to optimal conditions."},
			{25, "Self-service", "Make an object serve itself through auxiliary functions."},
			{35, "Parameter changes", "Change an object's physical state."},
			{40, "Composite materials", "Change from uniform to composite materials."},
		},
	}
}

func (t TRIZ) Title() string { return "TRIZ Bridge" }
func (t TRIZ) Done() bool    { return t.done }

func (t TRIZ) Init() tea.Cmd { return nil }

func (t TRIZ) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		t.width = msg.Width
		t.height = msg.Height
		return t, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q":
			t.done = true
			return t, nil
		case "up", "k":
			if t.cursor > 0 {
				t.cursor--
			}
		case "down", "j":
			if t.cursor < len(t.principles)-1 {
				t.cursor++
			}
		}
	}
	return t, nil
}

func (t TRIZ) View() string {
	if t.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("TRIZ Bridge")
	sub := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("40 Inventive Principles — Select to apply")

	var items []string
	for i, p := range t.principles {
		style := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground)
		num := lipgloss.NewStyle().Width(4).Render(fmt.Sprintf("%d", p.num))
		if i == t.cursor {
			style = lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan).Background(styles.ActiveTheme().Border)
			num = lipgloss.NewStyle().Width(4).Bold(true).Foreground(styles.ActiveTheme().Yellow).Render(fmt.Sprintf("%d", p.num))
		}
		line := num + " " + style.Render(p.name) + "  " + lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(internal.TruncateRunes(p.desc, t.width-30))
		items = append(items, line)
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		sub,
		"",
		lipgloss.JoinVertical(lipgloss.Left, items...),
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("↑/↓ to navigate  •  Esc/Q to close"),
	)

	box := lipgloss.NewStyle().
		Width(min(70, t.width-4)).
		Height(min(24, t.height-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		t.width, t.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
