package widgets

import (
	"fmt"
	"regexp"
	"strings"

	"c4tui/backend"
	"c4tui/config"
	"c4tui/internal"
	"c4tui/styles"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Result shows discovery metrics, hypotheses, sources.
type Result struct {
	Topic          string
	Papers         int
	Hypotheses     int
	Quality        string
	HypothesesList []map[string]any
	SourcesList    []map[string]any
	Viewport       viewport.Model
	cfg            config.Config
	width          int
	height         int
}

// NewResult creates a new Result widget.
func NewResult(cfg config.Config) Result {
	return Result{
		Viewport: viewport.New(cfg.Layout.TextAreaWidth, cfg.Layout.ResultHeight),
		cfg:      cfg,
		width:    cfg.Layout.TextAreaWidth,
		height:   cfg.Layout.ResultHeight,
	}
}

// SetSize updates panel dimensions.
func (r *Result) SetSize(width, height int) {
	r.width = width
	r.height = height
	if width > 4 {
		r.Viewport.Width = width - 4
	} else {
		r.Viewport.Width = 1
	}
	if height > 4 {
		r.Viewport.Height = height - 4
	} else {
		r.Viewport.Height = 1
	}
}

// Update handles viewport messages.
func (r Result) Update(msg tea.Msg) (Result, tea.Cmd) {
	var cmd tea.Cmd
	r.Viewport, cmd = r.Viewport.Update(msg)
	return r, cmd
}

// qualityColor maps grade to color.
func qualityColor(q string) lipgloss.Color {
	switch {
	case strings.HasPrefix(q, "A+") || strings.HasPrefix(q, "S"):
		return lipgloss.Color(styles.ActiveTheme().Green)
	case strings.HasPrefix(q, "A"):
		return lipgloss.Color(styles.ActiveTheme().Green)
	case strings.HasPrefix(q, "B"):
		return lipgloss.Color(styles.ActiveTheme().Yellow)
	case strings.HasPrefix(q, "C"):
		return lipgloss.Color(styles.ActiveTheme().Orange)
	default:
		return lipgloss.Color(styles.ActiveTheme().Dim)
	}
}

// copyMap returns a shallow copy of m.
func copyMap(m map[string]any) map[string]any {
	out := make(map[string]any, len(m))
	for k, v := range m {
		out[k] = v
	}
	return out
}

// markdownPatterns for lightweight inline syntax highlighting.
var (
	boldRe   = regexp.MustCompile(`\*\*(.+?)\*\*`)
	italicRe = regexp.MustCompile(`\*(.+?)\*`)
	codeRe   = regexp.MustCompile("`(.+?)`")
	headerRe = regexp.MustCompile(`^(#{1,3})\s+(.+)$`)
)

// highlightMarkdown applies lightweight syntax highlighting to a line.
func highlightMarkdown(line string, width int) string {
	// Headers
	if m := headerRe.FindStringSubmatch(line); m != nil {
		level := len(m[1])
		style := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan)
		if level == 1 {
			style = style.Underline(true)
		}
		return style.Render(m[2])
	}
	// Code inline
	line = codeRe.ReplaceAllStringFunc(line, func(s string) string {
		inner := codeRe.FindStringSubmatch(s)[1]
		return lipgloss.NewStyle().Background(styles.ActiveTheme().CursorBg).
			Foreground(styles.ActiveTheme().Foreground).Render(inner)
	})
	// Bold
	line = boldRe.ReplaceAllStringFunc(line, func(s string) string {
		inner := boldRe.FindStringSubmatch(s)[1]
		return lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Highlight).Render(inner)
	})
	// Italic
	line = italicRe.ReplaceAllStringFunc(line, func(s string) string {
		inner := italicRe.FindStringSubmatch(s)[1]
		return lipgloss.NewStyle().Italic(true).Foreground(styles.ActiveTheme().Dim).Render(inner)
	})
	return line
}

