package screens

import (
	"fmt"
	"time"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Dashboard shows session statistics.
type Dashboard struct {
	width  int
	height int
	store  *internal.Store
	done   bool
}

// NewDashboard creates a new dashboard overlay.
func NewDashboard(store *internal.Store) Dashboard {
	if store == nil {
		return Dashboard{store: &internal.Store{}}
	}
	return Dashboard{store: store}
}

func (d Dashboard) Title() string { return "Dashboard" }
func (d Dashboard) Done() bool    { return d.done }

func (d Dashboard) Init() tea.Cmd { return nil }

func (d Dashboard) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
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
	}
	return d, nil
}

func (d Dashboard) View() string {
	if d.width == 0 {
		return ""
	}

	recent := d.store.Recent(8)
	elapsed := time.Since(d.store.SessionStart)

	// Title bar
	titleBar := lipgloss.NewStyle().
		Width(d.width - 4).
		Align(lipgloss.Center).
		Bold(true).
		Foreground(styles.ActiveTheme().Yellow).
		Render("═══ Session Dashboard ═══")

	// Stats boxes with sparklines
	stats := lipgloss.JoinHorizontal(
		lipgloss.Top,
		statBox("Discoveries", fmt.Sprintf("%d", d.store.DiscoveriesCount), "", d.width/4),
		statBox("History", fmt.Sprintf("%d", len(d.store.History)), d.miniSpark(recent), d.width/4),
		statBox("Session", fmt.Sprintf("%dm", int(elapsed.Minutes())), "", d.width/4),
		statBox("Quality", d.avgQuality(recent), "", d.width/4),
	)

	// Recent discoveries table
	table := d.renderTable(recent)

	// Status bar
	statusBar := lipgloss.NewStyle().
		Width(d.width - 4).
		Align(lipgloss.Center).
		Foreground(styles.ActiveTheme().Dim).
		Render("[Esc/Q] Close  [↑/↓] Navigate")

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		titleBar,
		"",
		stats,
		"",
		table,
		"",
		statusBar,
	)

	box := lipgloss.NewStyle().
		Width(d.width - 4).
		Padding(1).
		Border(lipgloss.NormalBorder()).
		BorderForeground(styles.ActiveTheme().Primary).
		Render(content)

	return lipgloss.Place(
		d.width, d.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}

func (d Dashboard) miniSpark(recent []internal.SessionRecord) string {
	if len(recent) == 0 {
		return ""
	}
	bars := []rune{'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'}
	var out []rune
	for _, r := range recent {
		idx := 0
		if r.Papers > 0 {
			idx = min(len(bars)-1, r.Papers)
		}
		out = append(out, bars[idx])
	}
	return lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan).Render(string(out))
}

func (d Dashboard) renderTable(recent []internal.SessionRecord) string {
	header := lipgloss.NewStyle().
		Bold(true).
		Foreground(styles.ActiveTheme().Yellow).
		Render(fmt.Sprintf(" %-4s %-30s %-10s %-8s %-10s", "No", "Topic", "Mode", "Quality", "Time"))

	sep := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Border).
		Render("──── ────────────────────────────── ────────── ───────── ──────────")

	var rows []string
	if len(recent) == 0 {
		rows = append(rows, lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(" No discoveries yet. Run one!"))
	} else {
		for i, r := range recent {
			num := fmt.Sprintf("%d", i+1)
			topic := internal.TruncateRunes(r.Topic, 28)
			ago := time.Since(r.Timestamp)
			var timeStr string
			if ago < time.Minute {
				timeStr = "just now"
			} else if ago < time.Hour {
				timeStr = fmt.Sprintf("%dm", int(ago.Minutes()))
			} else {
				timeStr = fmt.Sprintf("%dh", int(ago.Hours()))
			}
			line := fmt.Sprintf(" %-4s %-30s %-10s %-8s %-10s", num, topic, r.Mode, r.Quality, timeStr)
			if i == 0 {
				// Highlight most recent row like the reference
				line = lipgloss.NewStyle().
					Background(styles.ActiveTheme().Primary).
					Foreground(styles.ActiveTheme().Highlight).
					Render(line)
			} else {
				line = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground).Render(line)
			}
			rows = append(rows, line)
		}
	}

	return lipgloss.JoinVertical(
		lipgloss.Left,
		header,
		sep,
		lipgloss.JoinVertical(lipgloss.Left, rows...),
	)
}

func statBox(label, value, spark string, w int) string {
	parts := []string{
		lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Yellow).Render(value),
	}
	if spark != "" {
		parts = append(parts, spark)
	}
	parts = append(parts, lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(label))
	content := lipgloss.JoinVertical(lipgloss.Center, parts...)

	return lipgloss.NewStyle().
		Width(w - 2).
		Padding(1).
		Align(lipgloss.Center).
		Border(lipgloss.NormalBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)
}

func (d Dashboard) avgQuality(recent []internal.SessionRecord) string {
	if len(recent) == 0 {
		return "N/A"
	}
	good := 0
	for _, r := range recent {
		if r.Quality != "" && r.Quality != "N/A" {
			good++
		}
	}
	return fmt.Sprintf("%d/%d", good, len(recent))
}
