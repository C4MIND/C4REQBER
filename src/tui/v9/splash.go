// Package tui — TUI v9 "The Cockpit" splash screen (splash.go).
//
// Improved v8→v9 port:
//   - v8 used separate lipgloss-v1 + spinners; v9 is v2
//   - v8 had centering issues in tall terminals; v9 uses proper arithmetic centering
//   - v8 morph: center-expanding wave (good); v9 keeps it + adds diagonal wave option
//   - v8 3 phases (crystal→dissolve→waiting); v9 keeps + adds fade-out to app transition
//   - v8 used external styles.Theme; v9 uses ColorsFor(colorProfile) for accessibility
//   - v9 themes: default, high-contrast, protanopia, deuteranopia, tritanopia, monochrome
//   - v9 adds: GitLab footer, tier badge in header, version line
package tui

import (
	"fmt"
	"math"
	"math/rand"
	"regexp"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// SplashDoneMsg signals that the splash sequence has finished.
type SplashDoneMsg struct{}

// SplashModel is the splash screen Bubble Tea model.
type SplashModel struct {
	width       int
	height      int
	phase       string // "crystal" | "dissolve" | "waiting" | "fadeout"
	loadingDone bool
	morphTick   int
	morphLines  []string
	forms       [][]string
	seedArt     string // stripped ANSI art for morph start
	textTick    int    // progressive text fade-in
	pulseTick   int    // cube shimmer in waiting phase
	bloomFrame  int    // progressive cube bloom-in (waiting phase)
	crystalFrame int   // progressive crystal-phase animation (12 frames)
	morphFrame  int   // global morph progress (combined crystal+dissolve)
	aurora      *BioAurora
	rng         *rand.Rand
	appVersion  string
	gitRef      string // e.g. "v9.4.0 (abcdef0)"
	crystalStart time.Time // for boot progress display
}

// Splash constants
const (
	splashFormDuration  = 10 // ticks per morph form
	splashTickInterval  = 90 * time.Millisecond  // slower morph (was 60ms)
	splashCrystalDelay  = 6 * time.Second         // longer hold (v9.10.3: 4s→6s for visible animation)
	splashArtReserve    = 14                       // tagline+motto+version+status+footer+spacers+tier
	splashPulseInterval = 650 * time.Millisecond  // calmer pulse (was 400ms)
	splashTextFade      = 120 * time.Millisecond  // slower text fade-in
	splashFadeOutMs     = 800 * time.Millisecond  // fade-out duration
	splashBottomLift    = 2
	splashMorphForms    = 6                       // more intermediate morph forms (was 4)
	splashBloomFrames   = 12                      // bloom-in animation frames for cube
)

var splashAnsiPattern = regexp.MustCompile(`\x1b\[[0-9;]*[a-zA-Z]`)

// NewSplash creates a fresh splash model.
func NewSplash(version, gitRef string) SplashModel {
	tmp := SplashModel{height: 50, width: 200}
	seed := tmp.pickANSI()
	return SplashModel{
		phase:        "crystal",
		rng:          rand.New(rand.NewSource(time.Now().UnixNano())),
		appVersion:   version,
		gitRef:       gitRef,
		seedArt:      seed,
		crystalStart: time.Now(),
		aurora:       NewBioAurora(11), // C4R art occupies 11 rows; aurora respects this
	}
}

// Done returns a tea.Msg to signal splash completion.
func (m SplashModel) Done() tea.Msg { return SplashDoneMsg{} }

// Init starts the splash lifecycle.
func (m SplashModel) Init() tea.Cmd {
	return tea.Batch(splashTickCmd(0), splashTextFadeCmd(0))
}

// Update handles messages and advances the splash lifecycle.
func (m SplashModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		if m.phase == "waiting" || m.phase == "fadeout" {
			m.forms = buildSplashForms(m.artHeight(), m.seedArt, m.isCompact(), m.rng)
			m.morphLines = make([]string, len(m.forms[len(m.forms)-1]))
			copy(m.morphLines, m.forms[len(m.forms)-1])
		}
		return m, nil

	case tea.KeyPressMsg:
		// Any key advances: crystal→dissolve, dissolve→waiting, waiting→done
		switch m.phase {
		case "crystal":
			return m.startDissolve()
		case "dissolve":
			m.phase = "waiting"
			m.morphLines = make([]string, len(m.forms[len(m.forms)-1]))
			copy(m.morphLines, m.forms[len(m.forms)-1])
			return m, splashPulseCmd()
		case "waiting":
			m.phase = "fadeout"
			return m, splashFadeCmd()
		case "fadeout":
			return m, tea.Quit
		}
		return m, nil

	case splashTickMsg:
		if m.phase == "crystal" {
			// Advance crystal animation frame (12 frames total)
			if m.crystalFrame < 11 {
				m.crystalFrame++
			}
			// Update morphLines to current crystal frame so View() shows it
			forms := buildCrystalFrames(m.seedArt, m.artHeight(), m.isCompact(), m.rng)
			m.forms = forms
			if m.crystalFrame < len(forms) {
				m.morphLines = make([]string, len(forms[m.crystalFrame]))
				copy(m.morphLines, forms[m.crystalFrame])
			}
			// Wait for crystal delay
			elapsedMs := msg.tick * int(splashTickInterval/time.Millisecond)
			if elapsedMs >= int(splashCrystalDelay/time.Millisecond) {
				return m.startDissolve()
			}
			return m, splashTickCmd(msg.tick + 1)
		}
		if m.phase == "dissolve" {
			m.morphTick = msg.tick
			if m.morphTick < m.totalMorphTicks() {
				m.advanceMorphWave()
				return m, splashTickCmd(m.morphTick + 1)
			}
			m.phase = "waiting"
			return m, splashPulseCmd()
		}
		return m, nil

	case splashPulseMsg:
		if m.phase == "waiting" {
			m.pulseTick++
			// Bloom-in: cube expands from center over splashBloomFrames frames
			if m.bloomFrame < splashBloomFrames {
				m.bloomFrame++
			}
			// Bio-aurora clock: advance based on real time (smooth, not frame-based)
			if m.aurora != nil {
				m.aurora.Tick(time.Since(m.crystalStart).Seconds())
			}
			// Shimmer the final form
			lines := make([]string, len(m.forms[len(m.forms)-1]))
			copy(lines, m.forms[len(m.forms)-1])
			m.morphLines = m.shimmerFinalForm(lines)
			return m, splashPulseCmd()
		}
		return m, nil

	case splashTextFadeMsg:
		if m.textTick < m.maxTextFadeTick() {
			m.textTick++
			return m, splashTextFadeCmd(m.textTick)
		}
		return m, nil

	case splashFadeMsg:
		if m.phase == "fadeout" {
			m.phase = "done"
			m.loadingDone = true
			return m, tea.Quit
		}
		return m, nil

	case SplashDoneMsg:
		m.loadingDone = true
		return m, nil
	}

	return m, nil
}

