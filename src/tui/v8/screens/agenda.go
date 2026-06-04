package screens

import (
	"fmt"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// AgendaItem is a single research question suggestion.
type AgendaItem struct {
	Title        string
	Score        float64
	CostUSD      float64
	TimeMin      int
	Tractability float64
	Status       string // "pending", "approved", "rejected", "modified"
}

// Agenda shows suggested next research questions.
type Agenda struct {
	width  int
	height int
	items  []AgendaItem
	cursor int
	done   bool
}

// NewAgenda creates an agenda overlay with placeholder/demo items.
func NewAgenda() Agenda {
	return Agenda{
		items: []AgendaItem{
			{
				Title:        "What if sleep deprivation affects decision-making via dopamine depletion?",
				Score:        0.87,
				CostUSD:      2.40,
				TimeMin:      45,
				Tractability: 0.75,
				Status:       "pending",
			},
			{
				Title:        "Can acoustic wave therapy reduce amyloid-beta aggregation in vitro?",
				Score:        0.72,
				CostUSD:      1.80,
				TimeMin:      30,
				Tractability: 0.60,
				Status:       "pending",
			},
			{
				Title:        "Does climate humidity correlate with enzyme kinetics degradation rates?",
				Score:        0.65,
				CostUSD:      0.90,
				TimeMin:      20,
				Tractability: 0.85,
				Status:       "pending",
			},
		},
	}
}

func (a Agenda) Title() string { return "Research Agenda" }
func (a Agenda) Done() bool    { return a.done }

func (a Agenda) Init() tea.Cmd { return nil }

func (a Agenda) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		a.width = msg.Width
		a.height = msg.Height
		return a, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q":
			a.done = true
			return a, nil
		case "up", "k":
			if a.cursor > 0 {
				a.cursor--
			}
			return a, nil
		case "down", "j":
			if a.cursor < len(a.items)-1 {
				a.cursor++
			}
			return a, nil
		case "a":
			if a.cursor < len(a.items) {
				a.items[a.cursor].Status = "approved"
			}
			return a, nil
		case "r":
			if a.cursor < len(a.items) {
				a.items[a.cursor].Status = "rejected"
			}
			return a, nil
		case "m":
			if a.cursor < len(a.items) {
				a.items[a.cursor].Status = "modified"
			}
			return a, nil
		}
	}
	return a, nil
}

func (a Agenda) View() string {
	if a.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(styles.ActiveTheme().Primary).
		Render("Research Agenda")

	subtitle := lipgloss.NewStyle().
		Foreground(styles.ActiveTheme().Dim).
		Render("Suggested next research questions")

	if len(a.items) == 0 {
		content := lipgloss.JoinVertical(
			lipgloss.Center,
			title,
			subtitle,
			"",
			"No questions available.",
		)
		return a.centerBox(content)
	}

	var rows []string
	for i, item := range a.items {
		selected := i == a.cursor
		row := a.renderItem(item, selected)
		rows = append(rows, row)
	}

	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	help := dim.Render("↑/↓ navigate • [a]pprove • [r]eject • [m]odify • [q]uit")

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		subtitle,
		"",
		lipgloss.JoinVertical(lipgloss.Left, rows...),
		"",
		help,
	)

	return a.centerBox(content)
}

func (a Agenda) renderItem(item AgendaItem, selected bool) string {
	width := min(80, a.width-8)
	statusIcon := "○"
	statusColor := styles.ActiveTheme().Dim
	switch item.Status {
	case "approved":
		statusIcon = "✓"
		statusColor = styles.ActiveTheme().Success
	case "rejected":
		statusIcon = "✗"
		statusColor = styles.ActiveTheme().Error
	case "modified":
		statusIcon = "~"
		statusColor = styles.ActiveTheme().Yellow
	}

	numStyle := lipgloss.NewStyle().Foreground(statusColor).Bold(true)
	if selected {
		numStyle = numStyle.Background(styles.ActiveTheme().CursorBg)
	}

	num := numStyle.Render(fmt.Sprintf(" %s ", statusIcon))
	titleStyle := lipgloss.NewStyle().Bold(true).Width(width - 6)
	if selected {
		titleStyle = titleStyle.Foreground(styles.ActiveTheme().Highlight)
	}

	metaStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Width(width - 6)
	meta := fmt.Sprintf(
		"score=%.2f  cost=$%.2f  time=%dm  tractability=%.0f%%",
		item.Score, item.CostUSD, item.TimeMin, item.Tractability*100,
	)

	row := lipgloss.JoinVertical(
		lipgloss.Left,
		fmt.Sprintf("%s %s", num, titleStyle.Render(internal.TruncateRunes(item.Title, width-6))),
		fmt.Sprintf("    %s", metaStyle.Render(meta)),
	)

	if selected {
		return lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(styles.ActiveTheme().Border).
			Width(width).
			Padding(0, 1).
			Render(row)
	}
	return lipgloss.NewStyle().Width(width).Padding(0, 1).Render(row)
}

func (a Agenda) centerBox(content string) string {
	box := lipgloss.NewStyle().
		Width(min(90, a.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)
	return lipgloss.Place(
		a.width, a.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
