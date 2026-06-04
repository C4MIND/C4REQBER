package splash

import (
	"math/rand"
	"strings"
	"testing"

	tea "github.com/charmbracelet/bubbletea"
)

func TestSplash_Init(t *testing.T) {
	m := New()
	cmd := m.Init()
	if cmd == nil {
		t.Fatal("expected non-nil init command")
	}
}

func TestSplash_View(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 24
	v := m.View()
	if v == "" {
		t.Fatal("expected non-empty view")
	}
}

func TestSplash_EnterTransitions(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 24
	// Enter should NOT transition during loading
	newM, _ := m.Update(tea.KeyMsg{Type: tea.KeyEnter})
	m2 := newM.(Model)
	if m2.loadingDone {
		t.Fatal("expected loadingDone false during loading phase")
	}
	// Enter SHOULD transition in waiting phase
	m2.phase = "waiting"
	newM, cmd := m2.Update(tea.KeyMsg{Type: tea.KeyEnter})
	if cmd == nil {
		t.Fatal("expected transition command")
	}
	m3 := newM.(Model)
	if !m3.loadingDone {
		t.Fatal("expected loadingDone to be true")
	}
}

func TestSplash_Quit(t *testing.T) {
	m := New()
	_, cmd := m.Update(tea.KeyMsg{Type: tea.KeyCtrlC})
	if cmd == nil {
		t.Fatal("expected quit command")
	}
}

func TestSplash_WindowSize(t *testing.T) {
	m := New()
	newM, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 30})
	m2 := newM.(Model)
	if m2.width != 100 {
		t.Fatalf("expected width 100, got %d", m2.width)
	}
	if m2.height != 30 {
		t.Fatalf("expected height 30, got %d", m2.height)
	}
}

func TestSplash_LoadingDone(t *testing.T) {
	m := New()
	if m.LoadingDone() {
		t.Fatal("expected loading not done initially")
	}
	// Simulate completion
	m.phase = "waiting"
	m.loadingDone = true
	if !m.LoadingDone() {
		t.Fatal("expected loading done")
	}
}

// ── Skip functionality ──────────────────────────────────────────────────────

func TestSplash_SkipAnyKey(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 40
	if m.phase != "crystal" {
		t.Fatal("expected initial phase crystal")
	}
	// Any non-Enter key should skip crystal and start dissolve
	newM, cmd := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'a'}})
	m2 := newM.(Model)
	if m2.phase != "dissolve" {
		t.Fatalf("expected phase dissolve after skip, got %s", m2.phase)
	}
	if cmd == nil {
		t.Fatal("expected dissolve tick command after skip")
	}
	// Escape key should also skip
	m = New()
	m.width = 80
	m.height = 40
	newM, _ = m.Update(tea.KeyMsg{Type: tea.KeyEscape})
	m2 = newM.(Model)
	if m2.phase != "dissolve" {
		t.Fatalf("expected phase dissolve after Escape skip, got %s", m2.phase)
	}
}

func TestSplash_SkipDoesNotAffectWaiting(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 40
	m.phase = "waiting"
	newM, _ := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'a'}})
	m2 := newM.(Model)
	if m2.phase != "waiting" {
		t.Fatalf("expected phase waiting unchanged, got %s", m2.phase)
	}
}

// ── Compact mode ────────────────────────────────────────────────────────────

func TestSplash_CompactModeDetection(t *testing.T) {
	m := New()
	m.height = 20
	if !m.isCompact() {
		t.Fatal("expected compact mode for height 20")
	}
	m.height = 40
	if m.isCompact() {
		t.Fatal("expected non-compact mode for height 40")
	}
}

func TestSplash_CompactFinalForm(t *testing.T) {
	lines := buildFinalForm(24, true)
	joined := strings.Join(lines, "\n")
	if !strings.Contains(joined, "EXO") {
		t.Fatal("expected compact final form to contain asciiC4R art")
	}
}

func TestSplash_NonCompactFinalForm(t *testing.T) {
	lines := buildFinalForm(60, false)
	joined := strings.Join(lines, "\n")
	if !strings.Contains(joined, "1111") {
		t.Fatal("expected non-compact final form to contain bigC4R art")
	}
}

// ── Dynamic boundaries ──────────────────────────────────────────────────────

