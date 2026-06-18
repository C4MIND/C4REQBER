// Package tui — golden snapshot generator for the 6 device fixtures.
// Per §18 of the unified plan: 6 fixtures × ~5 scenarios = 30 snapshots
// that lock the rendered output byte-for-byte. Update with
// `go test . -run TestGenerateGoldens -update`.

package tui

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
)

// Fixture represents one of the 6 standard terminal sizes (§2.5).
type Fixture struct {
	ID   string
	W, H int
}

var goldenFixtures = []Fixture{
	{"T0-tmux", 80, 24},
	{"T1-mbp13", 144, 40},
	{"T2-mbp16", 168, 48},
	{"T2-1080p", 192, 50},
	{"T3-4k", 220, 60},
	{"T3-ultrawide", 280, 50},
}

// freshGoldenModel returns a model ready to render at the given fixture size.
// HOME is set to a temp dir to isolate from the user's real state.
func freshGoldenModel(t *testing.T, w, h int) *model {
	t.Helper()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	// Pin the language BEFORE NewApp so the empty card (captured at append
	// time) and every later render are English regardless of a leaked global
	// lang or the developer's saved state. Goldens are English by design.
	SetLang(i18n.LangEN)
	// Mark first-run done so no wizard takes over the screen
	store, err := persist.New(persist.DefaultPath())
	if err == nil {
		store.MarkFirstRunDone()
		_ = store.Save()
	}
	m := NewApp("http://127.0.0.1:8000")
	// Pin the platform so keybinding labels (Ctrl+ vs Cmd+) in the help/
	// shortcuts widgets don't depend on the host OS that runs the test.
	m.keymap = NewKeyMap(PlatformLinux)
	m.width = w
	m.height = h
	_, _ = m.Update(tea.WindowSizeMsg{Width: w, Height: h})
	m.layout()
	return m
}

// renderClean strips ANSI noise (CSI escapes) and clock fields for
// stable byte comparison across runs.
func renderClean(s string) string {
	// strip CSI sequences: \x1b[...m, \x1b[...H, etc.
	var b strings.Builder
	skip := false
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c == 0x1b {
			skip = true
			continue
		}
		if skip {
			if (c >= '@' && c <= '~') || c == 'm' || c == 'K' || c == 'J' || c == 'H' {
				skip = false
			}
			continue
		}
		b.WriteByte(c)
	}
	// Normalize HH:MM:SS clock to <CLOCK>
	for {
		i := indexTime(b.String())
		if i < 0 {
			break
		}
		s := b.String()
		b.Reset()
		b.WriteString(s[:i])
		b.WriteString("<CLOCK>")
		b.WriteString(s[i+8:])
	}
	return b.String()
}

// indexTime returns the index of the first HH:MM:SS in s, or -1.
func indexTime(s string) int {
	for i := 0; i+8 <= len(s); i++ {
		if s[i+2] == ':' && s[i+5] == ':' &&
			isDigit(s[i]) && isDigit(s[i+1]) &&
			isDigit(s[i+3]) && isDigit(s[i+4]) &&
			isDigit(s[i+6]) && isDigit(s[i+7]) {
			return i
		}
	}
	return -1
}

func isDigit(c byte) bool { return c >= '0' && c <= '9' }

func populateEmpty(m *model) {
	// No-op; NewApp already adds the Empty placeholder card
}

func populateHypothesis(m *model) {
	m.appendCard(Card{Kind: CardPhase, Title: "D", Body: "scoring hypotheses", Time: time.Now(), Status: "running", Progress: 0.67})
	m.appendCard(Card{
		Kind: CardHypothesis, Title: "Hypothesis", Body: "guides with GC content <40% have higher off-target rates",
		Time: time.Now(), Status: "done",
		Meta: []cards.MetaKV{{Key: "novelty", Value: "0.87"}, {Key: "source", Value: "openmm"}},
	})
}

// populateMultiPaper adds a hypothesis + 3 papers to test list density.
func populateMultiPaper(m *model) {
	populateHypothesis(m)
	m.appendCard(Card{Kind: CardPaper, Title: "CRISPR off-target review", Body: "Nature 2024 · citations 142", Time: time.Now(), Status: "done", Meta: []cards.MetaKV{{Key: "doi", Value: "10.1038/nature.2024.001"}}})
	m.appendCard(Card{Kind: CardPaper, Title: "Guide RNA design principles", Body: "Cell 2023 · citations 87", Time: time.Now(), Status: "done", Meta: []cards.MetaKV{{Key: "doi", Value: "10.1016/j.cell.2023.04.012"}}})
	m.appendCard(Card{Kind: CardPaper, Title: "Off-target cleavage mechanisms", Body: "Science 2024 · citations 63", Time: time.Now(), Status: "done", Meta: []cards.MetaKV{{Key: "doi", Value: "10.1126/science.adi1234"}}})
}

