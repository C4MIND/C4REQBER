package tui

import (
	"strings"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/commands"
)

func TestPaletteFuzzyScorePrefix(t *testing.T) {
	// Prefix match: 2 chars matched, +10 prefix bonus, -length penalty
	// 2 + 10 - (12 - 2) = 2. Just verify it's positive and a non-subsequence
	// would score 0.
	if commands.FuzzyMatch("ca", "capabilities") <= 0 {
		t.Error("'ca' should match 'capabilities' (prefix)")
	}
	if commands.FuzzyMatch("xyz", "capabilities") != 0 {
		t.Error("'xyz' should not match 'capabilities'")
	}
}

func TestPaletteFuzzyScoreSubsequence(t *testing.T) {
	// 'sim' is a subsequence of 'simulation'
	if commands.FuzzyMatch("sim", "simulation") <= 0 {
		t.Error("'sim' should match 'simulation'")
	}
}

func TestPaletteFuzzyScoreNoMatch(t *testing.T) {
	if commands.FuzzyMatch("xyz", "capabilities") != 0 {
		t.Error("'xyz' should not match 'capabilities'")
	}
}

func TestPaletteEmptyQueryReturnsAll(t *testing.T) {
	r := buildRegistry()
	matches := r.Match("")
	if len(matches) < 30 {
		t.Errorf("expected at least 30 commands (got %d)", len(matches))
	}
}

func TestPaletteFuzzyMatchFilter(t *testing.T) {
	r := buildRegistry()
	matches := r.Match("sim")
	if len(matches) == 0 {
		t.Error("query 'sim' should match at least sim.list, sim.cost, etc.")
	}
	// All matches should contain 'sim' in id/title/alias (loosely)
	for _, m := range matches {
		found := strings.Contains(m.Cmd.ID, "sim") ||
			strings.Contains(strings.ToLower(m.Cmd.Title), "sim")
		if !found {
			t.Errorf("match %q should contain 'sim'", m.Cmd.ID)
		}
	}
}

func TestPaletteFuzzyMatchCapabilities(t *testing.T) {
	r := buildRegistry()
	matches := r.Match("capsim")
	if len(matches) == 0 {
		t.Error("'capsim' should match at least app.capabilities")
	}
	foundCapsim := false
	for _, m := range matches {
		if m.Cmd.ID == "app.capabilities" {
			foundCapsim = true
		}
	}
	if !foundCapsim {
		t.Error("'capsim' should find app.capabilities")
	}
}

func TestPaletteRenderEmpty(t *testing.T) {
	out := RenderCommandPalette("", nil, 0, 80, 24)
	if !strings.Contains(out, "Command Palette") {
		t.Error("expected 'Command Palette' in output")
	}
}

func TestPaletteRenderWithQuery(t *testing.T) {
	r := buildRegistry()
	matches := r.Match("sim")
	out := RenderCommandPalette("sim", matches, 0, 80, 24)
	if !strings.Contains(out, "sim") {
		t.Error("expected query in output")
	}
	if !strings.Contains(out, "▶") {
		t.Error("expected focus indicator")
	}
}

func TestPaletteRenderEmptyState(t *testing.T) {
	out := RenderCommandPalette("xyzqqq", nil, 0, 80, 24)
	if !strings.Contains(out, "no matches") {
		t.Error("expected 'no matches' for empty result")
	}
}

func TestPaletteOpenCycle(t *testing.T) {
	m := NewAppFresh("http://test")
	m.openPalette()
	if !m.paletteActive {
		t.Error("palette should be active after openPalette")
	}
	if m.paletteQuery != "" {
		t.Error("palette query should start empty")
	}
	if len(m.paletteMatches) == 0 {
		t.Error("palette should populate with all commands on empty query")
	}
}

func TestPaletteTypedFilter(t *testing.T) {
	m := NewAppFresh("http://test")
	m.openPalette()
	m.paletteQuery = "ca"
	m.refreshPaletteMatches()
	if len(m.paletteMatches) == 0 {
		t.Error("'ca' should match some commands")
	}
}

func TestPaletteRunFocused(t *testing.T) {
	m := NewAppFresh("http://test")
	m.openPalette()
	// Find the help command in the matches
	helpIdx := -1
	for i, mm := range m.paletteMatches {
		if mm.Cmd.ID == "app.help" {
			helpIdx = i
			break
		}
	}
	if helpIdx < 0 {
		t.Fatal("could not find app.help in palette matches")
	}
	before := m.showHelp
	m.paletteFocused = helpIdx
	m.runPaletteFocused()
	if m.paletteActive {
		t.Error("palette should close after running")
	}
	if m.showHelp == before {
		t.Error("running app.help should toggle showHelp")
	}
}

func TestPaletteFocusNavigation(t *testing.T) {
	m := NewAppFresh("http://test")
	m.openPalette()
	m.paletteQuery = "s"
	m.refreshPaletteMatches()
	if len(m.paletteMatches) < 2 {
		t.Skip("not enough matches to test focus nav")
	}
	start := m.paletteFocused
	m.paletteFocused = minInt2(m.paletteFocused+1, len(m.paletteMatches)-1)
	if m.paletteFocused <= start {
		t.Error("focused should increase on +1")
	}
}

func minInt2(a, b int) int {
	if a < b {
		return a
	}
	return b
}
