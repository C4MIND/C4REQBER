package widgets

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unicode/utf8"

	"c4tui/config"
	"c4tui/internal"
	"c4tui/styles"
	"github.com/charmbracelet/bubbles/cursor"
	"github.com/charmbracelet/bubbles/textarea"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// HistoryUpMsg triggers history recall upward.
type HistoryUpMsg struct{}

// HistoryDownMsg triggers history recall downward.
type HistoryDownMsg struct{}

// InputBar contains a styled textarea and mode buttons.
type InputBar struct {
	TextArea      textarea.Model
	Mode          string // discover | flash | turbo | turbofactory | search | verify
	SuggestedMode string
	cfg           config.Config
	history       []string
	historyIdx    int // -1 means current edit
	width         int
	height        int

	// Dropdown for mode autocomplete
	ShowDropdown bool
	DropdownIdx  int
}

// NewInputBar creates an InputBar with a richly styled textarea.
func NewInputBar(cfg config.Config) InputBar {
	ta := textarea.New()
	ta.Placeholder = "Enter research problem..."
	ta.ShowLineNumbers = false
	ta.SetWidth(cfg.Layout.TextAreaWidth)
	ta.SetHeight(cfg.Layout.TextAreaHeight)
	ta.Focus()

	// Style the textarea to match our theme
	primaryColor := lipgloss.Color(styles.ActiveTheme().Primary)
	dimColor := lipgloss.Color(styles.ActiveTheme().Dim)

	// Focused state: no internal border — Panel() will provide the frame
	ta.FocusedStyle.Base = lipgloss.NewStyle().Padding(0, 1)
	ta.FocusedStyle.Text = lipgloss.NewStyle().Foreground(lipgloss.Color(styles.ActiveTheme().Foreground))
	ta.FocusedStyle.Placeholder = lipgloss.NewStyle().Foreground(dimColor).Italic(true)
	ta.FocusedStyle.CursorLine = lipgloss.NewStyle().Background(styles.ActiveTheme().CursorBg)
	ta.FocusedStyle.Prompt = lipgloss.NewStyle().Foreground(primaryColor).Bold(true).SetString("› ")

	// Blurred state: same, no border
	ta.BlurredStyle.Base = lipgloss.NewStyle().Padding(0, 1)
	ta.BlurredStyle.Text = lipgloss.NewStyle().Foreground(dimColor)
	ta.BlurredStyle.Placeholder = lipgloss.NewStyle().Foreground(dimColor).Italic(true)
	ta.BlurredStyle.Prompt = lipgloss.NewStyle().Foreground(dimColor).SetString("› ")

	// Cursor style — static block with primary accent
	ta.Cursor.Style = lipgloss.NewStyle().Foreground(primaryColor).Bold(true)
	ta.Cursor.SetMode(cursor.CursorStatic)

	ib := InputBar{
		TextArea:   ta,
		Mode:       "discover",
		cfg:        cfg,
		history:    []string{},
		historyIdx: -1,
	}
	ib.loadDraft()
	return ib
}

var modePlaceholders = map[string]string{
	"discover":     "✨ " + internal.T("placeholder.discover"),
	"flash":        "⚡ " + internal.T("placeholder.flash"),
	"turbo":        "🔬 " + internal.T("placeholder.turbo"),
	"turbofactory": "📦 " + internal.T("placeholder.turbofactory"),
	"search":       "🔍 " + internal.T("placeholder.search"),
	"verify":       "✓ " + internal.T("placeholder.verify"),
}

var modeList = []string{"discover", "flash", "turbo", "turbofactory", "search", "verify"}

// SetMode updates the mode and textarea placeholder.
func (ib *InputBar) SetMode(mode string) {
	ib.Mode = mode
	if ph, ok := modePlaceholders[mode]; ok {
		ib.TextArea.Placeholder = ph
	}
}

// SetSize updates the textarea dimensions.
func (ib *InputBar) SetSize(width, height int) {
	ib.width = width
	ib.height = height
	if width > 4 {
		ib.TextArea.SetWidth(width - 4) // account for Panel border + padding
	}
	if height >= 6 {
		// Reserve 2 rows for buttons + hint, Panel handles its own border
		ib.TextArea.SetHeight(height - 4)
	} else if height >= 4 {
		ib.TextArea.SetHeight(2)
	}
}