func TestSplash_DynamicCubeLineCount(t *testing.T) {
	m := New()
	m.height = 40 // non-compact
	expected := len(splitLines(greenCubeRaw))
	if m.cubeLineCount() != expected {
		t.Fatalf("expected cubeLineCount %d, got %d", expected, m.cubeLineCount())
	}
}

func TestSplash_DynamicC4RLineCount(t *testing.T) {
	m := New()
	m.height = 40 // non-compact
	expected := len(splitLines(bigC4R))
	if m.c4rLineCount() != expected {
		t.Fatalf("expected c4rLineCount %d, got %d", expected, m.c4rLineCount())
	}
	// Compact mode
	m.height = 20
	expectedCompact := len(splitLines(asciiC4R))
	if m.c4rLineCount() != expectedCompact {
		t.Fatalf("expected compact c4rLineCount %d, got %d", expectedCompact, m.c4rLineCount())
	}
}

// ── Morph math ──────────────────────────────────────────────────────────────

func TestSplash_TotalMorphTicks(t *testing.T) {
	m := New()
	m.height = 40
	m.seedArt = stripANSI(rawANSISmall)
	m.forms = buildForms(m.artHeight(), m.seedArt, false, m.rng)
	expected := (len(m.forms) - 1) * formDuration
	if m.totalMorphTicks() != expected {
		t.Fatalf("expected totalMorphTicks %d, got %d", expected, m.totalMorphTicks())
	}
}

func TestSplash_BlendRowProgress(t *testing.T) {
	prev := []string{"abcd", "efgh"}
	curr := []string{"wxyz", "1234"}
	// tick == formDuration should give full progress
	row := blendRow(prev, curr, 0, formDuration, rand.New(rand.NewSource(1)))
	if row == "" {
		t.Fatal("expected non-empty blended row")
	}
}

// ── Art helpers ─────────────────────────────────────────────────────────────

func TestSplash_StripANSI(t *testing.T) {
	input := "\x1b[38;2;255;0;0mHello\x1b[0m"
	output := stripANSI(input)
	if output != "Hello" {
		t.Fatalf("expected 'Hello', got '%s'", output)
	}
}

func TestSplash_PadToHeight(t *testing.T) {
	lines := []string{"a", "b"}
	padded := padToHeight(lines, 5)
	if len(padded) != 5 {
		t.Fatalf("expected length 5, got %d", len(padded))
	}
}

func TestSplash_PickANSI(t *testing.T) {
	m := New()
	m.height = 66
	m.width = 115
	if m.pickANSI() != rawANSI {
		t.Fatal("expected rawANSI for large terminal")
	}
	m.height = 24
	m.width = 80
	if m.pickANSI() != rawANSISmall {
		t.Fatal("expected rawANSISmall for small terminal")
	}
}

// ── Color helpers ───────────────────────────────────────────────────────────

func TestSplash_RGBToHexZeroPadding(t *testing.T) {
	// Components < 16 must be zero-padded.
	hex := rgbToHex(0.01, 0.01, 0.01)
	if len(hex) != 7 {
		t.Fatalf("expected 7-char hex, got %d: %s", len(hex), hex)
	}
	// Verify hexToRGB can parse it back without falling back to (1,1,1).
	r, g, b := hexToRGB(hex)
	if r == 1 && g == 1 && b == 1 {
		t.Fatal("rgbToHex produced unparsable hex (fallback white)")
	}
}

func TestSplash_LerpColorLowComponents(t *testing.T) {
	// Lerp near-black to white at t=0.01 should produce a parseable dark color.
	c := lerpColor("#000000", "#ffffff", 0.01)
	if len(c) != 7 {
		t.Fatalf("expected 7-char hex, got %d: %s", len(c), c)
	}
	r, g, b := hexToRGB(c)
	if r == 1 && g == 1 && b == 1 {
		t.Fatal("lerpColor produced unparsable hex")
	}
}

func TestSplash_RGBToHexRounding(t *testing.T) {
	// Midpoint lerp must round correctly to #808080, not truncate to #7f7f7f.
	c := lerpColor("#000000", "#ffffff", 0.5)
	if c != "#808080" {
		t.Fatalf("expected midpoint #808080, got %s", c)
	}
}

// ── Art alignment ───────────────────────────────────────────────────────────