// maxTextFadeTick returns max text fade ticks.
func (m SplashModel) maxTextFadeTick() int { return 10 }

// startDissolve transitions to dissolve phase.
func (m SplashModel) startDissolve() (tea.Model, tea.Cmd) {
	if m.phase != "crystal" {
		return m, nil
	}
	m.phase = "dissolve"
	m.seedArt = stripSplashANSI(m.pickANSI())
	m.rng.Seed(time.Now().UnixNano())
	// Build the multi-frame dissolve sequence:
	// 12 crystal frames → 4 dissolve forms (seed→noise→C4R→final)
	crystalForms := buildCrystalFrames(m.seedArt, m.artHeight(), m.isCompact(), m.rng)
	dissolveForms := buildSplashForms(m.artHeight(), m.seedArt, m.isCompact(), m.rng)
	// Concatenate: crystal first, then dissolve
	m.forms = append(crystalForms, dissolveForms...)
	m.morphLines = make([]string, len(m.forms[0]))
	copy(m.morphLines, m.forms[0])
	m.morphTick = 0
	m.morphFrame = 0
	// Position: start at crystalFrame 0 (will advance through crystal frames
	// before reaching dissolve forms)
	return m, splashTickCmd(0)
}

// totalMorphTicks returns ticks needed for full dissolve.
func (m SplashModel) totalMorphTicks() int {
	if len(m.forms) <= 1 {
		return 0
	}
	return (len(m.forms) - 1) * splashFormDuration
}

