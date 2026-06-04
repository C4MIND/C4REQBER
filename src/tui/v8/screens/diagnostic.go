package screens

import (
	"context"
	"fmt"
	"time"

	"c4tui/backend"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Diagnostic runs quick health checks and recommends modes.
type Diagnostic struct {
	width    int
	height   int
	bridge   *backend.Bridge
	tests    []diagTest
	done     bool
	finished bool
}

type diagTest struct {
	name   string
	status string // pass, fail, pending
	detail string
}

// NewDiagnostic creates a diagnostic overlay.
func NewDiagnostic(bridge *backend.Bridge) Diagnostic {
	return Diagnostic{
		bridge: bridge,
		tests: []diagTest{
			{name: "API Reachable", status: "pending"},
			{name: "LLM Responsive", status: "pending"},
			{name: "Search Available", status: "pending"},
			{name: "C4 Navigation", status: "pending"},
		},
	}
}

func (d Diagnostic) Title() string { return "Diagnostic" }
func (d Diagnostic) Done() bool    { return d.done }

func (d Diagnostic) Init() tea.Cmd {
	return tea.Tick(200*time.Millisecond, func(t time.Time) tea.Msg {
		return diagTickMsg{idx: 0}
	})
}

func (d Diagnostic) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		d.width = msg.Width
		d.height = msg.Height
		return d, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			d.done = true
			return d, nil
		}
	case diagTickMsg:
		if msg.idx < len(d.tests) {
			return d, tea.Batch(
				d.runTestCmd(msg.idx),
				tea.Tick(400*time.Millisecond, func(t time.Time) tea.Msg {
					return diagTickMsg{idx: msg.idx + 1}
				}),
			)
		}
		d.finished = true
		return d, nil
	case diagResultMsg:
		if msg.idx >= 0 && msg.idx < len(d.tests) {
			d.tests[msg.idx].status = msg.status
			d.tests[msg.idx].detail = msg.detail
		}
		return d, nil
	}
	return d, nil
}

func (d Diagnostic) runTestCmd(idx int) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		switch idx {
		case 0:
			if d.bridge != nil {
				ok, detail := d.bridge.Health(ctx)
				if ok {
					return diagResultMsg{idx: idx, status: "pass", detail: "200 OK"}
				}
				return diagResultMsg{idx: idx, status: "fail", detail: detail}
			}
			return diagResultMsg{idx: idx, status: "fail", detail: "No bridge"}
		case 1:
			if d.bridge != nil {
				_, err := d.bridge.C4Navigate(ctx, "test")
				if err == nil {
					return diagResultMsg{idx: idx, status: "pass", detail: "LLM responsive"}
				}
				return diagResultMsg{idx: idx, status: "fail", detail: err.Error()}
			}
			return diagResultMsg{idx: idx, status: "fail", detail: "No bridge"}
		case 2:
			if d.bridge != nil {
				_, err := d.bridge.Search(ctx, "test")
				if err == nil {
					return diagResultMsg{idx: idx, status: "pass", detail: "Search available"}
				}
				return diagResultMsg{idx: idx, status: "fail", detail: err.Error()}
			}
			return diagResultMsg{idx: idx, status: "fail", detail: "No bridge"}
		case 3:
			if d.bridge != nil {
				_, err := d.bridge.Verify(ctx, "test", "z3")
				if err == nil {
					return diagResultMsg{idx: idx, status: "pass", detail: "Verify available"}
				}
				return diagResultMsg{idx: idx, status: "fail", detail: err.Error()}
			}
			return diagResultMsg{idx: idx, status: "fail", detail: "No bridge"}
		}
		return diagResultMsg{idx: idx, status: "fail", detail: "unknown test"}
	}
}

func (d Diagnostic) recommendMode() string {
	passes := 0
	for _, t := range d.tests {
		if t.status == "pass" {
			passes++
		}
	}
	switch {
	case passes == 4:
		return "All systems green. Use Turbo mode for deep research."
	case passes >= 2:
		return "Core services up. Standard Discover mode recommended."
	default:
		return "Backend issues detected. Flash mode only. Check API URL."
	}
}

func (d Diagnostic) View() string {
	if d.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("System Diagnostic")
	cyan := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)

	var lines []string
	for _, t := range d.tests {
		var status string
		switch t.status {
		case "pass":
			status = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Success).Render("✓ PASS")
		case "fail":
			status = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Error).Render("✗ FAIL")
		default:
			status = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow).Render("⋯ pending")
		}
		lines = append(lines, fmt.Sprintf("  %-20s  %s  %s", t.name, status, cyan.Render(t.detail)))
	}

	var rec string
	if d.finished {
		rec = lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Yellow).Render("Recommendation: " + d.recommendMode())
	} else {
		rec = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Running checks...")
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		lipgloss.JoinVertical(lipgloss.Left, lines...),
		"",
		rec,
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Press Esc or Q to close"),
	)

	boxW := d.width - 4
	if boxW < 20 {
		boxW = 20
	}
	if boxW > 70 {
		boxW = 70
	}
	box := lipgloss.NewStyle().
		Width(boxW).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		d.width, d.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}

type diagTickMsg struct {
	idx int
}

type diagResultMsg struct {
	idx    int
	status string
	detail string
}
