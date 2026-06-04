package widgets

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"c4tui/config"
	"c4tui/internal"
	"c4tui/styles"
	"github.com/charmbracelet/bubbles/progress"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Pipeline tracks 7-phase progress + narrative log.
type Pipeline struct {
	Running    bool
	CurPhase   int
	Statuses   []string // ○, ●, ✓, ✕
	Infos      []string
	Progress   []float64 // real 0-1 progress per phase
	Bars       []progress.Model
	Log        []string
	StartTime  time.Time
	elapsedStr string // cached formatted elapsed time to avoid time.Since in View()
	cfg        config.Config
	width      int
	height     int
}

// phaseNames maps backend phase names to indices.
var phaseNames = []string{
	"A: Framing",
	"B: Search",
	"C: Gaps",
	"D: Hyps",
	"E: Sim",
	"F: Dissertation",
	"G: Quality",
}

// phaseStories provides narrative flavor text per phase.
var phaseStories = []string{
	"Framing the problem space...",
	"Searching knowledge graph...",
	"Identifying gaps & contradictions...",
	"Generating hypotheses...",
	"Running simulations...",
	"Synthesizing dissertation...",
	"Validating quality & rigor...",
}

// PhaseIndex returns the index for a phase name (exported for mascot linkage).
func PhaseIndex(name string) int {
	if name == "" {
		return -1
	}
	// Try exact match first
	for i, n := range phaseNames {
		if n == name {
			return i
		}
	}
	// Try substring match (e.g. "Framing" matches "A: Framing")
	for i, n := range phaseNames {
		if strings.Contains(n, name) || strings.Contains(name, n) {
			return i
		}
	}
	return -1
}

// phaseColor returns the accent color for a given phase index.
// It reads from the active theme so colors stay correct after theme cycling.
func phaseColor(i int) lipgloss.Color {
	colors := []lipgloss.Color{
		styles.ActiveTheme().Cyan,   // A: Framing
		styles.ActiveTheme().Yellow, // B: Search
		styles.ActiveTheme().Purple, // C: Gaps
		styles.ActiveTheme().Green,  // D: Hyps
		styles.ActiveTheme().Pink,   // E: Sim
		styles.ActiveTheme().Orange, // F: Dissertation
		styles.ActiveTheme().Red,    // G: Quality
	}
	if i < 0 || i >= len(colors) {
		return styles.ActiveTheme().Primary
	}
	return colors[i]
}

// NewPipeline initializes 7 progress bars.
func NewPipeline(cfg config.Config) Pipeline {
	bars := make([]progress.Model, 7)
	for i := range bars {
		bars[i] = progress.New(progress.WithGradient(
			string(phaseColor(i)),
			string(styles.ActiveTheme().Secondary),
		))
	}
	return Pipeline{
		Statuses: make([]string, 7),
		Infos:    make([]string, 7),
		Progress: make([]float64, 7),
		Bars:     bars,
		cfg:      cfg,
	}
}

// SetSize updates panel dimensions and progress bar widths.
func (p *Pipeline) SetSize(width, height int) {
	p.width = width
	p.height = height
	barWidth := width - 24
	if barWidth < 8 {
		barWidth = 8
	}
	for i := range p.Bars {
		p.Bars[i].Width = barWidth
	}
}

// Start resets and begins the pipeline.
func (p *Pipeline) Start() {
	p.Running = true
	p.CurPhase = 0
	p.StartTime = time.Now()
	p.elapsedStr = ""
	p.Log = p.Log[:0]
	for i := range p.Statuses {
		p.Statuses[i] = "○"
		p.Infos[i] = ""
		p.Progress[i] = 0
	}
}

// SetThemeColors recreates progress bars with the active theme gradient.
func (p *Pipeline) SetThemeColors() {
	for i := range p.Bars {
		w := p.Bars[i].Width
		p.Bars[i] = progress.New(progress.WithGradient(
			string(phaseColor(i)),
			string(styles.ActiveTheme().Secondary),
		))
		p.Bars[i].Width = w
	}
}