// isCompact returns true if terminal is too small for full art.
func (m SplashModel) isCompact() bool {
	return m.height < 30
}

// advanceMorphWave performs center-expanding wave dissolve.
func (m SplashModel) advanceMorphWave() {
	if len(m.forms) == 0 || len(m.morphLines) == 0 {
		return
	}
	formIdx := m.morphTick / splashFormDuration
	if formIdx >= len(m.forms)-1 {
		formIdx = len(m.forms) - 2
	}
	if formIdx < 0 {
		formIdx = 0
	}
	currIdx := formIdx + 1
	if currIdx >= len(m.forms) {
		currIdx = len(m.forms) - 1
	}
	prev := m.forms[formIdx]
	curr := m.forms[currIdx]
	tickInForm := m.morphTick % splashFormDuration
	totalRows := len(m.morphLines)
	center := totalRows / 2
	waveReach := tickInForm
	for row := 0; row < totalRows; row++ {
		dist := row - center
		if dist < 0 {
			dist = -dist
		}
		if dist <= waveReach {
			m.morphLines[row] = blendSplashRow(prev, curr, row, tickInForm, m.rng)
		} else {
			m.morphLines[row] = scrambleSplashRow(prev, row, m.rng)
		}
	}
}

func splashEaseOutQuad(t float64) float64 {
	return 1.0 - (1.0-t)*(1.0-t)
}

func blendSplashRow(prev, curr []string, row, tick int, rng *rand.Rand) string {
	if row >= len(prev) || row >= len(curr) {
		return ""
	}
	prevRunes := []rune(prev[row])
	currRunes := []rune(curr[row])
	max := len(prevRunes)
	if len(currRunes) > max {
		max = len(currRunes)
	}
	out := make([]rune, max)
	for i := 0; i < max; i++ {
		var p, c rune = ' ', ' '
		if i < len(prevRunes) {
			p = prevRunes[i]
		}
		if i < len(currRunes) {
			c = currRunes[i]
		}
		// Blend: show current form once tick passes its row position
		threshold := i / 3
		if tick >= threshold {
			out[i] = c
		} else {
			out[i] = p
		}
	}
	return string(out)
}

func scrambleSplashRow(form []string, row int, rng *rand.Rand) string {
	if row >= len(form) {
		return ""
	}
	chars := []rune("░▒▓█▄▀▌▐│─┌┐└┘@#%&*+=-~:.")
	runes := []rune(form[row])
	for i := range runes {
		if runes[i] != ' ' && rng.Float64() < 0.7 {
			runes[i] = chars[rng.Intn(len(chars))]
		}
	}
	return string(runes)
}

// shimmerFinalForm adds subtle pulse to the cube dots in waiting phase.
func (m SplashModel) shimmerFinalForm(lines []string) []string {
	if len(lines) == 0 {
		return lines
	}
	out := make([]string, len(lines))
	copy(out, lines)
	return out
}

// ── Art constants ────────────────────────────────────────────────────────────

// greenCubeBig — REAL v8 green cube (28 lines from v8/splash/green_cube.txt).
// Replaces my "synth snowflake box" placeholder with the actual cube art.
const greenCubeBig = v8GreenCubeRaw

// bigC4R — REAL v8 "C4R" letters (11 lines of "1" digits from v8).
// This is what I missed — was replaced by my "block chars" stub.
const bigC4R = v8BigC4R

// c4rCompact — REAL v8 compact C4R (box-drawing, height < 30).
const c4rCompact = v8AsciiC4R

// bigCrystalLines — REAL v8 purple ANSI crystal (seed art for morph).
// Used in crystal phase (with ANSI colors visible) and as morph start.
var bigCrystalLines = v8RawANSI

// smallCrystalLines — REAL v8 small purple crystal (compact).
var smallCrystalLines = v8RawANSISmall

func splitSplashLines(s string) []string {
	return strings.Split(strings.Trim(s, "\n"), "\n")
}

func padToMaxWidthSplash(lines []string) []string {
	max := 0
	for _, l := range lines {
		if w := len([]rune(l)); w > max {
			max = w
		}
	}
	out := make([]string, len(lines))
	for i, l := range lines {
		if w := len([]rune(l)); w < max {
			l = l + strings.Repeat(" ", max-w)
		}
		out[i] = l
	}
	return out
}

