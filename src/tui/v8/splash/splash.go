package splash

import (
	"fmt"
	"math"
	"math/rand"
	"regexp"
	"strconv"
	"strings"
	"time"

	"c4tui/styles"

	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ansiEscapePattern matches ANSI escape sequences.
var ansiEscapePattern = regexp.MustCompile(`\x1b\[[0-9;]*[a-zA-Z]`)

// DoneMsg signals that the splash sequence has finished.
type DoneMsg struct{}

// Model is the splash screen Bubble Tea model.
type Model struct {
	width       int
	height      int
	phase       string // "crystal" | "dissolve" | "waiting"
	loadingDone bool
	morphTick   int
	morphLines  []string
	forms       [][]string
	seedArt     string // stripped ANSI art for morph start
	textTick    int    // progressive text fade-in
	pulseTick   int    // cube shimmer in waiting phase
	spinner     spinner.Model
	rng         *rand.Rand
}

// ── Constants ───────────────────────────────────────────────────────────────

const (
	formDuration     = 10 // ticks per morph form
	tickInterval     = 60 * time.Millisecond
	crystalDelay     = 5 * time.Second
	artReserve       = 12 // tagline + motto + status + footer + version + spacers
	pulseInterval    = 400 * time.Millisecond
	textFadeInterval = 80 * time.Millisecond
	bottomLift       = 3 // lift art+text up from the bottom edge
)

// ── Constructor ─────────────────────────────────────────────────────────────

// New creates a new splash model.
func New() Model {
	s := spinner.New()
	s.Spinner = spinner.Points
	return Model{
		phase:   "crystal",
		spinner: s,
		rng:     rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// Done returns a command that transitions to the main app.
func Done() tea.Msg { return DoneMsg{} }

// ── Init ────────────────────────────────────────────────────────────────────

// Init starts the splash animation sequence.
func (m Model) Init() tea.Cmd {
	return tea.Batch(
		tea.Tick(crystalDelay, func(_ time.Time) tea.Msg {
			return startDissolveMsg{}
		}),
		textFadeTickCmd(),
		m.spinner.Tick,
	)
}

// ── Update ──────────────────────────────────────────────────────────────────

// Update handles messages for the splash model.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		case "enter":
			if m.phase == "waiting" {
				m.loadingDone = true
				return m, func() tea.Msg { return DoneMsg{} }
			}
		default:
			// Any other key skips the crystal delay and starts dissolve immediately
			if m.phase == "crystal" {
				return m.startDissolve()
			}
		}

	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		if m.phase == "waiting" {
			m.forms = buildForms(m.artHeight(), m.seedArt, m.isCompact(), m.rng)
		} else if m.phase == "dissolve" {
			// Rebuild forms for new dimensions and preserve as much morph state
			// as possible by copying the existing morphLines into the new forms.
			oldMorph := m.morphLines
			m.forms = buildForms(m.artHeight(), m.seedArt, m.isCompact(), m.rng)
			m.morphLines = make([]string, len(m.forms[0]))
			copy(m.morphLines, m.forms[0])
			// Overlay previous morph state onto new lines where lengths match.
			for i := range min(len(oldMorph), len(m.morphLines)) {
				m.morphLines[i] = oldMorph[i]
			}
		}
		return m, nil

	case startDissolveMsg:
		if m.phase == "dissolve" || m.phase == "waiting" {
			return m, nil // already past crystal
		}
		return m.startDissolve()

	case dissolveTickMsg:
		m.morphTick = msg.tick
		if m.morphTick < m.totalMorphTicks() {
			m.advanceMorphWave()
			return m, dissolveTickCmd(m.morphTick + 1)
		}
		m.phase = "waiting"
		return m, cubePulseCmd()

	case textFadeTickMsg:
		if m.textTick < maxTextFadeTick {
			m.textTick++
			return m, textFadeTickCmd()
		}
		return m, nil
	default:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd

	case cubePulseMsg:
		if m.phase == "waiting" {
			m.pulseTick++
			return m, cubePulseCmd()
		}
		return m, nil

	case DoneMsg:
		m.loadingDone = true
		return m, nil
	}

	return m, nil
}