// Stop halts the pipeline.
func (p *Pipeline) Stop() {
	p.Running = false
}

// SetPhaseName updates a phase by its name with real progress from backend.
func (p *Pipeline) SetPhaseName(name, status string, progressPct float64) {
	idx := PhaseIndex(name)
	if idx < 0 {
		return
	}
	p.Progress[idx] = progressPct
	p.Statuses[idx] = status

	p.elapsedStr = ""
	if !p.StartTime.IsZero() {
		sec := time.Since(p.StartTime).Seconds()
		p.elapsedStr = " " + strconv.FormatFloat(sec, 'f', 1, 64) + "s"
	}

	switch {
	case status == "done" || status == "complete":
		p.Statuses[idx] = "✓"
		p.Progress[idx] = 1.0
		p.CurPhase = idx + 1
		for i := 0; i < idx; i++ {
			if p.Statuses[i] != "✕" {
				p.Statuses[i] = "✓"
				p.Progress[i] = 1.0
			}
		}
	case status == "working" || status == "running":
		p.Statuses[idx] = "●"
		p.CurPhase = idx
	case status == "failed" || status == "error":
		p.Statuses[idx] = "✕"
	}

	p.Infos[idx] = fmt.Sprintf("%.0f%%%s", progressPct*100, p.elapsedStr)

	story := ""
	if idx < len(phaseStories) {
		story = phaseStories[idx]
	}
	entry := fmt.Sprintf("%s %s — %s", p.Statuses[idx], name, story)
	// Deduplicate: skip if the last log entry is identical
	if len(p.Log) == 0 || p.Log[len(p.Log)-1] != entry {
		p.Log = append(p.Log, entry)
	}
	maxLog := p.cfg.Layout.PipelineHeight / 3
	if maxLog < 1 {
		maxLog = 1
	}
	if len(p.Log) > maxLog {
		p.Log = p.Log[len(p.Log)-maxLog:]
	}
}

// Update handles messages.
func (p Pipeline) Update(msg tea.Msg) (Pipeline, tea.Cmd) {
	var cmds []tea.Cmd
	for i := range p.Bars {
		m, cmd := p.Bars[i].Update(msg)
		if bar, ok := m.(progress.Model); ok {
			p.Bars[i] = bar
		}
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
	}
	return p, tea.Batch(cmds...)
}

// phaseIcons are tiny ASCII glyphs for each phase.
var phaseIcons = []string{"◉", "◎", "◈", "◇", "◆", "◊", "○"}


// renderSparkline draws a colorful mini bar using block characters.
func renderSparkline(progress float64, width int, color lipgloss.Color) string {
	if width < 2 {
		width = 2
	}
	filled := int(progress * float64(width))
	if filled > width {
		filled = width
	}
	empty := width - filled

	style := lipgloss.NewStyle().Foreground(color)
	dimStyle := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)

	var sb strings.Builder
	for i := 0; i < filled; i++ {
		sb.WriteRune('█')
	}
	for i := 0; i < empty; i++ {
		sb.WriteRune('░')
	}

	return style.Render(sb.String()[:filled]) + dimStyle.Render(sb.String()[filled:])
}

var (
	pipeCachedVersion uint64
	pipeDim           lipgloss.Style
	pipePrimaryBold   lipgloss.Style
	pipeSuccessBold   lipgloss.Style
	pipeRedBold       lipgloss.Style
	pipeGreen         lipgloss.Style
	pipeRed           lipgloss.Style
	pipeYellowBold    lipgloss.Style
	pipeItalicDim     lipgloss.Style
)

func syncPipelineStyles() {
	v := styles.ThemeVersion()
	if pipeCachedVersion == v {
		return
	}
	pipeCachedVersion = v
	pipeDim = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	pipePrimaryBold = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Primary).Bold(true)
	pipeSuccessBold = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Success).Bold(true)
	pipeRedBold = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Red).Bold(true)
	pipeGreen = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Green)
	pipeRed = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Red)
	pipeYellowBold = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow).Bold(true)
	pipeItalicDim = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)
}