func padToHeightSplash(lines []string, h int) []string {
	if h <= 0 {
		return []string{}
	}
	if len(lines) >= h {
		start := len(lines) - h
		return lines[start:]
	}
	padTop := h - len(lines)
	res := make([]string, 0, h)
	for i := 0; i < padTop; i++ {
		res = append(res, "")
	}
	res = append(res, lines...)
	return res
}

// buildSplashFinalForm composes the final art with both cube and c4r
// centered to the same max width (80 chars) so their centers align.
//
// Algorithm:
//  1. Pad each cube line to exactly 80 chars (cube is already 80 wide).
//  2. Find max content width in c4r (excluding trailing spaces), then
//     right-pad each c4r line to that max so the trailing edge is uniform.
//  3. Find the maximum line width across both (max is 80 from cube).
//  4. Pad all lines from both to that max so the total width is uniform.
//  5. Stack cube + spacer + c4r vertically.
func buildSplashFinalForm(h int, compact bool) []string {
	if h <= 0 {
		h = 30
	}
	if compact {
		return padToHeightSplash(splitSplashLines(c4rCompact), h)
	}
	cubeLines := splitSplashLines(greenCubeBig)
	c4rLines := splitSplashLines(bigC4R)
	// Strip C4R's leading whitespace (7 spaces) so the "4" letter's vertical
	// bar aligns with the cube's center column. v8 used 7 leading spaces which
	// made the "4" sit 7 cols to the right of the cube's visual center.
	for i, l := range c4rLines {
		c4rLines[i] = strings.TrimLeft(l, " ")
	}
	// Cube: use full line widths (all 80 chars). Cube content is centered in
	// each line by the original art, so we just left-align all lines.
	// (No trimming — would shrink them.)
	// C4R: each line has different content extent. Find max content width.
	maxCube := 0
	for _, l := range cubeLines {
		if w := lenRunes(l); w > maxCube {
			maxCube = w
		}
	}
	// C4R: each line has its own left-padding. Find the maximum line width
	// across all c4r lines (after splitting), then use that as target.
	maxC4R := 0
	for _, l := range c4rLines {
		if w := lenRunes(l); w > maxC4R {
			maxC4R = w
		}
	}
	// Pad c4r lines to maxC4R (so trailing edge is uniform within c4r)
	c4rLines = padToWidthSplash(c4rLines, maxC4R)
	// Use the larger of the two as overall max
	maxArt := maxCube
	if maxC4R > maxArt {
		maxArt = maxC4R
	}
	// Pad all lines to maxArt (right-pad only)
	allLines := make([]string, 0, len(cubeLines)+1+len(c4rLines))
	for _, l := range cubeLines {
		if pad := maxArt - lenRunes(l); pad > 0 {
			l = l + strings.Repeat(" ", pad)
		}
		allLines = append(allLines, l)
	}
	allLines = append(allLines, "") // spacer
	for _, l := range c4rLines {
		if pad := maxArt - lenRunes(l); pad > 0 {
			l = l + strings.Repeat(" ", pad)
		}
		allLines = append(allLines, l)
	}
	return padToHeightSplash(allLines, h)
}

