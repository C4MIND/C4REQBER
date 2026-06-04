package screens

import (
	"strings"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// PaletteAction is what the palette can trigger.
type PaletteAction int

const (
	ActionNone PaletteAction = iota
	ActionDashboard
	ActionExport
	ActionHelp
	ActionHistory
	ActionToggleChat
	ActionToggleHelpWidget
	ActionQuit
	ActionDissertation
	ActionKnowledgeGraph
	ActionMatrixRain
	ActionDiagnostic
	ActionBibliography
	ActionTRIZ
	ActionProvider
	ActionCache
	ActionSocial
	ActionGPU
	ActionPackages
	ActionAgenda
	ActionCycleTheme
	ActionCycleLanguage
)

// PaletteMsg is sent when the user selects a command.
type PaletteMsg struct {
	Action PaletteAction
}

// PaletteItem is a single command in the palette.
type PaletteItem struct {
	Name     string
	Shortcut string
	Action   PaletteAction
}

// Palette is a command picker overlay.
type Palette struct {
	width   int
	height  int
	filter  string
	cursor  int
	items   []PaletteItem
	matched []int
	done    bool
	action  PaletteAction
}

// NewPalette creates a new command palette.
func NewPalette() Palette {
	items := []PaletteItem{
		{"Dashboard", "shift+d", ActionDashboard},
		{"Export Results", "shift+e", ActionExport},
		{"Dissertation", "shift+o", ActionDissertation},
		{"History", "shift+y", ActionHistory},
		{"Knowledge Graph", "shift+k", ActionKnowledgeGraph},
		{"Help", "?", ActionHelp},
		{"Toggle Chat", "f2", ActionToggleChat},
		{"Toggle Help Bar", "?", ActionToggleHelpWidget},
		{"Matrix Rain", "ctrl+m", ActionMatrixRain},
		{"Diagnostic", "shift+x", ActionDiagnostic},
		{"Cycle Theme", "shift+h", ActionCycleTheme},
		{"Cycle Language", "shift+l", ActionCycleLanguage},
		{"Bibliography", "shift+b", ActionBibliography},
		{"TRIZ Bridge", "ctrl+r", ActionTRIZ},
		{"Providers", "shift+v", ActionProvider},
		{"Cache Inspector", "shift+c", ActionCache},
		{"Social Sharing", "shift+n", ActionSocial},
		{"GPU Monitor", "shift+g", ActionGPU},
		{"Packages", "shift+i", ActionPackages},
		{"Agenda", "shift+a", ActionAgenda},
		{"Quit", "ctrl+c", ActionQuit},
	}
	p := Palette{
		items:   items,
		matched: make([]int, len(items)),
	}
	for i := range items {
		p.matched[i] = i
	}
	return p
}

func (p Palette) Title() string         { return "Palette" }
func (p Palette) Done() bool            { return p.done }
func (p Palette) Action() PaletteAction { return p.action }

func (p Palette) Init() tea.Cmd { return nil }

func (p Palette) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		p.width = msg.Width
		p.height = msg.Height
		return p, nil
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyEsc, tea.KeyCtrlC:
			p.done = true
			return p, nil
		case tea.KeyEnter:
			if len(p.matched) > 0 {
				p.action = p.items[p.matched[p.cursor]].Action
				p.done = true
				return p, func() tea.Msg { return PaletteMsg{Action: p.action} }
			}
			return p, nil
		case tea.KeyUp:
			if p.cursor > 0 {
				p.cursor--
			}
		case tea.KeyDown:
			if p.cursor < len(p.matched)-1 {
				p.cursor++
			}
		case tea.KeyBackspace:
			if len(p.filter) > 0 {
				p.filter = p.filter[:len(p.filter)-1]
				p.updateFilter()
			}
		default:
			if msg.Type == tea.KeyRunes {
				p.filter += string(msg.Runes)
				p.updateFilter()
			}
		}
	}
	return p, nil
}

func (p *Palette) updateFilter() {
	p.matched = p.matched[:0]
	p.cursor = 0
	f := strings.ToLower(p.filter)
	for i, item := range p.items {
		if strings.Contains(strings.ToLower(item.Name), f) {
			p.matched = append(p.matched, i)
		}
	}
}

func (p Palette) View() string {
	if p.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Command Palette")

	prompt := "> "
	if p.filter != "" {
		prompt += p.filter
	} else {
		prompt += lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("type to filter...")
	}

	var items []string
	for i, idx := range p.matched {
		item := p.items[idx]
		cursor := "  "
		nameStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground)
		if i == p.cursor {
			cursor = "> "
			nameStyle = lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan)
		}
		shortcut := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("(" + item.Shortcut + ")")
		items = append(items, cursor+nameStyle.Render(item.Name)+"  "+shortcut)
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow).Render(prompt),
		"",
		lipgloss.JoinVertical(lipgloss.Left, items...),
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Enter to run  •  Esc to close"),
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
