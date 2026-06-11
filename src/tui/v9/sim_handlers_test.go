package tui

import (
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/api"
	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestSimDomainForEngine(t *testing.T) {
	cases := map[string]string{
		"openmm":             "biology",
		"newton":             "physics",
		"pyscf":              "chemistry",
		"gromacs":            "chemistry",
		"mujoco":             "physics",
		"fenicsx":            "materials",
		"xarray":             "climate",
		"mesa":               "economics",
		"rebound":            "astrophysics",
		"unknown_thing":      "general",
		"":                   "general",
	}
	for eng, want := range cases {
		if got := simDomainForEngine(eng); got != want {
			t.Errorf("simDomainForEngine(%q) = %q, want %q", eng, got, want)
		}
	}
}

func TestSimStatusString(t *testing.T) {
	cases := []struct {
		te   api.TypedEvent
		want string
	}{
		{api.TypedEvent{Type: api.EventSimStarted}, "running"},
		{api.TypedEvent{Type: api.EventSimStarted, EngineStatus: "available"}, "available"},
		{api.TypedEvent{Type: api.EventSimFinished, EngineStatus: "success"}, "success"},
		{api.TypedEvent{Type: api.EventSimFinished, EngineStatus: "error"}, "error"},
		{api.TypedEvent{Type: api.EventSimSkipped}, "skipped"},
		{api.TypedEvent{Type: api.EventSimBudgetExceeded}, "budget_exceeded"},
		{api.TypedEvent{Type: api.EventPhaseProgress, EngineStatus: "available"}, "available"},
	}
	for _, c := range cases {
		if got := simStatusString(c.te); got != c.want {
			t.Errorf("simStatusString(%s) = %q, want %q", c.te.Type, got, c.want)
		}
	}
}

func TestSimBody(t *testing.T) {
	cases := []struct {
		name string
		te   api.TypedEvent
		want string
	}{
		{"started", api.TypedEvent{Type: api.EventSimStarted, Engine: "openmm", Pattern: "protein_folding"}, "openmm"},
		{"finished", api.TypedEvent{Type: api.EventSimFinished, ElapsedMS: 1000, CostUSD: 0.001}, "1000ms"},
		{"verdict_finished", api.TypedEvent{Type: api.EventSimFinished, Verdict: "supports", ElapsedMS: 500, CostUSD: 0.01}, "supports"},
		{"skipped", api.TypedEvent{Type: api.EventSimSkipped, Reason: "no_wheel"}, "no_wheel"},
		{"skipped_with_hint", api.TypedEvent{Type: api.EventSimSkipped, Reason: "no_wheel", InstallHint: "conda install x"}, "conda install x"},
		{"budget", api.TypedEvent{Type: api.EventSimBudgetExceeded, CostUSD: 10}, "budget"},
	}
	for _, c := range cases {
		got := simBody(c.te)
		if !contains(got, c.want) {
			t.Errorf("%s: simBody() = %q, expected to contain %q", c.name, got, c.want)
		}
	}
}

func TestHandleSimEventAppendsCard(t *testing.T) {
	m := NewAppFresh("http://test")
	te := api.TypedEvent{
		Type:         api.EventSimFinished,
		Engine:       "openmm",
		Pattern:      "protein_folding",
		EngineStatus: "success",
		Verdict:      "supports_hypothesis",
		ElapsedMS:    1234,
		CostUSD:      0.001,
	}
	m.handleSimEvent(te)
	if len(m.feed) == 0 {
		t.Fatal("expected sim card in feed")
	}
	last := m.feed[len(m.feed)-1]
	if last.Kind != cards.KindSimulation {
		t.Errorf("expected simulation kind, got %d", last.Kind)
	}
	if last.Sim.Engine != "openmm" {
		t.Errorf("engine = %s", last.Sim.Engine)
	}
	if last.Sim.Verdict != "supports_hypothesis" {
		t.Errorf("verdict = %s", last.Sim.Verdict)
	}
	if m.simCountThisRun != 1 {
		t.Errorf("simCountThisRun = %d, want 1", m.simCountThisRun)
	}
}

func TestHandleSimEventSkippedWithInstallHint(t *testing.T) {
	m := NewAppFresh("http://test")
	te := api.TypedEvent{
		Type:       api.EventSimSkipped,
		Engine:     "fenicsx",
		Pattern:    "elasticity_3d",
		Reason:     "no_arm64_wheel",
		InstallHint: "conda install -c conda-forge fenics-dolfinx",
	}
	m.handleSimEvent(te)
	last := m.feed[len(m.feed)-1]
	if last.Sim.EngineStatus != "skipped" {
		t.Errorf("status = %s, want skipped", last.Sim.EngineStatus)
	}
	if last.Sim.InstallHint == "" {
		t.Error("install hint should be set")
	}
}

func TestHandlePhaseEventDedup(t *testing.T) {
	m := NewAppFresh("http://test")
	m.lastPhase = "A"
	m.lastProgress = 0.5
	// Same phase + same progress → should NOT append
	m.handlePhaseEvent(api.TypedEvent{Type: api.EventPhaseProgress, Phase: "A", Progress: 0.5})
	before := len(m.feed)
	m.handlePhaseEvent(api.TypedEvent{Type: api.EventPhaseProgress, Phase: "B", Progress: 0.0})
	after := len(m.feed)
	if after != before+1 {
		t.Errorf("phase change should append exactly one card; before=%d after=%d", before, after)
	}
}

func TestApplySimCostViaTypedEvent(t *testing.T) {
	m := NewAppFresh("http://test")
	te := api.TypedEvent{Type: api.EventCostUpdate, CostUSD: 0.05}
	m.ApplySimCost(te.CostUSD)
	if m.simSpendThisSession != 0.05 {
		t.Errorf("simSpend = %f, want 0.05", m.simSpendThisSession)
	}
}
