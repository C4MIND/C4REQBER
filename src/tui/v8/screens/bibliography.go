package screens

import (
	"fmt"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Bibliography shows formatted sources from the current discovery.
type Bibliography struct {
	width   int
	height  int
	sources []map[string]any
	done    bool
}

// NewBibliography creates a bibliography overlay from result sources.
func NewBibliography(result map[string]any) Bibliography {
	var sources []map[string]any
	if papers, ok := result["_papers_list"].([]any); ok {
		for _, p := range papers {
			if pm, ok := p.(map[string]any); ok {
				sources = append(sources, pm)
			}
		}
	}
	return Bibliography{sources: sources}
}

func (b Bibliography) Title() string { return "Bibliography" }
func (b Bibliography) Done() bool    { return b.done }

func (b Bibliography) Init() tea.Cmd { return nil }

func (b Bibliography) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		b.width = msg.Width
		b.height = msg.Height
		return b, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			b.done = true
			return b, nil
		}
	}
	return b, nil
}

func (b Bibliography) View() string {
	if b.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Bibliography")

	if len(b.sources) == 0 {
		content := lipgloss.JoinVertical(lipgloss.Center, title, "", "No sources available.")
		return b.centerBox(content)
	}

	yellow := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)

	var items []string
	for i, s := range b.sources {
		titleStr := fmt.Sprintf("%v", s["title"])
		authorStr := fmt.Sprintf("%v", s["authors"])
		if authorStr == "<nil>" || authorStr == "" {
			authorStr = "Unknown"
		}
		yearStr := fmt.Sprintf("%v", s["year"])
		if yearStr == "<nil>" || yearStr == "0" || yearStr == "" {
			yearStr = "n.d."
		}
		urlStr := fmt.Sprintf("%v", s["url"])
		if urlStr == "<nil>" {
			urlStr = ""
		}

		num := yellow.Render(fmt.Sprintf("[%d]", i+1))
		item := lipgloss.JoinVertical(
			lipgloss.Left,
			fmt.Sprintf("%s %s (%s)", num, titleStr, yearStr),
			dim.Render("    "+internal.TruncateRunes(authorStr, b.width-20)),
		)
		if urlStr != "" && urlStr != "<nil>" {
			item += "\n" + dim.Render("    "+internal.TruncateRunes(urlStr, b.width-20))
		}
		items = append(items, item)
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		lipgloss.JoinVertical(lipgloss.Left, items...),
		"",
		dim.Render("Press Esc or Q to close"),
	)

	return b.centerBox(content)
}

func (b Bibliography) centerBox(content string) string {
	box := lipgloss.NewStyle().
		Width(min(70, b.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)
	return lipgloss.Place(
		b.width, b.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