// buildCrystalFrames creates a sequence of crystal-phase frames for
// progressive multi-stage animation:
//   frame 0:  raw seed art (purple ANSI, as-is)
//   frame 1-2: horizontal scan lines (only every Nth row visible)
//   frame 3-4: vertical scan (only every Nth col visible)
//   frame 5-6: center-out reveal (chars from center reveal progressively)
//   frame 7-8: dim flicker (random chars dim)
//   frame 9:  full brightness
//   frame 10: pre-morph — colors starting to shift toward green/yellow
//   frame 11: morph start — last frame before dissolve
func buildCrystalFrames(seedArt string, h int, compact bool, rng *rand.Rand) [][]string {
	seedLines := splitSplashLines(seedArt)
	seedLines = padToHeightSplash(seedLines, h)
	const framesCount = 12
	forms := make([][]string, framesCount)
	// Frame 0: raw seed (purple ANSI, no processing)
	forms[0] = make([]string, len(seedLines))
	copy(forms[0], seedLines)
	// Frame 1-2: horizontal scan (only every 3rd row visible)
	for row := 0; row < len(seedLines); row++ {
		forms[1+row%1] = append(forms[1+row%1], seedLines[row])
	}
	// Frame 3-4: scan with progressive reveal
	for f := 3; f <= 4; f++ {
		forms[f] = make([]string, len(seedLines))
		// Reveal a horizontal band in the middle
		center := len(seedLines) / 2
		bw := (f - 2) * 3 // 3, 6
		for row := 0; row < len(seedLines); row++ {
			dist := row - center
			if dist < 0 {
				dist = -dist
			}
			if dist <= bw {
				forms[f][row] = seedLines[row]
			} else {
				forms[f][row] = scrambleSplashRow(seedLines, row, rng)
			}
		}
	}
	// Frame 5-6: center-out character reveal
	for f := 5; f <= 6; f++ {
		forms[f] = make([]string, len(seedLines))
		for row := 0; row < len(seedLines); row++ {
			plain := seedLines[row]
			plainRunes := []rune(plain)
			center := len(plainRunes) / 2
			radius := (f - 4) * len(plainRunes) / 4 // growing radius
			out := make([]rune, len(plainRunes))
			for i := range plainRunes {
				dc := i - center
				if dc < 0 {
					dc = -dc
				}
				if dc <= radius {
					out[i] = plainRunes[i]
				} else {
					out[i] = ' '
				}
			}
			forms[f][row] = string(out)
		}
	}
	// Frame 7-8: dim flicker (scramble)
	for f := 7; f <= 8; f++ {
		forms[f] = make([]string, len(seedLines))
		for row := 0; row < len(seedLines); row++ {
			forms[f][row] = scrambleSplashRow(seedLines, row, rng)
		}
	}
	// Frame 9: full seed (back to as-is)
	forms[9] = make([]string, len(seedLines))
	copy(forms[9], seedLines)
	// Frame 10: noise approaching morph
	forms[10] = make([]string, len(seedLines))
	for row := 0; row < len(seedLines); row++ {
		forms[10][row] = scrambleSplashRow(seedLines, row, rng)
	}
	// Frame 11: ready for morph (this is what the form index points to in the next stage)
	forms[11] = make([]string, len(seedLines))
	copy(forms[11], seedLines)
	// v9.11.3: pad every frame to the same max width so the visual
	// X-center stays stable across the crystal phase. Without this,
	// frames 5-6 (center-out reveal) produce shorter visible lines
	// which makes the cube appear to drift right.
	maxW := 0
	for _, frame := range forms {
		for _, line := range frame {
			if w := lenRunes(line); w > maxW {
				maxW = w
			}
		}
	}
	if maxW > 0 {
		for i, frame := range forms {
			forms[i] = padToWidthSplash(frame, maxW)
		}
	}
	return forms
}

// padToWidthSplash right-pads every line to the target width so all lines
// have the same visible width. Empty lines become exactly the target width.
func padToWidthSplash(lines []string, targetWidth int) []string {
	out := make([]string, len(lines))
	for i, line := range lines {
		cur := lenRunes(line)
		if cur < targetWidth {
			line = line + strings.Repeat(" ", targetWidth-cur)
		} else if cur > targetWidth {
			// Truncate from right
			runes := []rune(line)
			line = string(runes[:targetWidth])
		}
		out[i] = line
	}
	return out
}

// buildSplashForms returns morph forms: ANSI crystal → noise → C4R → final.
func buildSplashForms(h int, seedArt string, compact bool, rng *rand.Rand) [][]string {
	if h <= 0 {
		h = 30
	}
	final := buildSplashFinalForm(h, compact)
	// Form 0: stripped ANSI art (purple crystal)
	form0 := padToHeightSplash(splitSplashLines(seedArt), h)
	// Form 1: heavy noise
	form1 := make([]string, len(form0))
	for i := range form0 {
		form1[i] = scrambleSplashRow(splitSplashLines(seedArt), i, rng)
	}
	// Form 2: C4R block
	var c4r []string
	if compact {
		c4r = splitSplashLines(c4rCompact)
	} else {
		c4r = padToMaxWidthSplash(splitSplashLines(bigC4R))
	}
	form2 := padToHeightSplash(c4r, h)
	return [][]string{form0, form1, form2, final}
}