// qualityEmoji returns an emoji for the grade.
func qualityEmoji(q string) string {
	switch {
	case strings.HasPrefix(q, "S") || strings.HasPrefix(q, "A+"):
		return "🏆 "
	case strings.HasPrefix(q, "A"):
		return "✨ "
	case strings.HasPrefix(q, "B"):
		return "📊 "
	case strings.HasPrefix(q, "C"):
		return "⚠️ "
	default:
		return "🔍 "
	}
}

// metricCard renders a small metric card.
func metricCard(label, value string, color lipgloss.Color, width int) string {
	inner := lipgloss.JoinVertical(lipgloss.Center,
		lipgloss.NewStyle().Foreground(color).Bold(true).Render(value),
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render(label),
	)
	return lipgloss.NewStyle().
		Width(width).
		Padding(0, 1).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(color).
		Render(inner)
}

// SetContent updates the viewport content from current fields.
func (r *Result) SetContent() {
	var lines []string

	// Pre-create reused styles.
	primaryBold := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary)
	cyanBoldUnder := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan).Underline(true)
	purpleBoldUnder := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Purple).Underline(true)
	dimItalic := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)
	foregroundStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground)
	dimStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)

	// Topic header
	maxTopic := r.width - 8
	if maxTopic < 10 {
		maxTopic = 10
	}
	lines = append(lines, primaryBold.Render(
		"> "+internal.TruncateRunes(r.Topic, maxTopic)))
	lines = append(lines, "")

	// Quality badge — prominent centered badge
	qColor := qualityColor(r.Quality)
	qualityBadge := lipgloss.NewStyle().
		Background(qColor).
		Foreground(styles.ActiveTheme().Background).
		Bold(true).
		Padding(0, 3).
		Render(qualityEmoji(r.Quality) + "  " + r.Quality)
	centeredBadge := lipgloss.NewStyle().Width(maxTopic).Align(lipgloss.Center).Render(qualityBadge)
	lines = append(lines, centeredBadge)
	lines = append(lines, "")

	// Metric cards — responsive: horizontal when wide, vertical when narrow
	cardW := (r.width - 8) / 3
	if cardW < 8 {
		cardW = 8
	}
	papersCard := metricCard(internal.T("result.papers"), fmt.Sprintf("%d", r.Papers), lipgloss.Color(styles.ActiveTheme().Cyan), cardW)
	hypsCard := metricCard(internal.T("result.hypotheses_label"), fmt.Sprintf("%d", r.Hypotheses), lipgloss.Color(styles.ActiveTheme().Yellow), cardW)
	sourcesCard := metricCard(internal.T("result.sources_label"), fmt.Sprintf("%d", len(r.SourcesList)), lipgloss.Color(styles.ActiveTheme().Purple), cardW)
	// Claim coverage card (extracted from result if available)
	claimCovStr := "N/A"
	claimCovColor := lipgloss.Color(styles.ActiveTheme().Dim)
	if len(r.HypothesesList) > 0 {
		if h, ok := internal.ToFloat64(r.HypothesesList[0]["claim_coverage"]); ok && h > 0 {
			claimCovStr = fmt.Sprintf("%.0f%%", h*100)
			if h >= 0.75 {
				claimCovColor = lipgloss.Color(styles.ActiveTheme().Green)
			} else if h >= 0.5 {
				claimCovColor = lipgloss.Color(styles.ActiveTheme().Yellow)
			} else {
				claimCovColor = lipgloss.Color(styles.ActiveTheme().Red)
			}
		}
	}
	claimCard := metricCard("Coverage", claimCovStr, claimCovColor, cardW)
	var metricsRow string
	if r.width >= 60 {
		metricsRow = lipgloss.JoinHorizontal(lipgloss.Top, papersCard, " ", hypsCard, " ", sourcesCard, " ", claimCard)
	} else if r.width >= 50 {
		metricsRow = lipgloss.JoinHorizontal(lipgloss.Top, papersCard, " ", hypsCard, " ", sourcesCard)
	} else {
		metricsRow = lipgloss.JoinVertical(lipgloss.Left, papersCard, hypsCard, sourcesCard, claimCard)
	}
	lines = append(lines, metricsRow)
	lines = append(lines, "")

	// Hypotheses table
	if len(r.HypothesesList) > 0 {
		lines = append(lines, cyanBoldUnder.Render(internal.T("result.hypotheses")))
		for i, h := range r.HypothesesList {
			if i >= 10 {
				break
			}
			title, _ := h["title"].(string)
			if title == "" {
				title = fmt.Sprintf("H%d", i+1)
			}
			conf, _ := h["confidence"].(float64)
			confStr := ""
			if conf > 0 {
				confColor := styles.ActiveTheme().Green
				if conf < 0.5 {
					confColor = styles.ActiveTheme().Red
				} else if conf < 0.8 {
					confColor = styles.ActiveTheme().Yellow
				}
				confStr = lipgloss.NewStyle().Foreground(confColor).Render(fmt.Sprintf(" (%.0f%%)", conf*100))
			}
			lines = append(lines, fmt.Sprintf("  %d. %s%s", i+1,
				foregroundStyle.Render(title), confStr))
		}
	}

	// Sources table
	if len(r.SourcesList) > 0 {
		lines = append(lines, "")
		lines = append(lines, purpleBoldUnder.Render(internal.T("result.sources")))
		for i, s := range r.SourcesList {
			if i >= 10 {
				break
			}
			title, _ := s["title"].(string)
			if title == "" {
				title, _ = s["name"].(string)
			}
			if title == "" {
				title = fmt.Sprintf("S%d", i+1)
			}
			year, _ := s["year"].(float64)
			yearStr := ""
			if year > 0 {
				yearStr = dimStyle.Render(fmt.Sprintf(" [%d]", int(year)))
			}
			source, _ := s["source"].(string)
			sourceStr := ""
			if source != "" {
				sourceStr = dimStyle.Render(" " + source)
			}
			lines = append(lines, fmt.Sprintf("  %d. %s%s%s", i+1,
				foregroundStyle.Render(internal.TruncateRunes(title, r.width-12)),
				yearStr, sourceStr))
		}
	}

	// Export hint
	lines = append(lines, "")
	lines = append(lines, dimItalic.Render(internal.T("result.export_hint")))

	// Apply syntax highlighting to each line
	highlighted := make([]string, len(lines))
	for i, line := range lines {
		highlighted[i] = highlightMarkdown(line, r.width)
	}
	r.Viewport.SetContent(strings.Join(highlighted, "\n"))
	r.Viewport.GotoTop()
}