// populateError adds an error card.
func populateError(m *model) {
	m.appendCard(Card{Kind: CardError, Title: "Discovery failed", Body: "backend returned 500 on submit", Time: time.Now(), Status: "error"})
}

// populateExpanded creates a card with a long FullBody and expands it
// (sets State directly so renderCard renders FullBody).
func populateExpanded(m *model) {
	m.appendCard(Card{
		Kind:     CardHypothesis,
		Title:    "Expanded hypothesis",
		Body:     "Short body",
		FullBody: "This is the full body of the hypothesis. It is much longer than the body and explains everything in detail. The user can read the whole thing when expanded. Line two of the full body. Line three with more detail about methodology and findings.",
		State:    cards.StateExpanded,
	})
}

// populateFocused shows the focused-card chrome.
func populateFocused(m *model) {
	populateHypothesis(m)
	// Second hypothesis so we have a non-empty feed and can focus
	m.appendCard(Card{Kind: CardHypothesis, Title: "Second hypothesis", Body: "x", Time: time.Now(), Status: "done"})
	m.focusedCardIdx = 0
}

// populateMixedFeed is the most realistic scenario — phases interleaved
// with sim cards, plus a hypothesis and a paper. This is what a
// user would typically see 30 seconds into a discovery.
func populateMixedFeed(m *model) {
	// Append in chronological order
	now := time.Now()
	m.appendCard(Card{Kind: CardPhase, Title: "A", Body: "framing", Time: now.Add(-30 * time.Second), Status: "done", Progress: 1.0})
	m.appendCard(Card{Kind: CardPhase, Title: "B", Body: "knowledge acquisition", Time: now.Add(-20 * time.Second), Status: "done", Progress: 1.0})
	m.appendCard(Card{Kind: CardPhase, Title: "C", Body: "gap analysis", Time: now.Add(-10 * time.Second), Status: "done", Progress: 1.0})
	m.appendCard(Card{Kind: CardSimulation, Title: "openmm protein folding", Body: "verdict: supports_hypothesis", Time: now.Add(-5 * time.Second), Status: "done",
		Sim: cards.SimFields{Engine: "openmm", EngineStatus: "success", Domain: "biology", Pattern: "protein_folding", Verdict: "supports_hypothesis", CostUSD: 0.012}})
	m.appendCard(Card{Kind: CardPhase, Title: "D", Body: "scoring hypotheses", Time: now, Status: "running", Progress: 0.67})
}

// populateFullHypothesis: hypothesis with FullBody populated (not expanded yet).
// Verifies that the short body is shown and FullBody is hidden.
func populateFullHypothesis(m *model) {
	m.appendCard(Card{
		Kind:     CardHypothesis,
		Title:    "Hypothesis with full body",
		Body:     "Short body here",
		FullBody: "This long FullBody text is only shown when the card is expanded. The user can press Enter to see it.",
		Time:     time.Now(), Status: "done",
	})
}

// populateVerdictChips: hypothesis with 2 linked sims (1 supports, 1 refutes)
// to exercise the verdict chip rendering.
func populateVerdictChips(m *model) {
	now := time.Now()
	m.appendCard(Card{Kind: CardHypothesis, Title: "Verdict test", Body: "h body", Time: now, Status: "done"})
	m.appendCard(Card{Kind: CardSimulation, Title: "openmm", Body: "supports", Time: now, Status: "done",
		Sim: cards.SimFields{Engine: "openmm", EngineStatus: "success", Domain: "biology", Pattern: "p", Verdict: "supports_hypothesis", HypothesisID: 0 /* will be linked */}})
	m.appendCard(Card{Kind: CardSimulation, Title: "jaxsim", Body: "refutes", Time: now, Status: "done",
		Sim: cards.SimFields{Engine: "jaxsim", EngineStatus: "success", Domain: "biology", Pattern: "p", Verdict: "refutes_hypothesis", HypothesisID: 0}})
}

