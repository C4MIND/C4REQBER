package screens

import (
	"fmt"
	"net/url"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// SocialSharing shows share links for the last discovery.
type SocialSharing struct {
	width   int
	height  int
	topic   string
	quality string
	done    bool
}

// NewSocialSharing creates a social sharing overlay.
func NewSocialSharing(topic, quality string) SocialSharing {
	return SocialSharing{topic: topic, quality: quality}
}

func (s SocialSharing) Title() string { return "Share Discovery" }
func (s SocialSharing) Done() bool    { return s.done }

func (s SocialSharing) Init() tea.Cmd { return nil }

func (s SocialSharing) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		s.width = msg.Width
		s.height = msg.Height
		return s, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			s.done = true
			return s, nil
		}
	}
	return s, nil
}

func (s SocialSharing) View() string {
	if s.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Share Discovery")
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	cyan := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)

	var body string
	if s.topic == "" {
		body = "No discovery to share yet.\nRun a pipeline first!"
	} else {
		text := fmt.Sprintf("🔬 Discovered via C4REQBER: %s (quality: %s)", s.topic, s.quality)
		links := []string{
			"",
			cyan.Render("Telegram"),
			"  https://t.me/share/url?url=" + url.QueryEscape(text),
			"",
			cyan.Render("Mastodon"),
			"  Copy text and post to your instance.",
			"",
			cyan.Render("Discord"),
			"  Copy text to your channel.",
		}
		body = lipgloss.JoinVertical(lipgloss.Left, links...)
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		body,
		"",
		dim.Render("Press Esc or Q to close"),
	)

	box := lipgloss.NewStyle().
		Width(min(60, s.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		s.width, s.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