// SetSearchResults updates the panel from a search response.
func (r *Result) SetSearchResults(resp *backend.SearchResponse) {
	if resp == nil {
		return
	}
	r.Topic = resp.Query
	r.Papers = resp.Total
	r.Hypotheses = 0
	r.Quality = "search"
	r.HypothesesList = nil
	r.SourcesList = make([]map[string]any, 0, len(resp.Results))
	for _, paper := range resp.Results {
		r.SourcesList = append(r.SourcesList, map[string]any{
			"title":   paper.Title,
			"authors": paper.Authors,
			"year":    paper.Year,
			"source":  paper.Source,
		})
	}
	r.SetContent()
}

// SetVerifyResult updates the panel from a verification response.
func (r *Result) SetVerifyResult(resp *backend.VerifyResponse) {
	if resp == nil {
		return
	}
	r.Topic = "Verification " + resp.VerifyID
	r.Papers = 0
	r.Hypotheses = 0
	r.Quality = resp.Method
	if resp.Verified {
		r.Quality += " ✅"
	} else {
		r.Quality += " ❌"
	}
	r.HypothesesList = nil
	r.SourcesList = nil
	var lines []string
	lines = append(lines, lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render(internal.T("result.verification")))
	lines = append(lines, "")
	lines = append(lines, fmt.Sprintf("%s %s", internal.T("result.method"), resp.Method))
	lines = append(lines, fmt.Sprintf("%s %v", internal.T("result.verified"), resp.Verified))
	if len(resp.Errors) > 0 {
		lines = append(lines, "")
		lines = append(lines, lipgloss.NewStyle().Foreground(styles.ActiveTheme().Red).Render(internal.T("result.errors")))
		for _, err := range resp.Errors {
			lines = append(lines, "  "+err)
		}
	}
	r.Viewport.SetContent(strings.Join(lines, "\n"))
}