// Update delegates to textarea and handles history navigation.
func (ib InputBar) Update(msg tea.Msg) (InputBar, tea.Cmd) {
	switch msg := msg.(type) {
	case HistoryUpMsg:
		ib.HistoryUp()
		return ib, nil
	case HistoryDownMsg:
		ib.HistoryDown()
		return ib, nil
	case tea.KeyMsg:
		if ib.ShowDropdown {
			switch msg.String() {
			case "up":
				if ib.DropdownIdx > 0 {
					ib.DropdownIdx--
				}
				return ib, nil
			case "down":
				if ib.DropdownIdx < len(modeList)-1 {
					ib.DropdownIdx++
				}
				return ib, nil
			case "enter", "tab":
				// Select current dropdown item as mode
				ib.SetMode(modeList[ib.DropdownIdx])
				ib.ShowDropdown = false
				return ib, nil
			case "esc":
				ib.ShowDropdown = false
				return ib, nil
			}
		}
	}
	oldValue := ib.TextArea.Value()
	var cmd tea.Cmd
	ib.TextArea, cmd = ib.TextArea.Update(msg)
	newValue := ib.TextArea.Value()
	// Trigger dropdown when user types "/" as first character
	if !ib.ShowDropdown && newValue == "/" {
		ib.ShowDropdown = true
		ib.DropdownIdx = 0
	}
	if ib.ShowDropdown && newValue != "/" {
		ib.ShowDropdown = false
	}
	if newValue != oldValue {
		return ib, tea.Batch(cmd, saveDraftCmd(newValue))
	}
	return ib, cmd
}

// SetHistory loads previous queries from store.
func (ib *InputBar) SetHistory(items []string) {
	ib.history = items
	ib.historyIdx = -1
}

// HistoryUp recalls previous query (if textarea is empty or at history).
func (ib *InputBar) HistoryUp() bool {
	if len(ib.history) == 0 {
		return false
	}
	if ib.historyIdx < 0 {
		// Save current draft
		ib.historyIdx = len(ib.history) - 1
	} else if ib.historyIdx > 0 {
		ib.historyIdx--
	} else {
		return false
	}
	ib.TextArea.SetValue(ib.history[ib.historyIdx])
	ib.TextArea.SetCursor(utf8.RuneCountInString(ib.history[ib.historyIdx]))
	return true
}

// HistoryDown recalls next query.
func (ib *InputBar) HistoryDown() bool {
	if ib.historyIdx < 0 || len(ib.history) == 0 {
		return false
	}
	ib.historyIdx++
	if ib.historyIdx >= len(ib.history) {
		ib.historyIdx = -1
		ib.TextArea.SetValue("")
		return true
	}
	ib.TextArea.SetValue(ib.history[ib.historyIdx])
	ib.TextArea.SetCursor(utf8.RuneCountInString(ib.history[ib.historyIdx]))
	return true
}

func (ib *InputBar) draftPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		home = "."
	}
	return filepath.Join(home, ".c4reqber", "draft.txt")
}

func saveDraftCmd(value string) tea.Cmd {
	return func() tea.Msg {
		home, err := os.UserHomeDir()
		if err != nil {
			return fmt.Errorf("draft: home dir: %w", err)
		}
		path := filepath.Join(home, ".c4reqber", "draft.txt")
		if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
			return fmt.Errorf("draft: mkdir: %w", err)
		}
		if err := os.WriteFile(path, []byte(value), 0644); err != nil {
			return fmt.Errorf("draft: write: %w", err)
		}
		return nil
	}
}

func (ib *InputBar) loadDraft() {
	data, err := os.ReadFile(ib.draftPath())
	if err != nil {
		return
	}
	ib.TextArea.SetValue(string(data))
	ib.TextArea.SetCursor(utf8.RuneCountInString(string(data)))
}

// AnalyzeSuggest updates SuggestedMode based on input text heuristics (v7 parity).
func (ib *InputBar) AnalyzeSuggest() {
	t := strings.ToLower(ib.TextArea.Value())
	w := len(strings.Fields(t))
	if w == 0 {
		ib.SuggestedMode = ""
		return
	}
	switch {
	case containsWord(t, "paradigm", "revolution", "breakthrough") && w >= 3:
		ib.SuggestedMode = "turbo"
	case containsWord(t, "explain", "what is", "define") && w <= 6:
		ib.SuggestedMode = "flash"
	case strings.Contains(t, ",") || strings.Contains(t, ";"):
		ib.SuggestedMode = "turbofactory"
	default:
		ib.SuggestedMode = "discover"
	}
}

