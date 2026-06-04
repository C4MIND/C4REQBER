package screens

import (
	"encoding/json"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ExportResult is sent when an export completes.
type ExportResultMsg struct {
	Path string
	Err  error
}

// Export formats.
const (
	FormatMarkdown = "markdown"
	FormatJSON     = "json"
	FormatHTML     = "html"
	FormatBibTeX   = "bibtex"
)

// ExportPicker lets the user choose an export format.
type ExportPicker struct {
	width   int
	height  int
	cursor  int
	formats []string
	result  map[string]any
	done    bool
}

// NewExportPicker creates an export picker with the current result data.
func NewExportPicker(result map[string]any) ExportPicker {
	return ExportPicker{
		formats: []string{
			internal.T("export.markdown"),
			internal.T("export.json"),
			internal.T("export.html"),
			internal.T("export.bibtex"),
		},
		result: result,
	}
}

func (e ExportPicker) Title() string { return "Export" }
func (e ExportPicker) Done() bool    { return e.done }

func (e ExportPicker) Init() tea.Cmd { return nil }

func (e ExportPicker) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		e.width = msg.Width
		e.height = msg.Height
		return e, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q":
			e.done = true
			return e, nil
		case "up", "k":
			if e.cursor > 0 {
				e.cursor--
			}
		case "down", "j":
			if e.cursor < len(e.formats)-1 {
				e.cursor++
			}
		case "enter":
			return e, e.exportCmd(e.cursor)
		}
	}
	return e, nil
}

func (e ExportPicker) exportCmd(idx int) tea.Cmd {
	return func() tea.Msg {
		home, err := os.UserHomeDir()
		if err != nil {
			return ExportResultMsg{Err: fmt.Errorf("home dir: %w", err)}
		}
		outDir := filepath.Join(home, ".c4reqber", "exports")
		if err := os.MkdirAll(outDir, 0755); err != nil {
			return ExportResultMsg{Err: fmt.Errorf("mkdir: %w", err)}
		}

		now := time.Now()
		ts := now.Format("20060102-150405")
		var path string
		var data []byte

		switch idx {
		case 0:
			path = filepath.Join(outDir, "export-"+ts+".md")
			data, err = e.toMarkdown(now)
		case 1:
			path = filepath.Join(outDir, "export-"+ts+".json")
			data, err = e.toJSON()
		case 2:
			path = filepath.Join(outDir, "export-"+ts+".html")
			data, err = e.toHTML(now)
		case 3:
			path = filepath.Join(outDir, "export-"+ts+".bib")
			data, err = e.toBibTeX(now)
		default:
			return ExportResultMsg{Err: fmt.Errorf("unknown export format index %d", idx)}
		}

		if err != nil {
			return ExportResultMsg{Err: err}
		}
		if err := os.WriteFile(path, data, 0644); err != nil {
			return ExportResultMsg{Err: err}
		}
		return ExportResultMsg{Path: path}
	}
}

func (e ExportPicker) toMarkdown(now time.Time) ([]byte, error) {
	var b strings.Builder
	b.WriteString("# C4REQBER Export\n\n")
	b.WriteString("Generated: ")
	b.WriteString(now.Format(time.RFC3339))
	b.WriteString("\n\n")
	keys := make([]string, 0, len(e.result))
	for k := range e.result {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		b.WriteString("## ")
		b.WriteString(k)
		b.WriteString("\n\n")
		fmt.Fprintf(&b, "%v\n\n", e.result[k])
	}
	return []byte(b.String()), nil
}

func (e ExportPicker) toJSON() ([]byte, error) {
	return json.MarshalIndent(e.result, "", "  ")
}

func (e ExportPicker) toHTML(now time.Time) ([]byte, error) {
	var b strings.Builder
	b.WriteString("<!DOCTYPE html>\n<html>\n<head>\n")
	b.WriteString("<meta charset=\"UTF-8\">\n")
	b.WriteString("<title>C4REQBER Export</title>\n")
	b.WriteString("</head>\n<body>\n")
	b.WriteString("<h1>C4REQBER Export</h1>\n")
	b.WriteString("<p>Generated: " + now.Format(time.RFC3339) + "</p>\n")
	for k, v := range e.result {
		b.WriteString("<h2>" + html.EscapeString(k) + "</h2>\n")
		b.WriteString("<pre>" + html.EscapeString(fmt.Sprintf("%v", v)) + "</pre>\n")
	}
	b.WriteString("</body>\n</html>\n")
	return []byte(b.String()), nil
}

// bibTeXEscape escapes special BibTeX characters inside brace-delimited fields.
func bibTeXEscape(s string) string {
	replacer := strings.NewReplacer(
		`\`, `\textbackslash{}`,
		`{`, `\{`,
		`}`, `\}`,
		`$`, `\$`,
		`&`, `\&`,
		`#`, `\#`,
		`^`, `\^{}`,
		`_`, `\_`,
		`~`, `\~{}`,
		`%`, `\%`,
	)
	return replacer.Replace(s)
}

func (e ExportPicker) toBibTeX(now time.Time) ([]byte, error) {
	var b strings.Builder
	b.WriteString("% C4REQBER BibTeX Export\n")
	b.WriteString("% Generated: " + now.Format(time.RFC3339) + "\n\n")

	// Try to extract sources from the result
	sources, _ := e.result["_papers_list"].([]any)
	for i, src := range sources {
		if m, ok := src.(map[string]any); ok {
			title, _ := m["title"].(string)
			authors, _ := m["authors"].([]any)
			year, _ := internal.ToFloat64(m["year"])
			url, _ := m["url"].(string)

			var authorStrs []string
			for _, a := range authors {
				if s, ok := a.(string); ok {
					authorStrs = append(authorStrs, bibTeXEscape(s))
				}
			}
			key := fmt.Sprintf("c4_%d", i+1)
			b.WriteString(fmt.Sprintf("@article{%s,\n", key))
			b.WriteString(fmt.Sprintf("  title = {%s},\n", bibTeXEscape(title)))
			b.WriteString(fmt.Sprintf("  author = {%s},\n", strings.Join(authorStrs, " and ")))
			b.WriteString(fmt.Sprintf("  year = {%d},\n", int(year)))
			if url != "" {
				b.WriteString(fmt.Sprintf("  url = {%s},\n", url))
			}
			b.WriteString("}\n\n")
		}
	}
	if sources == nil {
		b.WriteString("% No paper sources found in result.\n")
	}
	return []byte(b.String()), nil
}

func (e ExportPicker) View() string {
	if e.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Export Results")
	sub := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Choose a format")

	var items []string
	for i, f := range e.formats {
		cursor := "  "
		style := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground)
		if i == e.cursor {
			cursor = "> "
			style = lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan)
		}
		items = append(items, style.Render(cursor+f))
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		sub,
		"",
		lipgloss.JoinVertical(lipgloss.Left, items...),
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Enter to export  •  Esc/Q to close"),
	)

	boxW := e.width - 4
	if boxW < 20 {
		boxW = 20
	}
	if boxW > 60 {
		boxW = 60
	}
	box := lipgloss.NewStyle().
		Width(boxW).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		e.width, e.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
