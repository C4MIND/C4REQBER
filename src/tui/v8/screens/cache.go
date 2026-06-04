package screens

import (
	"fmt"
	"time"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// CacheInspector shows what's in the knowledge cache.
type CacheInspector struct {
	width  int
	height int
	done   bool
}

// NewCacheInspector creates a cache inspector overlay.
func NewCacheInspector() CacheInspector { return CacheInspector{} }

func (c CacheInspector) Title() string { return "Cache Inspector" }
func (c CacheInspector) Done() bool    { return c.done }

func (c CacheInspector) Init() tea.Cmd { return nil }

func (c CacheInspector) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		c.width = msg.Width
		c.height = msg.Height
		return c, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			c.done = true
			return c, nil
		}
	}
	return c, nil
}

func (c CacheInspector) View() string {
	if c.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Cache Inspector")
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	green := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Success)

	items := []string{
		fmt.Sprintf("  Entries:        %s", green.Render("0")),
		fmt.Sprintf("  Memory used:    %s", dim.Render("~0 MB")),
		fmt.Sprintf("  Last flush:     %s", dim.Render(time.Now().Format("15:04:05"))),
		fmt.Sprintf("  Cache policy:   %s", dim.Render("LRU")),
		fmt.Sprintf("  TTL:            %s", dim.Render("1h")),
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		lipgloss.JoinVertical(lipgloss.Left, items...),
		"",
		dim.Render("Cache is empty or backend cache endpoint not configured."),
		"",
		dim.Render("Press Esc or Q to close"),
	)

	box := lipgloss.NewStyle().
		Width(min(50, c.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		c.width, c.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