// containsWord checks whether s contains any of subs as whole words
// (surrounded by spaces/punctuation or string boundaries) to avoid substring false positives.
func containsWord(s string, subs ...string) bool {
	for _, sub := range subs {
		idx := strings.Index(s, sub)
		if idx == -1 {
			continue
		}
		// Check left boundary
		leftOK := idx == 0 || !isWordChar(rune(s[idx-1]))
		// Check right boundary
		rightOK := idx+len(sub) == len(s) || !isWordChar(rune(s[idx+len(sub)]))
		if leftOK && rightOK {
			return true
		}
	}
	return false
}

func isWordChar(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_'
}

var modeButtons = []struct {
	id    string
	label string
}{
	{"discover", internal.T("input.mode.discover")},
	{"flash", internal.T("input.mode.flash")},
	{"turbo", internal.T("input.mode.turbo")},
	{"turbofactory", internal.T("input.mode.turbofactory")},
	{"search", internal.T("input.mode.search")},
	{"verify", internal.T("input.mode.verify")},
}

var compactLabels = map[string]string{
	"discover":     "Disco",
	"flash":        "Flash",
	"turbo":        "Turbo",
	"turbofactory": "Batch",
	"search":       "Srch",
	"verify":       "Vrfy",
}

// ClickAt handles a mouse click at local (x, y) relative to the InputBar.
func (ib InputBar) ClickAt(x, y int) string {
	// Buttons are below the textarea (after Panel padding + textarea height).
	// Allow some slack for wrapped button rows.
	if y < ib.TextArea.Height() {
		return ""
	}
	// Determine labels and compactness.
	labels := make([]string, len(modeButtons))
	for i, m := range modeButtons {
		labels[i] = m.label
	}
	useCompact := ib.width > 0 && ib.width < 50
	if useCompact {
		for i, m := range modeButtons {
			if cl, ok := compactLabels[m.id]; ok {
				labels[i] = cl
			}
		}
	}
	xPos := 0
	for i, m := range modeButtons {
		isActive := ib.Mode == m.id
		isSuggested := ib.SuggestedMode == m.id && ib.SuggestedMode != ib.Mode
		w := btnRenderedWidth(labels[i], useCompact, isActive, isSuggested)
		if x >= xPos && x < xPos+w {
			return m.id
		}
		xPos += w
	}
	return ""
}

// btnRenderedWidth returns the exact lipgloss-rendered width of a mode button.
func btnRenderedWidth(label string, isCompact, isActive, isSuggested bool) int {
	var style lipgloss.Style
	if isCompact {
		style = lipgloss.NewStyle().Padding(0).MarginRight(1)
	} else {
		style = lipgloss.NewStyle().Padding(0, 1).MarginRight(1)
	}
	if isActive {
		style = style.Background(lipgloss.Color(styles.ActiveTheme().Primary)).Foreground(lipgloss.Color(styles.ActiveTheme().Background)).Bold(true)
	} else if isSuggested {
		style = style.BorderStyle(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color(styles.ActiveTheme().Primary)).Foreground(lipgloss.Color(styles.ActiveTheme().Primary))
	} else {
		style = style.Foreground(lipgloss.Color(styles.ActiveTheme().Dim))
	}
	return lipgloss.Width(style.Render(label))
}

var (
	inputCachedVersion         uint64
	inputBtnBase               lipgloss.Style
	inputCompactBtnBase        lipgloss.Style
	inputActiveStyle           lipgloss.Style
	inputCompactActiveStyle    lipgloss.Style
	inputSuggestedStyle        lipgloss.Style
	inputCompactSuggestedStyle lipgloss.Style
	inputDimStyle              lipgloss.Style
	inputCompactDimStyle       lipgloss.Style
	inputHintStyle             lipgloss.Style
)

func syncInputStyles() {
	v := styles.ThemeVersion()
	if inputCachedVersion == v {
		return
	}
	inputCachedVersion = v
	inputBtnBase = lipgloss.NewStyle().Padding(0, 1).MarginRight(1)
	inputCompactBtnBase = lipgloss.NewStyle().Padding(0).MarginRight(1)
	inputActiveStyle = inputBtnBase.Background(lipgloss.Color(styles.ActiveTheme().Primary)).Foreground(lipgloss.Color(styles.ActiveTheme().Background)).Bold(true)
	inputCompactActiveStyle = inputCompactBtnBase.Background(lipgloss.Color(styles.ActiveTheme().Primary)).Foreground(lipgloss.Color(styles.ActiveTheme().Background)).Bold(true)
	inputSuggestedStyle = inputBtnBase.BorderStyle(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color(styles.ActiveTheme().Primary)).Foreground(lipgloss.Color(styles.ActiveTheme().Primary))
	inputCompactSuggestedStyle = inputCompactBtnBase.BorderStyle(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color(styles.ActiveTheme().Primary)).Foreground(lipgloss.Color(styles.ActiveTheme().Primary))
	inputDimStyle = lipgloss.NewStyle().Padding(0, 1).MarginRight(1).Foreground(lipgloss.Color(styles.ActiveTheme().Dim))
	inputCompactDimStyle = lipgloss.NewStyle().Padding(0).MarginRight(1).Foreground(lipgloss.Color(styles.ActiveTheme().Dim))
	inputHintStyle = lipgloss.NewStyle().Foreground(lipgloss.Color(styles.ActiveTheme().Dim)).Italic(true)
}