func TestSplash_PadToMaxWidth(t *testing.T) {
	lines := []string{"abc", "ab", "a"}
	padded := padToMaxWidth(lines)
	for i, l := range padded {
		if len([]rune(l)) != 3 {
			t.Fatalf("expected width 3 for line %d, got %d", i, len([]rune(l)))
		}
	}
}

func TestSplash_ArtBoundsPadded(t *testing.T) {
	m := New()
	m.height = 60 // non-compact, tall enough for padding
	m.width = 100
	// Simulate bottom-aligned padded art: 8 empty + 28 cube + 1 spacer + 11 C4R = 48
	art := make([]string, 48)
	for i := range art {
		art[i] = " "
	}
	cubeEnd, c4rStart, c4rEnd := m.artBounds(art)
	if cubeEnd != 36 {
		t.Fatalf("expected cubeEnd 36 for padded art, got %d", cubeEnd)
	}
	if c4rStart != 37 {
		t.Fatalf("expected c4rStart 37 for padded art, got %d", c4rStart)
	}
	if c4rEnd != 48 {
		t.Fatalf("expected c4rEnd 48 for padded art, got %d", c4rEnd)
	}
}

func TestSplash_ArtBoundsTruncated(t *testing.T) {
	m := New()
	m.height = 40 // non-compact, truncated
	m.width = 100
	// Truncated art: 35 lines (missing 4 cube lines from top)
	art := make([]string, 35)
	for i := range art {
		art[i] = " "
	}
	cubeEnd, c4rStart, c4rEnd := m.artBounds(art)
	if cubeEnd != 23 {
		t.Fatalf("expected cubeEnd 23 for truncated art, got %d", cubeEnd)
	}
	if c4rStart != 24 {
		t.Fatalf("expected c4rStart 24 for truncated art, got %d", c4rStart)
	}
	if c4rEnd != 35 {
		t.Fatalf("expected c4rEnd 35 for truncated art, got %d", c4rEnd)
	}
}

func TestSplash_ArtBoundsCompact(t *testing.T) {
	m := New()
	m.height = 24 // compact
	m.width = 80
	// Bottom-aligned padded compact: 15 empty + 9 C4R = 24
	art := make([]string, 24)
	for i := range art {
		art[i] = " "
	}
	cubeEnd, c4rStart, c4rEnd := m.artBounds(art)
	if cubeEnd != 0 {
		t.Fatalf("expected cubeEnd 0 for compact, got %d", cubeEnd)
	}
	if c4rStart != 15 {
		t.Fatalf("expected c4rStart 15 for compact, got %d", c4rStart)
	}
	if c4rEnd != 24 {
		t.Fatalf("expected c4rEnd 24 for compact, got %d", c4rEnd)
	}
}

// ── Bottom-aligned padding ──────────────────────────────────────────────────

func TestSplash_PadToHeightBottomAlign(t *testing.T) {
	lines := []string{"a", "b"}
	padded := padToHeight(lines, 5)
	if len(padded) != 5 {
		t.Fatalf("expected length 5, got %d", len(padded))
	}
	// Content should be at the bottom (last 2 lines)
	if padded[3] != "a" || padded[4] != "b" {
		t.Fatalf("expected content at bottom, got %v", padded)
	}
	// Top should be blank
	if padded[0] != "" || padded[1] != "" || padded[2] != "" {
		t.Fatalf("expected blank top padding, got %v", padded)
	}
}

// ── Waiting-phase resize rebuild ────────────────────────────────────────────

func TestSplash_WaitingResizeRebuildsForms(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 40 // non-compact
	m.phase = "waiting"
	m.seedArt = stripANSI(rawANSISmall)
	m.forms = buildForms(m.artHeight(), m.seedArt, false, m.rng)
	oldLen := len(m.forms[len(m.forms)-1])

	// Resize to compact height
	m.height = 24
	newM, _ := m.Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	m2 := newM.(Model)
	if len(m2.forms) == 0 {
		t.Fatal("expected forms rebuilt after resize")
	}
	newLen := len(m2.forms[len(m2.forms)-1])
	if newLen == oldLen {
		t.Fatalf("expected form length to change after resize, got old=%d new=%d", oldLen, newLen)
	}
}

// ── Text fade in waiting phase ──────────────────────────────────────────────

