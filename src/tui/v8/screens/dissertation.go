package screens

import (
	"fmt"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Dissertation shows the full discovery record.
type Dissertation struct {
	width  int
	height int
	result map[string]any
	done   bool
}

// NewDissertation creates a dissertation viewer overlay.
func NewDissertation(result map[string]any) Dissertation {
	return Dissertation{result: result}
}

func (d Dissertation) Title() string { return "Dissertation" }
func (d Dissertation) Done() bool    { return d.done }

func (d Dissertation) Init() tea.Cmd { return nil }

func (d Dissertation) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
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

func (d Dissertation) View() string {
	if d.width == 0 {
		return ""
	}
	if d.result == nil {
		return d.centerBox("No discovery data available.\nRun a pipeline first.")
	}

	cyan := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	yellow := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)

	var sections []string

	// Title / Problem
	if problem, ok := d.result["problem"].(string); ok {
		sections = append(sections, yellow.Render("Problem"))
		sections = append(sections, internal.WrapRunes(problem, d.width-12))
		sections = append(sections, "")
	}

	// Quality
	if quality, ok := d.result["quality"].(string); ok {
		sections = append(sections, cyan.Render("Quality Score: "+quality))
		sections = append(sections, "")
	}

	// Hypotheses
	if hyps, ok := d.result["hypotheses"].([]any); ok && len(hyps) > 0 {
		sections = append(sections, yellow.Render("Hypotheses"))
		for i, h := range hyps {
			if hm, ok := h.(map[string]any); ok {
				text := fmt.Sprintf("%d. %v", i+1, hm["text"])
				sections = append(sections, internal.WrapRunes(text, d.width-12))
			}
		}
		sections = append(sections, "")
	} else if hyp, ok := d.result["hypothesis"].(map[string]any); ok {
		sections = append(sections, yellow.Render("Hypothesis"))
		if text, ok := hyp["text"].(string); ok {
			sections = append(sections, internal.WrapRunes(text, d.width-12))
		}
		sections = append(sections, "")
	}

	// Sources
	if papers, ok := d.result["_papers_list"].([]any); ok && len(papers) > 0 {
		sections = append(sections, yellow.Render(fmt.Sprintf("Sources (%d)", len(papers))))
		for i, p := range papers {
			if pm, ok := p.(map[string]any); ok {
				title := fmt.Sprintf("%v", pm["title"])
				sections = append(sections, fmt.Sprintf("  %d. %s", i+1, internal.TruncateRunes(title, d.width-16)))
			}
		}
		sections = append(sections, "")
	}

	// Verification
	if verify, ok := d.result["verification"].(map[string]any); ok {
		sections = append(sections, yellow.Render("Verification"))
		for k, v := range verify {
			sections = append(sections, fmt.Sprintf("  %s: %v", k, v))
		}
		sections = append(sections, "")
	}

	// Claim Verification Coverage
	if cv, ok := d.result["claim_verification"].(map[string]any); ok {
		sections = append(sections, yellow.Render("Claim Verification"))
		if coverage, ok := internal.ToFloat64(cv["overall_coverage"]); ok {
			covColor := styles.ActiveTheme().Green
			if coverage < 0.5 {
				covColor = styles.ActiveTheme().Red
			} else if coverage < 0.75 {
				covColor = styles.ActiveTheme().Yellow
			}
			covStr := lipgloss.NewStyle().Foreground(covColor).Bold(true).Render(fmt.Sprintf("%.0f%%", coverage*100))
			passed := "❌"
			if p, ok := cv["passed"].(bool); ok && p {
				passed = "✅"
			}
			sections = append(sections, fmt.Sprintf("  Coverage: %s %s", covStr, passed))
		}
		if sc, ok := internal.ToFloat64(cv["supported_count"]); ok {
			cc, _ := cv["claim_count"].(float64)
			sections = append(sections, fmt.Sprintf("  Claims: %.0f/%.0f supported", sc, cc))
		}
		if unsupported, ok := cv["unsupported_claims"].([]any); ok && len(unsupported) > 0 {
			sections = append(sections, dim.Render("  Unsupported:"))
			for _, uc := range unsupported {
				if us, ok := uc.(string); ok {
					sections = append(sections, dim.Render("    • "+internal.TruncateRunes(us, d.width-18)))
				}
			}
		}
		sections = append(sections, "")
	}

	// Raw fields (anything else)
	for k, v := range d.result {
		if k == "problem" || k == "quality" || k == "hypotheses" || k == "hypothesis" ||
			k == "_papers_list" || k == "verification" || k == "_papers_found" {
			continue
		}
		sections = append(sections, cyan.Render(k))
		sections = append(sections, internal.WrapRunes(fmt.Sprintf("%v", v), d.width-12))
		sections = append(sections, "")
	}

	sections = append(sections, "", dim.Render("Press Esc or Q to close"))
	content := lipgloss.JoinVertical(lipgloss.Left, sections...)

	box := lipgloss.NewStyle().
		Width(d.width - 6).
		Height(d.height - 4).
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

func (d Dissertation) centerBox(text string) string {
	box := lipgloss.NewStyle().
		Width(d.width - 10).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(text)
	return lipgloss.Place(d.width, d.height, lipgloss.Center, lipgloss.Center, box)
}