// startDissolve transitions from crystal → dissolve.
func (m Model) startDissolve() (Model, tea.Cmd) {
	m.phase = "dissolve"
	m.seedArt = stripANSI(m.pickANSI())
	m.forms = buildForms(m.artHeight(), m.seedArt, m.isCompact(), m.rng)
	m.morphLines = make([]string, len(m.forms[0]))
	copy(m.morphLines, m.forms[0])
	m.morphTick = 0
	// Reseed the local random source so each dissolve looks unique.
	m.rng.Seed(time.Now().UnixNano())
	return m, dissolveTickCmd(0)
}

// totalMorphTicks returns the total number of dissolve ticks needed.
func (m Model) totalMorphTicks() int {
	if len(m.forms) == 0 {
		return 0
	}
	// Last form is the final hold; we only animate transitions between forms.
	return (len(m.forms) - 1) * formDuration
}

// isCompact returns true when the terminal is too small for the big art.
func (m Model) isCompact() bool {
	return m.height < compactModeThreshold
}

// ── Morph engine ────────────────────────────────────────────────────────────

// advanceMorphWave performs a center-expanding wave dissolve through forms.
func (m *Model) advanceMorphWave() {
	if len(m.forms) == 0 || len(m.morphLines) == 0 {
		return
	}

	formIdx := m.morphTick / formDuration
	if formIdx >= len(m.forms)-1 {
		formIdx = len(m.forms) - 2
	}
	if formIdx < 0 {
		formIdx = 0
	}

	prevIdx := formIdx
	currIdx := formIdx + 1
	if currIdx >= len(m.forms) {
		currIdx = len(m.forms) - 1
	}

	prevForm := m.forms[prevIdx]
	currForm := m.forms[currIdx]
	tickInForm := m.morphTick % formDuration

	totalRows := len(m.morphLines)
	center := totalRows / 2
	waveReach := tickInForm

	for row := 0; row < totalRows; row++ {
		dist := row - center
		if dist < 0 {
			dist = -dist
		}

		if dist <= waveReach {
			m.morphLines[row] = blendRow(prevForm, currForm, row, tickInForm, m.rng)
		} else {
			m.morphLines[row] = scrambleRow(prevForm, row, m.rng)
		}
	}
}

// easeOutQuad accelerates quickly then decelerates: t=0→0, t=0.5→0.75, t=1→1.
func easeOutQuad(t float64) float64 {
	if t >= 1 {
		return 1
	}
	if t <= 0 {
		return 0
	}
	return 1 - (1-t)*(1-t)
}

func blendRow(prev, curr []string, row, tick int, rng *rand.Rand) string {
	if row >= len(curr) {
		return ""
	}
	target := curr[row]
	source := ""
	if row < len(prev) {
		source = prev[row]
	}

	targetRunes := []rune(target)
	sourceRunes := []rune(source)
	if len(sourceRunes) < len(targetRunes) {
		sourceRunes = append(sourceRunes, []rune(strings.Repeat(" ", len(targetRunes)-len(sourceRunes)))...)
	}
	if len(sourceRunes) > len(targetRunes) {
		sourceRunes = sourceRunes[:len(targetRunes)]
	}

	// Use formDuration-1 so the final tick reaches full progress.
	divisor := formDuration - 1
	if divisor < 1 {
		divisor = 1
	}
	progress := easeOutQuad(float64(tick) / float64(divisor))
	if progress >= 1 {
		return target
	}
	lockCount := int(progress * float64(len(targetRunes)))

	result := make([]rune, len(targetRunes))
	locked := 0
	for i, tr := range targetRunes {
		if locked < lockCount && tr != ' ' {
			result[i] = tr
			locked++
		} else if sourceRunes[i] != ' ' {
			if rng.Float64() < 0.4 {
				result[i] = scrambleChars[rng.Intn(len(scrambleChars))]
			} else {
				result[i] = sourceRunes[i]
			}
		} else {
			if rng.Float64() < 0.2 {
				result[i] = scrambleChars[rng.Intn(len(scrambleChars))]
			} else {
				result[i] = ' '
			}
		}
	}
	return string(result)
}

func scrambleRow(form []string, row int, rng *rand.Rand) string {
	if row >= len(form) {
		return ""
	}
	line := form[row]
	runes := []rune(line)
	for i := range runes {
		if runes[i] != ' ' && rng.Float64() < 0.15 {
			runes[i] = scrambleChars[rng.Intn(len(scrambleChars))]
		}
	}
	return string(runes)
}

// ── Art resolution ──────────────────────────────────────────────────────────