// populatePalette: command palette open with empty query (shows all commands).
func populatePalette(m *model) {
	m.openPalette()
}

// populateBookmark: hypothesis that's bookmarked (should never auto-prune).
func populateBookmark(m *model) {
	m.appendCard(Card{Kind: CardHypothesis, Title: "Bookmarked insight", Body: "Important", Time: time.Now(), Status: "done", Bookmark: true})
}

// populateSimVerdictSupports: a single sim with verdict=supports.
func populateSimVerdictSupports(m *model) {
	m.appendCard(Card{Kind: CardSimulation, Title: "openmm",
		Body: "verdict: supports_hypothesis", Time: time.Now(), Status: "done",
		Sim: cards.SimFields{Engine: "openmm", EngineStatus: "success", Domain: "biology", Pattern: "p", Verdict: "supports_hypothesis"}})
}

// populateSimVerdictRefutes: a single sim with verdict=refutes.
func populateSimVerdictRefutes(m *model) {
	m.appendCard(Card{Kind: CardSimulation, Title: "jaxsim",
		Body: "verdict: refutes_hypothesis", Time: time.Now(), Status: "done",
		Sim: cards.SimFields{Engine: "jaxsim", EngineStatus: "success", Domain: "biology", Pattern: "p", Verdict: "refutes_hypothesis"}})
}

// populateSimVerdictInconclusive: a single sim with verdict=inconclusive.
func populateSimVerdictInconclusive(m *model) {
	m.appendCard(Card{Kind: CardSimulation, Title: "vina",
		Body: "verdict: inconclusive", Time: time.Now(), Status: "done",
		Sim: cards.SimFields{Engine: "vina", EngineStatus: "success", Domain: "biology", Pattern: "p", Verdict: "inconclusive"}})
}

// populateSimSkipped: a sim with status=unavailable + install hint.
func populateSimSkipped(m *model) {
	m.appendCard(Card{Kind: CardSimulation, Title: "fenicsx unavailable",
		Body: "skipped: no_arm64_wheel", Time: time.Now(), Status: "skipped",
		Sim: cards.SimFields{
			Engine: "fenicsx", EngineStatus: "unavailable", Domain: "materials",
			Pattern: "elasticity_3d", InstallHint: "conda install -c conda-forge fenics-dolfinx",
		}})
}

// populateHelpShown: help overlay is open.
func populateHelpShown(m *model) {
	m.showHelp = true
	m.appendCard(Card{Kind: CardHypothesis, Title: "Sample", Body: "x", Time: time.Now(), Status: "done"})
}

// populateSettingsOpen: settings menu is open.
func populateSettingsOpen(m *model) {
	m.settingsVisible = true
}

// populateAchievementShown: achievement overlay is showing.
func populateAchievementShown(m *model) {
	m.achievements.ShowOverlay("🏆 First Discovery · You completed your first discovery!", 90*60)
	m.appendCard(Card{Kind: CardHypothesis, Title: "triggered", Body: "x", Time: time.Now(), Status: "done"})
}

// populateFocusedExpanded: focused card that is also expanded (combined).
func populateFocusedExpanded(m *model) {
	m.appendCard(Card{
		Kind:     CardHypothesis,
		Title:    "Focused & expanded",
		Body:     "short",
		FullBody: "Long detailed body that shows in expanded mode. The card is also focused (thick border) at the same time as expanded (thicker border).",
		Time:     time.Now(), Status: "done", State: cards.StateExpanded,
	})
	m.focusedCardIdx = 0
}

func populateSim(m *model) {
	m.appendCard(Card{
		Kind: CardSimulation, Title: "openmm protein folding",
		Body: "verdict: supports_hypothesis",
		Time: time.Now(), Status: "done",
		Sim: cards.SimFields{
			Engine: "openmm", EngineStatus: "success", Domain: "biology",
			Pattern: "protein_folding", Verdict: "supports_hypothesis",
			CostUSD: 0.012, ElapsedMS: 12450,
		},
	})
	m.appendCard(Card{
		Kind: CardSimulation, Title: "fenicsx elasticity_3d",
		Body: "skipped: no_arm64_wheel",
		Time: time.Now(), Status: "skipped",
		Sim: cards.SimFields{
			Engine: "fenicsx", EngineStatus: "unavailable", Domain: "materials",
			Pattern: "elasticity_3d", InstallHint: "conda install -c conda-forge fenics-dolfinx",
		},
	})
}