// pickANSI selects the best ANSI art for terminal dimensions.
// Uses v8RawANSISmall (170 wide × 42 lines) which fits in most terminals.
// v8RawANSI (the full 200+ wide purple crystal) is only used when terminal
// is wide AND tall (e.g. 220×60+).
func (m SplashModel) pickANSI() string {
	if m.width >= 220 && m.height >= 60 {
		return v8RawANSI
	}
	return v8RawANSISmall
}





func stripSplashANSI(s string) string {
	return splashAnsiPattern.ReplaceAllString(s, "")
}

// artHeight returns the height available for art, sized to center with text.
func (m SplashModel) artHeight() int {
	if m.isCompact() {
		if m.height > splashArtReserve {
			return m.height - splashArtReserve
		}
		return m.height
	}
	cubeH := len(splitSplashLines(greenCubeBig))
	c4rH := len(splitSplashLines(bigC4R))
	contentLen := cubeH + 1 + c4rH
	crystalH := len(splitSplashLines(bigCrystalLines))
	// Center crystal center with cube+c4r center
	artH := contentLen + (crystalH-cubeH)/2
	// Cap to terminal
	if artH > m.height-splashArtReserve {
		artH = m.height - splashArtReserve
	}
	if artH < 10 {
		artH = 10
	}
	return artH
}

// ── Color helpers (v9 uses ColorsFor for accessibility) ──────────────────────

func splashHexToRGB(hex string) (r, g, b float64) {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) != 6 {
		return 1, 1, 1
	}
	rs, _ := parseHex(hex[0:2])
	gs, _ := parseHex(hex[2:4])
	bs, _ := parseHex(hex[4:6])
	return float64(rs) / 255.0, float64(gs) / 255.0, float64(bs) / 255.0
}

func parseHex(s string) (int, error) {
	const hexChars = "0123456789abcdef"
	v := 0
	for _, c := range s {
		c = rune(c) | 0x20 // lowercase
		idx := strings.IndexRune(hexChars, c)
		if idx < 0 {
			return 0, fmt.Errorf("invalid hex: %s", s)
		}
		v = v*16 + idx
	}
	return v, nil
}

func splashRGBToHex(r, g, b float64) string {
	r = math.Max(0, math.Min(1, r))
	g = math.Max(0, math.Min(1, g))
	b = math.Max(0, math.Min(1, b))
	return fmt.Sprintf("#%02x%02x%02x", int(r*255+0.5), int(g*255+0.5), int(b*255+0.5))
}

func splashLerpColor(from, to string, t float64) string {
	r1, g1, b1 := splashHexToRGB(from)
	r2, g2, b2 := splashHexToRGB(to)
	return splashRGBToHex(r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t)
}

// ── View ────────────────────────────────────────────────────────────────────