// artView returns the current art lines.
func (m Model) artView() []string {
	switch m.phase {
	case "crystal":
		if m.height >= 66 && m.width >= 115 {
			return rawANSLines
		}
		return rawANSISmallLines
	case "dissolve":
		return m.morphLines
	case "waiting":
		if len(m.forms) > 0 {
			return m.shimmerFinalForm(m.forms[len(m.forms)-1])
		}
		return buildFinalForm(m.artHeight(), m.isCompact())
	}
	return []string{}
}

// shimmerFinalForm adds a subtle living pulse to the cube dots in waiting phase.
func (m Model) shimmerFinalForm(lines []string) []string {
	cubeEnd, _, _ := m.artBounds(lines)
	if cubeEnd < 0 {
		cubeEnd = 0
	}
	out := make([]string, len(lines))
	copy(out, lines)
	for i := 0; i < cubeEnd && i < len(out); i++ {
		runes := []rune(out[i])
		for j := range runes {
			if runes[j] == '.' || runes[j] == ':' {
				// Two interleaved primes create a richer, less regular pattern.
				// (j*i+i+j) avoids zero-products that would flash entire rows/cols.
				if (j+i+m.pulseTick)%23 == 0 || (j*i+i+j+m.pulseTick)%41 == 0 {
					if runes[j] == '.' {
						runes[j] = ':'
					} else {
						runes[j] = '.'
					}
				}
			}
		}
		out[i] = string(runes)
	}
	return out
}

// cubeLineCount returns the number of lines in the green cube.
func (m Model) cubeLineCount() int {
	if m.isCompact() {
		return 0
	}
	return len(greenCubeLines)
}

// c4rLineCount returns the number of lines in the active C4R art.
func (m Model) c4rLineCount() int {
	if m.isCompact() {
		return len(asciiC4RLines)
	}
	return len(bigC4RLines)
}

// artBounds returns the exclusive cube end index and the [c4rStart, c4rEnd)
// range within the given (possibly padded or truncated) art lines.
func (m Model) artBounds(artLines []string) (cubeEnd, c4rStart, c4rEnd int) {
	if m.isCompact() {
		c4rLines := m.c4rLineCount()
		if len(artLines) <= c4rLines {
			return 0, 0, len(artLines)
		}
		padTop := len(artLines) - c4rLines
		return 0, padTop, padTop + c4rLines
	}

	cubeLines := m.cubeLineCount()
	c4rLines := m.c4rLineCount()
	contentLen := cubeLines + 1 + c4rLines

	if len(artLines) <= contentLen {
		// Truncated from top; content sits at the bottom of artLines.
		missing := contentLen - len(artLines)
		actualCube := cubeLines - missing
		if actualCube <= 0 {
			return 0, 0, len(artLines)
		}
		return actualCube, actualCube + 1, len(artLines)
	}

	// Padded (bottom-aligned): content sits at the bottom of artLines.
	padTop := len(artLines) - contentLen
	cubeEnd = padTop + cubeLines
	c4rStart = cubeEnd + 1
	c4rEnd = c4rStart + c4rLines
	return
}

// waitingCubeCenterY returns the absolute screen Y coordinate (0-indexed) of
// the green cube's center line as it would appear in the waiting phase with
// the current terminal dimensions. Returns -1 in compact mode (no cube).
func (m Model) waitingCubeCenterY() int {
	if m.isCompact() {
		return -1
	}

	h := m.artHeight()
	cubeLines := m.cubeLineCount()
	c4rLines := m.c4rLineCount()
	contentLen := cubeLines + 1 + c4rLines

	// Waiting-phase text layout (matches View() for phase == "waiting"):
	// tagline, motto, version, "", status, "", footer = 7 lines.
	textCount := 7
	spacerLines := 1

	// Total vertical footprint including bottom lift.
	totalContent := h + spacerLines + textCount + bottomLift
	actualArt := h
	if totalContent > m.height {
		maxArt := m.height - textCount - spacerLines - bottomLift
		if maxArt < 0 {
			maxArt = 0
		}
		if maxArt < actualArt {
			actualArt = maxArt
		}
	}

	// Screen offset of the art block.
	padTopView := m.height - actualArt - spacerLines - textCount - bottomLift
	if padTopView < 0 {
		padTopView = 0
	}

	// Cube position within the art block.
	var cubeTopInH, visibleCube int
	if h >= contentLen {
		padTopArt := h - contentLen
		cubeTopInH = padTopArt
		visibleCube = cubeLines
	} else {
		contentRemoved := contentLen - h
		cubeTopInH = 0
		visibleCube = cubeLines - contentRemoved
		if visibleCube < 0 {
			visibleCube = 0
		}
	}

	// Apply any additional truncation performed by View().
	removed := h - actualArt
	cubeTop := cubeTopInH - removed
	if cubeTop < 0 {
		visibleCube += cubeTop // cubeTop is negative here
		cubeTop = 0
	}
	if visibleCube < 0 {
		visibleCube = 0
	}

	return padTopView + cubeTop + visibleCube/2
}