func TestSplash_TextFadeContinuesInWaiting(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 40
	m.phase = "waiting"
	m.textTick = 0
	newM, cmd := m.Update(textFadeTickMsg{})
	m2 := newM.(Model)
	if m2.textTick != 1 {
		t.Fatalf("expected textTick to increment in waiting, got %d", m2.textTick)
	}
	if cmd == nil {
		t.Fatal("expected text fade command to continue in waiting phase")
	}
}

// ── Trim consistency ────────────────────────────────────────────────────────

func TestSplash_CubeLeadingSpacesPreserved(t *testing.T) {
	// buildFinalForm must NOT strip leading spaces from the first line of the cube.
	lines := buildFinalForm(60, false)
	// Find first non-empty line (after bottom-align padding)
	var firstNonEmpty string
	for _, l := range lines {
		if strings.TrimSpace(l) != "" {
			firstNonEmpty = l
			break
		}
	}
	if firstNonEmpty == "" {
		t.Fatal("expected non-empty line in final form")
	}
	// The first content line of greenCubeRaw has leading spaces.
	if !strings.HasPrefix(firstNonEmpty, " ") {
		t.Fatal("expected leading spaces preserved on first cube line")
	}
}

func TestSplash_BlendRowNoNullRunes(t *testing.T) {
	// When source is shorter than target, blendRow must pad with spaces,
	// not null runes.
	prev := []string{"ab"}
	curr := []string{"wxyz"}
	row := blendRow(prev, curr, 0, 0, rand.New(rand.NewSource(1)))
	if strings.ContainsRune(row, '\x00') {
		t.Fatalf("blendRow produced null runes: %q", row)
	}
	// Positions beyond the source length should be spaces or scramble chars,
	// never null runes.
	for i, r := range row {
		if r == '\x00' {
			t.Fatalf("null rune at position %d: %q", i, row)
		}
	}
}

func TestSplash_CrystalArtNoEmptyBookends(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 40
	lines := m.artView()
	if len(lines) == 0 {
		t.Fatal("expected non-empty crystal art")
	}
	if lines[0] == "" {
		t.Fatal("expected first crystal art line to be non-empty (no leading newline)")
	}
	if lines[len(lines)-1] == "" {
		t.Fatal("expected last crystal art line to be non-empty (no trailing newline)")
	}
}

func TestSplash_SplitLines(t *testing.T) {
	input := "\n  a\n\n b \n"
	lines := splitLines(input)
	// strings.Trim removes leading/trailing "\n", eliminating empty
	// bookend lines while preserving internal empties.
	if len(lines) != 3 {
		t.Fatalf("expected 3 lines, got %d: %v", len(lines), lines)
	}
	if lines[0] != "  a" {
		t.Fatalf("expected first line '  a', got %q", lines[0])
	}
	if lines[1] != "" {
		t.Fatalf("expected second line empty, got %q", lines[1])
	}
	if lines[2] != " b " {
		t.Fatalf("expected third line ' b ', got %q", lines[2])
	}
}

// ── Easing & morph perfection ───────────────────────────────────────────────

func TestSplash_EaseOutQuad(t *testing.T) {
	if easeOutQuad(0) != 0 {
		t.Fatalf("expected easeOutQuad(0)=0, got %f", easeOutQuad(0))
	}
	if easeOutQuad(1) != 1 {
		t.Fatalf("expected easeOutQuad(1)=1, got %f", easeOutQuad(1))
	}
	mid := easeOutQuad(0.5)
	if mid <= 0.5 || mid >= 1 {
		t.Fatalf("expected easeOutQuad(0.5) in (0.5,1), got %f", mid)
	}
}

func TestSplash_BlendRowFullLock(t *testing.T) {
	prev := []string{"abcd"}
	curr := []string{"wxyz"}
	// At the final tick (formDuration-1) blendRow must return the target
	// row completely, with no residual scramble.
	row := blendRow(prev, curr, 0, formDuration-1, rand.New(rand.NewSource(1)))
	if row != "wxyz" {
		t.Fatalf("expected full lock to target 'wxyz', got %q", row)
	}
}

