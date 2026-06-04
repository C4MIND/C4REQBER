package screens

import (
	"strings"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Help shows a full-screen keyboard reference.
type Help struct {
	width  int
	height int
	done   bool
}

// NewHelp creates a full-screen help overlay.
func NewHelp() Help { return Help{} }

func (h Help) Title() string { return "Help" }
func (h Help) Done() bool    { return h.done }

func (h Help) Init() tea.Cmd { return nil }

func (h Help) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		h.width = msg.Width
		h.height = msg.Height
		return h, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" || msg.String() == "?" {
			h.done = true
			return h, nil
		}
	}
	return h, nil
}

func (h Help) View() string {
	if h.width == 0 {
		return ""
	}

	cyan := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	yellow := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)
	green := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Green)
	pink := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Pink)

	sections := []struct {
		title string
		color lipgloss.Style
		rows  [][2]string
	}{
		{
			title: "Discovery",
			color: yellow,
			rows: [][2]string{
				{"Ctrl+Enter", "Start pipeline with current mode"},
				{"Ctrl+D", "Discover mode (default, 6-phase)"},
				{"Ctrl+F", "Flash mode (quick synthesis)"},
				{"Ctrl+T", "Turbo mode (deep agentic)"},
				{"Ctrl+Shift+T", "TurboFactory (batch)"},
			},
		},
		{
			title: "Tools",
			color: green,
			rows: [][2]string{
				{"Ctrl+S", "Search knowledge base"},
				{"Ctrl+V", "Verify / formal proof"},
			},
		},
		{
			title: "Navigation",
			color: cyan,
			rows: [][2]string{
				{"Tab", "Cycle C4 cognitive axis"},
				{"Arrows", "Move C4 cursor"},
				{"F2", "Toggle chat"},
			},
		},
		{
			title: "Overlays",
			color: pink,
			rows: [][2]string{
				{"Shift+D", "Dashboard"},
				{"Shift+E", "Export picker"},
				{"Shift+P", "Command palette"},
				{"?", "This help screen"},
			},
		},
		{
			title: "Settings",
			color: lipgloss.NewStyle().Foreground(styles.ActiveTheme().Purple),
			rows: [][2]string{
				{"Shift+H", "Cycle theme (dark/matrix/paper)"},
				{"Shift+L", "Cycle language (en/ru/zh/ja/de/ar/hi)"},
			},
		},
		{
			title: "Specialist",
			color: yellow,
			rows: [][2]string{
				{"Shift+O", "Dissertation"},
				{"Shift+Y", "History"},
				{"Shift+K", "Knowledge graph"},
				{"Ctrl+M", "Matrix rain"},
				{"Shift+X", "Diagnostic"},
				{"Shift+B", "Bibliography"},
				{"Ctrl+R", "TRIZ bridge"},
				{"Shift+V", "Providers"},
				{"Shift+C", "Cache"},
				{"Shift+N", "Social"},
				{"Shift+G", "GPU monitor"},
				{"Shift+I", "Packages"},
			},
		},
		{
			title: "System",
			color: dim,
			rows: [][2]string{
				{"Esc", "Cancel / close overlay"},
				{"Ctrl+C / q", "Quit"},
			},
		},
	}

	// Build section blocks
	var leftBlocks []string
	var rightBlocks []string
	for i, sec := range sections {
		var lines []string
		lines = append(lines, sec.color.Bold(true).Render(sec.title))
		lines = append(lines, "")
		for _, row := range sec.rows {
			key := lipgloss.NewStyle().Width(16).Render(row[0])
			lines = append(lines, "  "+cyan.Render(key)+"  "+dim.Render(row[1]))
		}
		block := strings.Join(lines, "\n")
		if i%2 == 0 {
			leftBlocks = append(leftBlocks, block)
		} else {
			rightBlocks = append(rightBlocks, block)
		}
	}

	leftCol := strings.Join(leftBlocks, "\n\n")
	rightCol := strings.Join(rightBlocks, "\n\n")

	body := lipgloss.JoinHorizontal(lipgloss.Top, leftCol, "    ", rightCol)

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("C4REQBER Keyboard Reference"),
		"",
		body,
		"",
		dim.Render("Press Esc, Q, or ? to close"),
	)

	box := lipgloss.NewStyle().
		Width(h.width - 6).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Primary).
		Background(styles.ActiveTheme().PanelBg).
		Render(content)

	return lipgloss.Place(
		h.width, h.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