// pickANSI selects the best ANSI art size for the terminal dimensions.
func (m Model) pickANSI() string {
	if m.height >= 66 && m.width >= 115 {
		return rawANSI
	}
	return rawANSISmall
}

// stripANSI removes ANSI escape sequences from a string.
func stripANSI(s string) string {
	return ansiEscapePattern.ReplaceAllString(s, "")
}

// artHeight returns the height available for art after reserving space for text.
// For non-compact terminals that are tall enough, it returns a fixed height
// algebraically chosen so the green cube center aligns with the purple crystal
// center across all splash phases (crystal → dissolve → waiting).
//
// Derivation:
//
//	crystalCenter = padTop + len(crystal)/2
//	cubeCenter    = padTop + (h - contentLen) + cubeLines/2
//	Setting them equal: h = contentLen + (len(crystal) - cubeLines) / 2
func (m Model) artHeight() int {
	if m.isCompact() {
		if m.height > artReserve {
			return m.height - artReserve
		}
		return m.height
	}

	cubeH := len(greenCubeLines)
	c4rH := len(bigC4RLines)
	contentLen := cubeH + 1 + c4rH // cube + spacer + C4R text

	bigH := contentLen + (len(rawANSLines)-cubeH)/2
	smallH := contentLen + (len(rawANSISmallLines)-cubeH)/2

	// Fixed alignment heights for terminals large enough to fit the full layout.
	if m.height >= 66 && m.width >= 115 {
		return bigH
	}
	if m.height >= 57 {
		return smallH
	}

	// Fallback for very small terminals where perfect alignment is impossible.
	if m.height > artReserve {
		return m.height - artReserve
	}
	return m.height
}

// ── Color helpers (no external deps) ────────────────────────────────────────

// hexToRGB converts a 6-digit hex color string to float64 RGB components.
// Returns white (1,1,1) on any parse failure.
func hexToRGB(hex string) (r, g, b float64) {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) != 6 {
		return 1, 1, 1
	}
	ri, err1 := strconv.ParseInt(hex[0:2], 16, 64)
	gi, err2 := strconv.ParseInt(hex[2:4], 16, 64)
	bi, err3 := strconv.ParseInt(hex[4:6], 16, 64)
	if err1 != nil || err2 != nil || err3 != nil {
		return 1, 1, 1
	}
	return float64(ri) / 255.0, float64(gi) / 255.0, float64(bi) / 255.0
}

// rgbToHex converts float64 RGB back to a zero-padded hex string.
func rgbToHex(r, g, b float64) string {
	r = math.Max(0, math.Min(1, r))
	g = math.Max(0, math.Min(1, g))
	b = math.Max(0, math.Min(1, b))
	return fmt.Sprintf("#%02x%02x%02x", int(r*255+0.5), int(g*255+0.5), int(b*255+0.5))
}

// lerpColor linearly interpolates between two hex colors.
func lerpColor(from, to string, t float64) string {
	r1, g1, b1 := hexToRGB(from)
	r2, g2, b2 := hexToRGB(to)
	r := r1 + (r2-r1)*t
	g := g1 + (g2-g1)*t
	b := b1 + (b2-b1)*t
	return rgbToHex(r, g, b)
}

// fadeColor returns dimmed color until revealAfter ticks have passed.
func (m Model) fadeColor(targetHex string, revealAfter int) string {
	if m.textTick >= revealAfter {
		return targetHex
	}
	// Blend from theme dim toward target with eased progress.
	blend := easeOutQuad(float64(m.textTick) / float64(revealAfter+1))
	return lerpColor(string(styles.ActiveTheme().Dim), targetHex, blend)
}

// ── View ────────────────────────────────────────────────────────────────────