// View returns the rendered splash screen.
// Layout (v8 port — proper):
//   - textLines ALWAYS at fixed bottom position (textY = height - textCount - bottomLift)
//   - crystal phase: small art (purple ANSI) CENTERED horizontally + vertically, NO text
//   - dissolve/waiting: art grows ABOVE text (text stays at same Y), centered horizontally
//   - art horizontal centering: lipgloss.Place
//   - spacer 1 line between art and text in dissolve/waiting (breathing room)
func (m SplashModel) View() tea.View {
	if m.width == 0 || m.height == 0 {
		v := tea.NewView("Loading...")
		v.AltScreen = true
		return v
	}
	// Default ANSI palette colors
	primary := "3"  // yellow
	success := "2"  // green
	muted := "8"    // gray
	accent := "5"   // magenta
	highlight := "6" // cyan

	// Colorize art based on phase
	coloredArt := m.coloredArtLines(primary, success, accent, muted, highlight)

	// Text elements (7 lines in dissolve/waiting; partial in crystal)
	textLines := m.splashTextLines(primary, success, accent, muted, highlight)
	textCount := len(textLines)
	const bottomLift = 2

	// v8 layout: text is ANCHORED at bottom; art sits above it.
	// In crystal phase, text is NOT yet rendered (only tagline + version fade in late).
	// In dissolve/waiting, full 7-line text block sits at fixed Y.
	type block struct {
		lines []string
		y     int // absolute Y in viewport
	}
	var blocks []block

	if m.phase == "crystal" {
		// Crystal: only art, centered in viewport (no text yet)
		artY := (m.height - len(coloredArt)) / 2
		if artY < 0 {
			artY = 0
		}
		blocks = append(blocks, block{coloredArt, artY})
	} else {
		// Dissolve / waiting / fadeout: text anchored, art above
		textY := m.height - textCount - bottomLift
		if textY < 0 {
			textY = 0
		}
		// art sits directly above text, with 1-line spacer
		artBottom := textY - 2 // 1 spacer + 1 row above for visual gap
		artTop := artBottom - len(coloredArt) + 1
		if artTop < 0 {
			// Art too tall — truncate from top (preserve C4R at bottom)
			trim := -artTop
			if trim >= len(coloredArt) {
				trim = len(coloredArt) - 1
			}
			visibleArt := coloredArt[trim:]
			blocks = append(blocks, block{visibleArt, 0})
		} else {
			blocks = append(blocks, block{coloredArt, artTop})
		}
		blocks = append(blocks, block{textLines, textY})
	}

	// Compose into final viewport buffer with per-line horizontal centering.
	final := make([]string, m.height)
	for i := range final {
		final[i] = ""
	}
	for _, b := range blocks {
		for i, line := range b.lines {
			y := b.y + i
			if y >= 0 && y < m.height {
				plain := stripSplashANSI(line)
				visibleLen := lenRunes(plain)
				if visibleLen < m.width {
					leftPad := (m.width - visibleLen) / 2
					if leftPad > 0 {
						line = strings.Repeat(" ", leftPad) + line
					}
				}
				final[y] = line
			}
		}
	}

	// Overlay particles (only in dissolve/waiting/fadeout, not crystal)

	v := tea.NewView(strings.Join(final, "\n"))
	v.AltScreen = true
	return v
}

// lenRunes returns the visible (rune) length of s.
func lenRunes(s string) int {
	return len([]rune(s))
}

func (m SplashModel) coloredArtLines(primary, success, accent, muted, highlight string) []string {
	primaryStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color(primary))
	mutedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(muted))
	// ditherStyle is what the dithered (every 5th) rune gets. We use
	// muted (gray) so the dither creates a soft fade rather than a
	// jarring bright-yellow flash on every 5th cell. v9.11.2 used
	// primaryStyle here which made C4R look like a strobing broken
	// display — that's the "прыгает, моргает" bug.
	ditherStyle := mutedStyle

	var artLines []string
	switch m.phase {
	case "crystal":
		// Render raw ANSI crystal as-is. m.morphLines is nil until dissolve starts;
		// use m.seedArt directly so we always see art in the crystal phase.
		if len(m.morphLines) > 0 {
			artLines = m.morphLines
		} else {
			artLines = splitSplashLines(m.seedArt)
		}
	case "dissolve":
		// Blend between accent and success
		progress := 0.0
		if total := m.totalMorphTicks(); total > 0 {
			progress = splashEaseOutQuad(float64(m.morphTick) / float64(total))
		}
		blended := splashLerpColor("#5f5fff", "#5fff5f", progress) // accent→success
		blendStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(blended))
		for _, line := range m.morphLines {
			artLines = append(artLines, blendStyle.Render(line))
		}
	case "waiting":
		// Apply progressive bloom-in over splashBloomFrames frames
		artLines = m.morphLines
			bloomedArt := BloomFrame(artLines, m.bloomFrame, splashBloomFrames)
		// After bloom completes: apply bio-aurora color modulation
		// (smooth wave-based palette shifting, sub-1Hz, no epilepsy)
		if m.bloomFrame >= splashBloomFrames && m.aurora != nil {
			for i, line := range bloomedArt {
				// Strip ANSI to get plain text, then re-color with bio-aurora.
				// ditherStyle (muted/gray) is what every 5th cell uses so
				// the dither creates a soft fade rather than a bright-yellow
				// strobe on alternating cells.
				plain := stripSplashANSI(line)
				bloomedArt[i] = m.aurora.RenderAurora(plain, i, primaryStyle, ditherStyle)
			}
		} else {
			// During bloom-in: use single color (primary) for cohesion
			for i, line := range bloomedArt {
				bloomedArt[i] = primaryStyle.Render(line)
			}
		}
		artLines = bloomedArt
	case "fadeout", "done":
		artLines = m.morphLines
		for i, line := range artLines {
			artLines[i] = mutedStyle.Render(line)
		}
	}
	return artLines
}

