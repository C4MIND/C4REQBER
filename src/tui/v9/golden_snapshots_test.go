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
	// Mark first-run done so no wizard takes over the screen
	store, err := persist.New(persist.DefaultPath())
	if err == nil {
		store.MarkFirstRunDone()
		_ = store.Save()
	}
	m := NewApp("http://127.0.0.1:8000")
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
		{name: "sim", build: populateSim},
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