// Pre-built style bases to avoid redundant NewStyle() allocations per frame.
var (
	boldStyleBase  = lipgloss.NewStyle().Bold(true)
	plainStyleBase = lipgloss.NewStyle()
)

// View renders the splash screen.
func (m Model) View() string {
	if m.width == 0 || m.height == 0 {
		return "Loading..."
	}

	artLines := m.artView()

	// Colorize art based on phase
	coloredArt := make([]string, 0, len(artLines))
	primaryStyle := boldStyleBase.Foreground(lipgloss.Color(styles.ActiveTheme().Primary))
	dimStyle := plainStyleBase.Foreground(lipgloss.Color(styles.ActiveTheme().Dim))
	greenStyle := plainStyleBase.Foreground(lipgloss.Color(styles.ActiveTheme().Success))

	switch m.phase {
	case "crystal":
		coloredArt = artLines
	case "dissolve":
		progress := 0.0
		if total := m.totalMorphTicks(); total > 0 {
			progress = easeOutQuad(float64(m.morphTick) / float64(total))
		}
		midHex := lerpColor(string(styles.ActiveTheme().Primary), string(styles.ActiveTheme().Success), progress)
		midStyle := plainStyleBase.Foreground(lipgloss.Color(midHex))
		for _, line := range artLines {
			coloredArt = append(coloredArt, midStyle.Render(line))
		}
	case "waiting":
		cubeEnd, c4rStart, c4rEnd := m.artBounds(artLines)
		for i, line := range artLines {
			switch {
			case i < cubeEnd:
				coloredArt = append(coloredArt, greenStyle.Render(line))
			case i >= c4rStart && i < c4rEnd && strings.TrimSpace(line) != "":
				coloredArt = append(coloredArt, primaryStyle.Render(line))
			default:
				coloredArt = append(coloredArt, dimStyle.Render(line))
			}
		}
	}

	// ── Text elements with progressive fade-in ──────────────────────────────
	textLines := make([]string, 0, 6)

	tagline := boldStyleBase.
		Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Primary), 0))).
		Render("COGNITIVE EXOSKELETON FOR AI-AGENTS AND HUMANS")
	textLines = append(textLines, tagline)

	// Motto — visible in dissolve & waiting
	if m.phase != "crystal" {
		d := plainStyleBase.Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Purple), 3))).Render("Discover.")
		i := plainStyleBase.Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Yellow), 3))).Render("Invent.")
		s := plainStyleBase.Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Red), 3))).Render("Shift paradigms.")
		motto := lipgloss.JoinHorizontal(lipgloss.Center, d, " ", i, " ", s)
		textLines = append(textLines, motto)
	}

	version := plainStyleBase.
		Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Dim), 5))).
		Render("C4REQBER " + AppVersion)
	textLines = append(textLines, version)

	// Status & footer
	var status, footer string
	switch m.phase {
	case "crystal":
		spinnerView := m.spinner.View()
		status = plainStyleBase.Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Dim), 6))).Render(spinnerView + " initializing cognitive exoskeleton...")
		if m.textTick < 5 {
			footer = plainStyleBase.Foreground(lipgloss.Color(styles.ActiveTheme().Dim)).Render("press any key to skip »")
		}
	case "dissolve":
		spinnerView := m.spinner.View()
		status = plainStyleBase.Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Yellow), 6))).Render(spinnerView + " Transmuting...")
	case "waiting":
		status = plainStyleBase.Foreground(lipgloss.Color(m.fadeColor(string(styles.ActiveTheme().Success), 6))).Render("✓ Ready")
		footer = boldStyleBase.Foreground(lipgloss.Color(styles.ActiveTheme().Primary)).Render("► press Enter to continue ◄")
	}

	if status != "" {
		textLines = append(textLines, "", status)
	}
	if footer != "" {
		textLines = append(textLines, "", footer)
	}

	// In dissolve/waiting, insert a blank line between art and text for visual
	// breathing room. Crystal keeps art and text flush.
	spacerLines := 0
	if m.phase != "crystal" {
		spacerLines = 1
	}

	textCount := len(textLines)
	padTop := 0

	if m.phase == "crystal" {
		// Align purple crystal center with green cube center in waiting phase.
		targetCenter := m.waitingCubeCenterY()
		total := len(coloredArt) + textCount
		if targetCenter >= 0 {
			crystalCenter := len(artLines) / 2
			padTop = targetCenter - crystalCenter
		} else {
			// Compact mode — center the whole block.
			padTop = (m.height - total) / 2
		}
		if padTop < 0 {
			padTop = 0
		}

		// Push tagline down to the same fixed row used in waiting phase
		// without moving the crystal (add spacer lines between art and text).
		actualTaglineY := padTop + len(coloredArt)
		const waitingTextCount = 7
		targetTaglineY := m.height - waitingTextCount - bottomLift
		if targetTaglineY < 0 {
			targetTaglineY = 0
		}
		if actualTaglineY < targetTaglineY {
			spacerLines = targetTaglineY - actualTaglineY
		}

		// Recalculate total with the new spacer.
		total = len(coloredArt) + spacerLines + textCount
		if padTop+total > m.height {
			padTop = (m.height - total) / 2
			if padTop < 0 {
				padTop = 0
			}
		}
		if padTop+total > m.height && len(coloredArt) > 0 {
			maxArt := m.height - textCount - spacerLines - padTop
			if maxArt < 0 {
				maxArt = 0
				padTop = 0
			}
			if maxArt < len(coloredArt) {
				coloredArt = coloredArt[len(coloredArt)-maxArt:]
			}
		}
	} else {
		// Fixed tagline row — the same absolute screen position as in waiting phase.
		// Waiting-phase text: tagline + motto + version + "" + status + "" + footer = 7 lines.
		const waitingTextCount = 7
		targetTaglineY := m.height - waitingTextCount - bottomLift
		if targetTaglineY < 0 {
			targetTaglineY = 0
		}

		// Position art so the first text line (tagline) lands on targetTaglineY.
		padTop = targetTaglineY - len(coloredArt) - spacerLines
		if padTop < 0 {
			padTop = 0
		}

		// Ensure everything fits; truncate art from top if necessary.
		totalLines := len(coloredArt) + spacerLines + textCount
		if padTop+totalLines > m.height && len(coloredArt) > 0 {
			maxArt := m.height - textCount - spacerLines - padTop
			if maxArt < 0 {
				maxArt = 0
				padTop = 0
			}
			if maxArt < len(coloredArt) {
				coloredArt = coloredArt[len(coloredArt)-maxArt:]
			}
			// Recompute padTop after truncation to keep tagline as close to target as possible.
			padTop = targetTaglineY - len(coloredArt) - spacerLines
			if padTop < 0 {
				padTop = 0
			}
		}
	}

	output := make([]string, 0, padTop+len(coloredArt)+spacerLines+len(textLines))
	for i := 0; i < padTop; i++ {
		output = append(output, "")
	}

	// Compute a single horizontal offset for art so the block stays aligned.
	maxArtWidth := 0
	for _, line := range coloredArt {
		if w := lipgloss.Width(line); w > maxArtWidth {
			maxArtWidth = w
		}
	}
	artPadLeft := 0
	if maxArtWidth < m.width {
		artPadLeft = (m.width - maxArtWidth) / 2
	}

	artPad := strings.Repeat(" ", artPadLeft)
	for _, line := range coloredArt {
		output = append(output, artPad+line)
	}
	for i := 0; i < spacerLines; i++ {
		output = append(output, "")
	}
	centerStyle := plainStyleBase.Width(m.width).Align(lipgloss.Center)
	for _, line := range textLines {
		output = append(output, centerStyle.Render(line))
	}
	return strings.Join(output, "\n")
}

// LoadingDone reports whether the splash sequence has completed.
func (m Model) LoadingDone() bool {
	return m.loadingDone
}

// ── Message types & commands ────────────────────────────────────────────────

type startDissolveMsg struct{}
type dissolveTickMsg struct{ tick int }
type textFadeTickMsg struct{}
type cubePulseMsg struct{}

// maxTextFadeTick is the highest textTick we need before every element
// has reached full brightness.  After this the ticker stops.
const maxTextFadeTick = 10

func dissolveTickCmd(tick int) tea.Cmd {
	return tea.Tick(tickInterval, func(_ time.Time) tea.Msg {
		return dissolveTickMsg{tick: tick}
	})
}

func textFadeTickCmd() tea.Cmd {
	return tea.Tick(textFadeInterval, func(_ time.Time) tea.Msg {
		return textFadeTickMsg{}
	})
}

func cubePulseCmd() tea.Cmd {
	return tea.Tick(pulseInterval, func(_ time.Time) tea.Msg {
		return cubePulseMsg{}
	})
}