// View renders progress bars + log.
func (p Pipeline) View(width int) string {
	w := width
	if p.width > 0 {
		w = p.width
	}
	lines := make([]string, 0, 20)
	syncPipelineStyles()

	// Completion summary when done
	completed := 0
	failed := 0
	for _, s := range p.Statuses {
		if s == "✓" {
			completed++
		}
		if s == "✕" {
			failed++
		}
	}

	// Idle state — compact hint, no empty circles
	if !p.Running && p.StartTime.IsZero() && completed == 0 {
		idle := lipgloss.JoinVertical(lipgloss.Center,
			pipeItalicDim.Render("💡 "+internal.T("pipeline.hint")),
			pipePrimaryBold.Render("Ctrl+Enter →"),
		)
		h := p.cfg.Layout.PipelineHeight
		if p.height > 0 {
			h = p.height
		}
		return styles.Panel(w, h).Render(idle)
	}

	if !p.Running && completed > 0 {
		totalElapsed := ""
		if !p.StartTime.IsZero() {
			sec := int(time.Since(p.StartTime).Seconds())
			totalElapsed = fmt.Sprintf(" · %d:%02d", sec/60, sec%60)
		}
		summary := pipeSuccessBold.Render(fmt.Sprintf("✓ %d/%d %s%s", completed, 7, internal.T("pipeline.phases"), totalElapsed))
		if failed > 0 {
			summary += " " + pipeRedBold.Render(fmt.Sprintf("· %d failed", failed))
		}
		lines = append(lines, summary)
	} else {
		// Compact header with elapsed time when running
		header := "▶ " + internal.T("pipeline.header")
		if p.Running && !p.StartTime.IsZero() {
			sec := int(time.Since(p.StartTime).Seconds())
			header = fmt.Sprintf("▶ %s  %d:%02d", internal.T("pipeline.header"), sec/60, sec%60)
		}
		lines = append(lines, pipePrimaryBold.Render(header))
	}

	for i := 0; i < 7; i++ {
		status := p.Statuses[i]
		if status == "" {
			status = "○"
		}

		var statusStyle lipgloss.Style
		isActive := status == "●"
		switch status {
		case "✓":
			statusStyle = pipeGreen
		case "✕":
			statusStyle = pipeRed
		case "●":
			statusStyle = pipeYellowBold
		default:
			statusStyle = pipeDim
		}

		label := statusStyle.Render(status + " " + phaseIcons[i] + " " + phaseNames[i])
		if isActive {
			label = pipeYellowBold.Render("▸ ") + label
		}
		info := pipeDim.Render(p.Infos[i])

		// Use sparkline for narrow, progress bar for wide
		var bar string
		if w < 50 {
			sparkW := 8
			if w < 35 {
				sparkW = 4
			}
			bar = renderSparkline(p.Progress[i], sparkW, phaseColor(i))
		} else {
			bar = p.Bars[i].ViewAs(p.Progress[i])
		}
		lines = append(lines, label+" "+bar+" "+info)
	}

	// Compact log: last entry only when narrow, last 3 otherwise
	if len(p.Log) > 0 {
		logView := strings.Join(p.Log, "\n")
		if len(p.Log) > 3 {
			logView = strings.Join(p.Log[len(p.Log)-3:], "\n")
		}
		lines = append(lines, pipeItalicDim.Render(logView))
	} else if !p.Running {
		lines = append(lines, "")
		lines = append(lines, pipeItalicDim.Render("💡 "+internal.T("pipeline.hint")))
	}

	h := p.cfg.Layout.PipelineHeight
	if p.height > 0 {
		h = p.height
	}
	return styles.Panel(w, h).Render(lipgloss.JoinVertical(lipgloss.Left, lines...))
}
