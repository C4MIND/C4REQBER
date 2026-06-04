package widgets

import (
	"fmt"
	"strings"
	"time"
	"unicode/utf8"

	"c4tui/config"
	"c4tui/internal"
	"c4tui/styles"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	chatCachedVersion uint64
	chatCollapsedBase lipgloss.Style
	chatPrimaryBold   lipgloss.Style
	chatDimItalic     lipgloss.Style
	chatDim           lipgloss.Style
	chatCyan          lipgloss.Style
)

func syncChatStyles() {
	v := styles.ThemeVersion()
	if chatCachedVersion == v {
		return
	}
	chatCachedVersion = v
	chatCollapsedBase = lipgloss.NewStyle().Background(styles.ActiveTheme().PanelBg).Padding(0, 1).Foreground(styles.ActiveTheme().Dim)
	chatPrimaryBold = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Primary).Bold(true)
	chatDimItalic = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)
	chatDim = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	chatCyan = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
}

// Chat is a collapsible log viewport.
type Chat struct {
	Viewport viewport.Model
	Expanded bool
	Lines    []string
	cfg      config.Config
	width    int
	height   int
}

// NewChat creates a chat panel.
func NewChat(cfg config.Config) Chat {
	vp := viewport.New(cfg.Layout.TextAreaWidth, cfg.Layout.ChatCollapsedHeight)
	return Chat{Viewport: vp, Expanded: false, cfg: cfg}
}

// SetSize updates panel dimensions.
func (c *Chat) SetSize(width, height int) {
	c.width = width
	c.height = height
	if width > 4 && height > 4 {
		c.Viewport.Width = width - 4
		c.Viewport.Height = height - 4
	}
}

// Add appends a line and scrolls.
func (c *Chat) Add(line string) {
	const maxLineLen = 2000
	if utf8.RuneCountInString(line) > maxLineLen {
		runes := []rune(line)
		line = string(runes[:maxLineLen]) + "…"
	}
	ts := time.Now().Format("15:04:05")
	styled := c.styleLine(line)
	c.Lines = append(c.Lines, fmt.Sprintf("[%s] %s", ts, styled))
	const maxLines = 1000
	if len(c.Lines) > maxLines {
		c.Lines = c.Lines[len(c.Lines)-maxLines:]
	}
	c.Viewport.SetContent(strings.Join(c.Lines, "\n"))
	c.Viewport.GotoBottom()
}

func (c *Chat) styleLine(line string) string {
	switch {
	case strings.HasPrefix(line, "[err]"):
		return styles.Error().Render(line)
	case strings.HasPrefix(line, "[warn]"):
		return styles.Warning().Render(line)
	case strings.HasPrefix(line, "[pipeline]"):
		return styles.Success().Render(line)
	case strings.HasPrefix(line, "[phase]"):
		return styles.CyanStyle().Render(line)
	case strings.HasPrefix(line, "[c4]"):
		return styles.YellowStyle().Render(line)
	case strings.HasPrefix(line, "[search]"):
		return styles.GreenStyle().Render(line)
	case strings.HasPrefix(line, "[verify]"):
		return styles.MagentaStyle().Render(line)
	default:
		return line
	}
}

// Update delegates to viewport.
func (c Chat) Update(msg tea.Msg) (Chat, tea.Cmd) {
	var cmd tea.Cmd
	c.Viewport, cmd = c.Viewport.Update(msg)
	return c, cmd
}

// View renders chat or minimized bar.
func (c Chat) View(width int) string {
	w := c.width
	if w == 0 {
		w = width
	}

	syncChatStyles()
	collapsedStyle := chatCollapsedBase.Width(w)

	if !c.Expanded {
		return collapsedStyle.Render("💬 [F2] Chat »")
	}
	h := c.height
	if h == 0 {
		h = c.cfg.Layout.ChatExpandedHeight
	}
	content := c.Viewport.View()
	if len(c.Lines) == 0 {
		empty := lipgloss.JoinVertical(lipgloss.Center,
			chatPrimaryBold.Render(internal.T("panel.chat")),
			"",
			chatDimItalic.Render(internal.T("panel.chat.empty")),
			"",
			chatDim.Render("Press ")+chatCyan.Render("F2")+
				chatDim.Render(internal.T("panel.chat.toggle"))+chatCyan.Render("Shift+E")+
				chatDim.Render(internal.T("panel.chat.export")),
		)
		content = empty
	}
	return styles.Panel(w, h).Render(content)
}
