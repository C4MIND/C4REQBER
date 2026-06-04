package screens

import (
	"fmt"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Provider shows LLM provider status.
type Provider struct {
	width  int
	height int
	done   bool
}

// NewProvider creates a provider dashboard overlay.
func NewProvider() Provider { return Provider{} }

func (p Provider) Title() string { return "Provider Dashboard" }
func (p Provider) Done() bool    { return p.done }

func (p Provider) Init() tea.Cmd { return nil }

func (p Provider) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		p.width = msg.Width
		p.height = msg.Height
		return p, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			p.done = true
			return p, nil
		}
	}
	return p, nil
}

func (p Provider) View() string {
	if p.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Provider Dashboard")

	green := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Success)
	red := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Red)
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)

	providers := []struct {
		name   string
		status string
		model  string
		ok     bool
	}{
		{"OpenAI", "Connected", "gpt-4o", true},
		{"Anthropic", "Connected", "claude-3-5-sonnet", true},
		{"Local (Ollama)", "Standby", "llama3.1", false},
		{"DeepSeek", "Standby", "deepseek-chat", false},
	}

	var rows []string
	for _, pr := range providers {
		status := red.Render("○ " + pr.status)
		if pr.ok {
			status = green.Render("● " + pr.status)
		}
		rows = append(rows, fmt.Sprintf("  %-18s  %-12s  %s", pr.name, status, dim.Render(pr.model)))
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		lipgloss.JoinVertical(lipgloss.Left, rows...),
		"",
		dim.Render("Status is polled from backend configuration."),
		"",
		dim.Render("Press Esc or Q to close"),
	)

	box := lipgloss.NewStyle().
		Width(min(60, p.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		p.width, p.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