func TestSplash_ShimmerFinalForm(t *testing.T) {
	m := New()
	m.height = 60 // non-compact, tall enough for padding
	m.pulseTick = 2
	// Build art taller than content so cube lines sit inside the slice.
	lines := make([]string, 48)
	for i := range lines {
		lines[i] = " "
	}
	lines[21] = "...." // inside cube region (padTop=48-39=9, cube=9..36)
	lines[37] = "1111" // inside C4R region

	shimm := m.shimmerFinalForm(lines)
	if shimm[21] == lines[21] {
		t.Fatal("expected shimmer to modify cube dots")
	}
	if shimm[37] != lines[37] {
		t.Fatal("expected C4R line to be untouched by shimmer")
	}
}

func TestSplash_FadeColorExact(t *testing.T) {
	m := New()
	m.textTick = 0
	c := m.fadeColor("#ffffff", 3)
	if c == "#ffffff" {
		t.Fatal("expected dim color at tick 0")
	}
	m.textTick = 3
	c = m.fadeColor("#ffffff", 3)
	if c != "#ffffff" {
		t.Fatalf("expected full color at tick>=revealAfter, got %s", c)
	}
}

// ── Round 8 — Defensive & Structural Fixes ──────────────────────────────────

func TestSplash_DissolveResizeRebuildsForms(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 40 // non-compact
	// Enter dissolve manually
	m.phase = "dissolve"
	m.seedArt = stripANSI(rawANSISmall)
	m.forms = buildForms(m.artHeight(), m.seedArt, false, m.rng)
	m.morphLines = make([]string, len(m.forms[0]))
	copy(m.morphLines, m.forms[0])
	m.morphTick = 5
	oldFormLen := len(m.forms[0])

	// Resize to compact height
	newM, _ := m.Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	m2 := newM.(Model)
	if m2.phase != "dissolve" {
		t.Fatalf("expected phase still dissolve, got %s", m2.phase)
	}
	if len(m2.forms) == 0 {
		t.Fatal("expected forms rebuilt after resize in dissolve")
	}
	newFormLen := len(m2.forms[0])
	if newFormLen == oldFormLen {
		t.Fatalf("expected form length to change after resize, got old=%d new=%d", oldFormLen, newFormLen)
	}
	if len(m2.morphLines) != newFormLen {
		t.Fatalf("expected morphLines length %d after resize, got %d", newFormLen, len(m2.morphLines))
	}
}

func TestSplash_ViewDoesNotMutateArtLines(t *testing.T) {
	m := New()
	m.width = 80
	m.height = 24
	m.phase = "dissolve"
	m.seedArt = stripANSI(rawANSISmall)
	m.forms = buildForms(m.artHeight(), m.seedArt, false, m.rng)
	m.morphLines = make([]string, len(m.forms[0]))
	copy(m.morphLines, m.forms[0])
	m.morphTick = 3

	v1 := m.View()
	if v1 == "" {
		t.Fatal("expected non-empty view")
	}
	v2 := m.View()
	if v1 != v2 {
		// The view should be deterministic for the same model state.
		// If it differs, something mutated internal state during rendering.
		t.Fatal("expected deterministic View() output; got mutation during render")
	}
}

func TestSplash_CrystalCubeAlignment(t *testing.T) {
	// On a tall non-compact terminal the purple crystal should be positioned
	// so that its centre aligns with the green cube's centre in waiting phase.
	m := New()
	m.width = 120
	m.height = 80 // non-compact, plenty of room
	m.phase = "crystal"

	artLines := m.artView()
	crystalCenter := len(artLines) / 2
	targetCenter := m.waitingCubeCenterY()
	if targetCenter < 0 {
		t.Fatal("expected non-compact waiting cube center")
	}

	expectedPadTop := targetCenter - crystalCenter
	if expectedPadTop < 0 {
		expectedPadTop = 0
	}

	v := m.View()
	lines := strings.Split(v, "\n")

	// Find the first rendered line that isn't blank.
	firstNonEmpty := -1
	for i, l := range lines {
		if strings.TrimSpace(l) != "" {
			firstNonEmpty = i
			break
		}
	}
	if firstNonEmpty < 0 {
		t.Fatal("expected non-empty content in view")
	}
	if firstNonEmpty != expectedPadTop {
		t.Fatalf("expected crystal art to start at line %d (center aligned to waiting cube center %d), got %d",
			expectedPadTop, targetCenter, firstNonEmpty)
	}
}