// View renders textarea + mode buttons + optional suggest hint inside a Panel.
func (ib InputBar) View(width int) string {
	w := ib.width
	if w == 0 {
		w = width
	}
	h := ib.height
	if h == 0 {
		h = 6
	}

	syncInputStyles()
	var sections []string
	sections = append(sections, ib.TextArea.View())

	renderBtn := func(m struct{ id, label string }) string {
		isActive := ib.Mode == m.id
		isSuggested := ib.SuggestedMode == m.id && ib.SuggestedMode != ib.Mode
		if isActive {
			return inputActiveStyle.Render(m.label)
		} else if isSuggested {
			return inputSuggestedStyle.Render(m.label)
		}
		return inputDimStyle.Render(m.label)
	}
	renderCompactBtn := func(m struct{ id, label string }) string {
		isActive := ib.Mode == m.id
		isSuggested := ib.SuggestedMode == m.id && ib.SuggestedMode != ib.Mode
		lbl := m.label
		if cl, ok := compactLabels[m.id]; ok {
			lbl = cl
		}
		if isActive {
			return inputCompactActiveStyle.Render(lbl)
		} else if isSuggested {
			return inputCompactSuggestedStyle.Render(lbl)
		}
		return inputCompactDimStyle.Render(lbl)
	}
	divider := lipgloss.NewStyle().Foreground(lipgloss.Color(styles.ActiveTheme().Dim)).Render("│")
	if w >= 50 {
		var buttons []string
		for i, m := range modeButtons {
			if i > 0 {
				buttons = append(buttons, divider)
			}
			buttons = append(buttons, renderBtn(m))
		}
		sections = append(sections, lipgloss.JoinHorizontal(lipgloss.Left, buttons...))
	} else {
		var row1, row2 []string
		mid := (len(modeButtons) + 1) / 2
		for i, m := range modeButtons {
			if i > 0 && i == mid {
				row1 = append(row1, divider)
			}
			if i == mid && i > 0 {
				row2 = append(row2, divider)
			}
			if i < mid {
				row1 = append(row1, renderCompactBtn(m))
			} else {
				row2 = append(row2, renderCompactBtn(m))
			}
		}
		sections = append(sections, lipgloss.JoinHorizontal(lipgloss.Left, row1...))
		sections = append(sections, lipgloss.JoinHorizontal(lipgloss.Left, row2...))
	}

	// Suggest hint line
	if ib.SuggestedMode != "" && ib.SuggestedMode != ib.Mode {
		sections = append(sections, inputHintStyle.Render(fmt.Sprintf(internal.T("input.suggest"), ib.SuggestedMode)))
	}

	// Mode autocomplete dropdown
	if ib.ShowDropdown {
		var dropdownLines []string
		dropdownLines = append(dropdownLines, lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("─ select mode ─"))
		for i, mode := range modeList {
			label := modePlaceholders[mode]
			if i == ib.DropdownIdx {
				dropdownLines = append(dropdownLines,
					lipgloss.NewStyle().Background(styles.ActiveTheme().Primary).
						Foreground(styles.ActiveTheme().Background).Bold(true).Padding(0, 1).Render("▸ "+label))
			} else {
				dropdownLines = append(dropdownLines,
					lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Padding(0, 1).Render("  "+label))
			}
		}
		sections = append(sections, lipgloss.JoinVertical(lipgloss.Left, dropdownLines...))
	}

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)

	// Dynamic border color: Primary when focused, Dim when blurred
	borderColor := styles.ActiveTheme().Dim
	if ib.TextArea.Focused() {
		borderColor = styles.ActiveTheme().Primary
	}
	return styles.Panel(w, h).BorderForeground(borderColor).Render(content)
}