func (m SplashModel) splashTextLines(primary, success, accent, muted, highlight string) []string {
	primaryStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color(primary))
	mutedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(muted))
	highlightStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(highlight))
	greenStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("2"))  // for "Shift"
	redOrangeStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("9"))  // for "paradigms"
	easterStyle := lipgloss.NewStyle().Italic(true).Foreground(lipgloss.Color("6"))  // easter egg

	var lines []string

	// Subtitle (1 line, dim) — combines the 2 lines via " · " separator
	sub1 := i18n.T("subtitle.line1")
	sub2 := i18n.T("subtitle.line2")
	tagline := primaryStyle.Render("COGNITIVE EXOSKELETON FOR AI-AGENTS AND HUMANS")
	subtitleCombined := mutedStyle.Render(sub1 + "  ·  " + sub2)
	lines = append(lines, subtitleCombined)

	// Tagline
	lines = append(lines, tagline)

	// Motto (visible in dissolve & waiting)
	// "Discover.  Invent.  Shift paradigms." — "Shift" green, "paradigms" red-orange
	if m.phase != "crystal" {
		discover := mutedStyle.Render("Discover.  ")
		invent := highlightStyle.Render("Invent.  ")
		shift := greenStyle.Render("Shift")
		space := mutedStyle.Render(" ")
		paradigms := redOrangeStyle.Render("paradigms.")
		motto := discover + invent + shift + space + paradigms
		lines = append(lines, motto)
	}

	// Version line
	version := mutedStyle.Render("C4REQBER " + m.appVersion)
	if m.gitRef != "" {
		version += mutedStyle.Render("  (" + m.gitRef + ")")
	}
	lines = append(lines, version)

	// Spacer
	lines = append(lines, "")

	// Status / hint
	var status string
	switch m.phase {
	case "crystal":
		elapsed := time.Since(m.crystalStart).Seconds()
		bootProgress := BootingProgress(elapsed / splashCrystalDelay.Seconds())
		bootStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("3"))
		status = mutedStyle.Render("booting in "+splashCrystalDelay.String()+" · ") + bootStyle.Render(bootProgress) + mutedStyle.Render(" · press any key to skip")
	case "dissolve":
		status = primaryStyle.Render("◆ awakening cube state ◆")
	case "waiting":
		status = highlightStyle.Render("✨ ready · press any key to launch")
	case "fadeout":
		status = mutedStyle.Render("transitioning...")
	}
	lines = append(lines, status)

	// Footer
	footer := mutedStyle.Render("GitLab · c4reqber · Z₃³")
	lines = append(lines, footer)

	// Easter egg (dim, only in waiting phase — rare sighting, vibe farm)
	if m.phase == "waiting" {
		easter := easterStyle.Render(i18n.T("easter.line1") + "  ·  " + i18n.T("easter.line2"))
		lines = append(lines, easter)
	}

	return lines
}

// ── Tea messages ────────────────────────────────────────────────────────────

type splashTickMsg struct{ tick int }
type splashPulseMsg struct{}
type splashTextFadeMsg struct{}
type splashFadeMsg struct{}

func splashTickCmd(tick int) tea.Cmd {
	return tea.Tick(splashTickInterval, func(time.Time) tea.Msg {
		return splashTickMsg{tick: tick}
	})
}

func splashPulseCmd() tea.Cmd {
	return tea.Tick(splashPulseInterval, func(time.Time) tea.Msg {
		return splashPulseMsg{}
	})
}

func splashTextFadeCmd(_ int) tea.Cmd { //nolint:unused
	return tea.Tick(splashTextFade, func(time.Time) tea.Msg {
		return splashTextFadeMsg{}
	})
}

func splashFadeCmd() tea.Cmd {
	return tea.Tick(300*time.Millisecond, func(time.Time) tea.Msg {
		return splashFadeMsg{}
	})
}