// SetJobResult updates the panel from a completed job result.
func (r *Result) SetJobResult(result map[string]any) {
	if result == nil {
		return
	}
	if problem, ok := result["problem"].(string); ok {
		r.Topic = problem
	}
	if papers, ok := internal.ToFloat64(result["_papers_found"]); ok {
		r.Papers = int(papers)
	}
	if quality, ok := result["quality"].(string); ok {
		r.Quality = quality
	} else {
		r.Quality = "unknown"
	}
	// Extract hypotheses from result if available (plural array first, then singular map)
	if hypsArray, ok := result["hypotheses"].([]any); ok && len(hypsArray) > 0 {
		r.HypothesesList = make([]map[string]any, 0, len(hypsArray))
		for _, h := range hypsArray {
			if hm, ok := h.(map[string]any); ok {
				r.HypothesesList = append(r.HypothesesList, hm)
			}
		}
		r.Hypotheses = len(r.HypothesesList)
	} else if hyps, ok := result["hypothesis"].(map[string]any); ok {
		r.HypothesesList = []map[string]any{hyps}
		r.Hypotheses = 1
	} else {
		r.Hypotheses = 0
		r.HypothesesList = nil
	}
	// Inject claim coverage into first hypothesis for metric card display (copy to avoid mutating input)
	if len(r.HypothesesList) > 0 {
		if cv, ok := result["claim_verification"].(map[string]any); ok {
			if cov, ok := internal.ToFloat64(cv["overall_coverage"]); ok {
				r.HypothesesList[0] = copyMap(r.HypothesesList[0])
				r.HypothesesList[0]["claim_coverage"] = cov
			}
		}
	}
	// Extract sources from papers list
	if papers, ok := result["_papers_list"].([]any); ok {
		r.SourcesList = make([]map[string]any, 0, len(papers))
		for _, p := range papers {
			if pm, ok := p.(map[string]any); ok {
				r.SourcesList = append(r.SourcesList, pm)
			}
		}
	}
	r.SetContent()
}

var emptyCube = `
    ╭─────────╮
   ╱         ╱│
  ╱    ▣    ╱ │
 ╱         ╱  │
╰─────────╯   │
│    ▣    │   │
│         │  ╱
│    ▣    │ ╱
╰─────────╯
`

// View renders the result panel.
func (r Result) View(width int) string {
	w := width
	if r.width > 0 {
		w = r.width
	}
	h := r.height
	if h == 0 {
		h = r.cfg.Layout.ResultHeight
	}

	// Pre-create reused styles.
	primaryBold := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary)
	cyanStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
	dimItalic := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)
	dimStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	scrollStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)

	if r.Topic == "" {
		emptyContent := lipgloss.JoinVertical(lipgloss.Center,
			primaryBold.Render(internal.T("panel.result")),
			"",
			cyanStyle.Render(emptyCube),
			"",
			dimItalic.Render(internal.T("panel.result.waiting")),
			"",
			dimStyle.Render(internal.T("panel.result.hint"))+
				cyanStyle.Render("Ctrl+Enter")+
				dimStyle.Render(internal.T("panel.result.hint2")),
		)
		return styles.Panel(w, h).Render(emptyContent)
	}

	content := r.Viewport.View()
	// Scroll indicator when content overflows
	if r.Viewport.TotalLineCount() > r.Viewport.VisibleLineCount() {
		scrollInfo := scrollStyle.Render(fmt.Sprintf("─ %d/%d ─", r.Viewport.VisibleLineCount(), r.Viewport.TotalLineCount()))
		content = lipgloss.JoinVertical(lipgloss.Left, content, scrollInfo)
	}
	return styles.Panel(w, h).Render(content)
}