func populateCapsim(m *model) {
	m.capsimReport = &capsim.Report{
		Platform: capsim.Platform{System: "Darwin", Arch: "arm64"},
		Hardware: capsim.Hardware{GPUName: "Apple M3 Pro", GPUMemoryGB: 18, CPUCount: 12, RAMGB: 36},
		Engines: []capsim.Engine{
			{ID: "newton", Name: "Newton", Domain: capsim.DomainPhysics, Status: capsim.StatusAvailable, Tier: "fast"},
			{ID: "openmm", Name: "OpenMM", Domain: capsim.DomainBiology, Status: capsim.StatusAvailable, Tier: "slow"},
			{ID: "fenicsx", Name: "FEniCSx", Domain: capsim.DomainPhysics, Status: capsim.StatusUnavailable, InstallHint: "conda install -c conda-forge fenics-dolfinx"},
			{ID: "gromacs", Name: "GROMACS", Domain: capsim.DomainChemistry, Status: capsim.StatusUnavailable},
		},
		Verifiers:      []capsim.Verifier{{ID: "lean4", Available: true, Version: "4.0.0"}},
		ProbeLatencyMS: 1200,
	}
	m.capsimReport.ProbeTimestamp = time.Now()
	m.showCapabilities = true
}

func populateDebug(m *model) {
	m.showDebug = true
	m.simCountThisRun = 3
	m.simSpendThisSession = 0.05
	m.capsimReport = &capsim.Report{
		Engines: []capsim.Engine{
			{Status: capsim.StatusAvailable}, {Status: capsim.StatusAvailable}, {Status: capsim.StatusUnavailable},
		},
	}
}

// snapshotBuilder describes one golden test: a populated model + a name.
type snapshotBuilder struct {
	name  string
	build func(m *model)
}

// TestGoldenSnapshotsAll renders all (fixture, scenario) combinations
// and either writes them to disk (UPDATE=1) or compares against the
// on-disk file.
func TestGoldenSnapshotsAll(t *testing.T) {
	t.Log("TestGoldenSnapshotsAll starting")
	update := os.Getenv("UPDATE") == "1"
	scenarios := []snapshotBuilder{
		{name: "empty", build: populateEmpty},
		{name: "hypothesis", build: populateHypothesis},
		{name: "multi-paper", build: populateMultiPaper},
		{name: "sim", build: populateSim},
		{name: "error", build: populateError},
		{name: "expanded", build: populateExpanded},
		{name: "focused", build: populateFocused},
		{name: "focused-expanded", build: populateFocusedExpanded},
		{name: "full-hypothesis", build: populateFullHypothesis},
		{name: "verdict-chips", build: populateVerdictChips},
		{name: "sim-supports", build: populateSimVerdictSupports},
		{name: "sim-refutes", build: populateSimVerdictRefutes},
		{name: "sim-inconclusive", build: populateSimVerdictInconclusive},
		{name: "sim-skipped", build: populateSimSkipped},
		{name: "bookmark", build: populateBookmark},
		{name: "palette", build: populatePalette},
		{name: "help-shown", build: populateHelpShown},
		{name: "settings-open", build: populateSettingsOpen},
		{name: "achievement-shown", build: populateAchievementShown},
		{name: "mixed-feed", build: populateMixedFeed},
		{name: "capsim", build: populateCapsim},
		{name: "debug", build: populateDebug},
	}

	goldenDir := filepath.Join("tests", "golden")
	if update {
		if err := os.MkdirAll(goldenDir, 0755); err != nil {
			t.Fatal(err)
		}
	}

	for _, f := range goldenFixtures {
		for _, sc := range scenarios {
			m := freshGoldenModel(t, f.W, f.H)
			sc.build(m)
			viewStr := m.View().Content
			clean := renderClean(viewStr)
			file := filepath.Join(goldenDir, f.ID+"-"+sc.name+".txt")

			if update {
				if err := os.WriteFile(file, []byte(clean), 0644); err != nil {
					t.Fatal(err)
				}
				continue
			}
			data, err := os.ReadFile(file)
			if err != nil {
				t.Errorf("missing golden file %s (run with UPDATE=1 to create): %v", file, err)
				continue
			}
			if string(data) != clean {
				t.Errorf("golden mismatch for %s\n--- want ---\n%s\n--- got ---\n%s\n(run with UPDATE=1 to accept)",
					file, string(data), clean)
			}
		}
	}
	// silence unused import warning if any
	_ = time.Second
}
