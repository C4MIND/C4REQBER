package screens

import (
	"fmt"
	"strings"
	"time"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// HistoryTable shows the last N discoveries in a tabular overlay.
type HistoryTable struct {
	width   int
	height  int
	cursor  int
	records []internal.SessionRecord
	done    bool
}

// NewHistoryTable creates a history overlay with records from the store.
func NewHistoryTable(store *internal.Store) HistoryTable {
	if store == nil {
		return HistoryTable{records: []internal.SessionRecord{}}
	}
	return HistoryTable{records: store.Recent(20)}
}

func (h HistoryTable) Title() string { return "History" }
func (h HistoryTable) Done() bool    { return h.done }

func (h HistoryTable) Init() tea.Cmd { return nil }

func (h HistoryTable) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		h.width = msg.Width
		h.height = msg.Height
		return h, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q":
			h.done = true
			return h, nil
		case "up", "k":
			if h.cursor > 0 {
				h.cursor--
			}
		case "down", "j":
			if h.cursor < len(h.records)-1 {
				h.cursor++
			}
		}
	}
	return h, nil
}

func (h HistoryTable) View() string {
	if h.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Session History")
	sub := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(fmt.Sprintf("%d discoveries", len(h.records)))

	if len(h.records) == 0 {
		content := lipgloss.JoinVertical(lipgloss.Center, title, "", sub, "", "No discoveries yet.")
		return h.centerBox(content)
	}

	// Header
	header := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Yellow).Render(
		fmt.Sprintf("%-40s  %-10s  %-8s  %s", "Topic", "Mode", "Quality", "Time"),
	)

	var rows []string
	for i, r := range h.records {
		style := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground)
		if i == h.cursor {
			style = lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan).Background(styles.ActiveTheme().Border)
		}
		topic := internal.TruncateRunes(r.Topic, 38)
		ago := time.Since(r.Timestamp)
		var timeStr string
		if ago < time.Minute {
			timeStr = "just now"
		} else if ago < time.Hour {
			timeStr = fmt.Sprintf("%dm ago", int(ago.Minutes()))
		} else {
			timeStr = fmt.Sprintf("%dh ago", int(ago.Hours()))
		}
		rows = append(rows, style.Render(
			fmt.Sprintf("%-40s  %-10s  %-8s  %s", topic, r.Mode, r.Quality, timeStr),
		))
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		sub,
		"",
		header,
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Border).Render(strings.Repeat("─", max(0, min(80, h.width-8)))),
		lipgloss.JoinVertical(lipgloss.Left, rows...),
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("↑/↓ to navigate  •  Esc/Q to close"),
	)

	return h.centerBox(content)
}

func (h HistoryTable) centerBox(content string) string {
	box := lipgloss.NewStyle().
		Width(min(86, h.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)
	return lipgloss.Place(
		h.width, h.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