func TestSplash_WaitingCubeCenterY(t *testing.T) {
	// Verify the helper returns sensible values for various heights.
	m := New()
	m.width = 100

	m.height = 24 // compact
	if m.waitingCubeCenterY() != -1 {
		t.Fatal("expected -1 for compact mode")
	}

	m.height = 60
	c := m.waitingCubeCenterY()
	if c < 0 {
		t.Fatalf("expected positive center for height 60, got %d", c)
	}
	// For height 60: h=48, padTopView=1, padTopArt=9, cube center=13 => 23
	if c != 23 {
		t.Fatalf("expected center 23 for height 60, got %d", c)
	}

	m.height = 50
	c = m.waitingCubeCenterY()
	// h=38, truncated by padToHeight: cubeTop=0, visibleCube=26, center=13
	// padTopView = 50-38-1-7-3 = 1 => 14
	if c != 14 {
		t.Fatalf("expected center 14 for height 50, got %d", c)
	}
}

func TestSplash_CrossPhaseTaglineAlignment(t *testing.T) {
	// On large terminals the tagline should land on the same absolute row in
	// all three phases so the vertical layout never jumps during transitions.
	m := New()
	m.width = 120
	m.height = 80

	findTaglineRow := func(phase string) int {
		m.phase = phase
		v := m.View()
		lines := strings.Split(v, "\n")
		for i, l := range lines {
			if strings.Contains(l, "COGNITIVE EXOSKELETON") {
				return i
			}
		}
		return -1
	}

	crystalRow := findTaglineRow("crystal")

	// Dissolve: manually set up forms so artView returns morphLines.
	m.seedArt = stripANSI(rawANSI)
	m.forms = buildForms(m.artHeight(), m.seedArt, false, m.rng)
	m.morphLines = make([]string, len(m.forms[0]))
	copy(m.morphLines, m.forms[0])
	dissolveRow := findTaglineRow("dissolve")

	// Waiting: build final form shimmer.
	m.forms = buildForms(m.artHeight(), m.seedArt, false, m.rng)
	waitingRow := findTaglineRow("waiting")

	if crystalRow < 0 || dissolveRow < 0 || waitingRow < 0 {
		t.Fatalf("tagline not found in all phases: crystal=%d dissolve=%d waiting=%d",
			crystalRow, dissolveRow, waitingRow)
	}

	if crystalRow != dissolveRow {
		t.Fatalf("crystal tagline row %d != dissolve tagline row %d", crystalRow, dissolveRow)
	}
	if crystalRow != waitingRow {
		t.Fatalf("crystal tagline row %d != waiting tagline row %d", crystalRow, waitingRow)
	}
}

func TestSplash_WaitingCubeCenterY_LargeTerminal(t *testing.T) {
	m := New()
	m.width = 120
	m.height = 80
	c := m.waitingCubeCenterY()
	// h=54, padTopView=15, padTopArt=15, cube center=13 => 43
	if c != 43 {
		t.Fatalf("expected center 43 for height 80, got %d", c)
	}
}

func TestSplash_CrystalTaglineMatchesWaiting(t *testing.T) {
	// The tagline in crystal phase should land on the same absolute row as in
	// waiting phase (or as close as possible without moving the crystal).
	m := New()
	m.width = 120
	m.height = 80

	findTaglineRow := func(phase string) int {
		m.phase = phase
		v := m.View()
		lines := strings.Split(v, "\n")
		for i, l := range lines {
			if strings.Contains(l, "COGNITIVE EXOSKELETON") {
				return i
			}
		}
		return -1
	}

	crystalRow := findTaglineRow("crystal")
	waitingRow := findTaglineRow("waiting")
	if crystalRow < 0 {
		t.Fatal("tagline not found in crystal phase")
	}
	if waitingRow < 0 {
		t.Fatal("tagline not found in waiting phase")
	}

	// On large terminals with big crystal the tagline may sit 0–2 rows below
	// the waiting target because the crystal is taller than the available space
	// above the fixed tagline row.  We allow a small tolerance.
	diff := crystalRow - waitingRow
	if diff < 0 || diff > 2 {
		t.Fatalf("crystal tagline row %d too far from waiting row %d (diff=%d, want 0..2)",
			crystalRow, waitingRow, diff)
	}
}
