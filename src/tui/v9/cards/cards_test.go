package cards

import (
	"testing"
)

func TestNextIDMonotonic(t *testing.T) {
	a := NextID()
	b := NextID()
	c := NextID()
	if !(a < b && b < c) {
		t.Errorf("NextID() not monotonic: %d %d %d", a, b, c)
	}
}

func TestKindString(t *testing.T) {
	for k, s := range map[Kind]string{
		KindEmpty:      "empty",
		KindPhase:      "phase",
		KindHypothesis: "hypothesis",
		KindPaper:      "paper",
		KindCode:       "code",
		KindError:      "error",
		KindSimulation: "simulation",
	} {
		if got := k.String(); got != s {
			t.Errorf("Kind(%d).String() = %q, want %q", k, got, s)
		}
	}
}

func TestVerdictIcon(t *testing.T) {
	cases := map[string]string{
		"supports_hypothesis": "◆✓",
		"refutes_hypothesis":  "◆✗",
		"inconclusive":        "◆?",
		"":                    "",
		"unknown":             "",
	}
	for v, want := range cases {
		if got := VerdictIcon(v); got != want {
			t.Errorf("VerdictIcon(%q) = %q, want %q", v, got, want)
		}
	}
}

func TestActionsForHypothesisHasBookmark(t *testing.T) {
	c := Card{Kind: KindHypothesis}
	acts := ActionsFor(c)
	keys := map[string]bool{}
	for _, a := range acts {
		keys[a.Key] = true
	}
	for _, want := range []string{"y", "e", "r", "s", "b"} {
		if !keys[want] {
			t.Errorf("Hypothesis card missing action key %q", want)
		}
	}
}

func TestActionsForSimAvailableAddsOpenPlot(t *testing.T) {
	c := Card{
		Kind: KindSimulation,
		Sim: SimFields{
			EngineStatus: "success",
			Evidence:     SimEvidence{Type: "image", ImageURL: "https://example/plot.png"},
		},
	}
	acts := ActionsFor(c)
	hasOpen := false
	for _, a := range acts {
		if a.Kind == ActOpenPlot {
			hasOpen = true
		}
	}
	if !hasOpen {
		t.Error("available+image sim card should offer 'o' open plot")
	}
}

func TestActionsForSimUnavailableAddsInstallHint(t *testing.T) {
	c := Card{Kind: KindSimulation, Sim: SimFields{EngineStatus: "unavailable"}}
	acts := ActionsFor(c)
	hasInstall := false
	for _, a := range acts {
		if a.Kind == ActInstallHint {
			hasInstall = true
		}
	}
	if !hasInstall {
		t.Error("unavailable sim card should offer 'i' install hint")
	}
}

func TestActionsForSimSkippedAddsFallback(t *testing.T) {
	c := Card{Kind: KindSimulation, Sim: SimFields{EngineStatus: "skipped"}}
	acts := ActionsFor(c)
	hasFallback := false
	for _, a := range acts {
		if a.Kind == ActSelectFallback {
			hasFallback = true
		}
	}
	if !hasFallback {
		t.Error("skipped sim card should offer 'f' fallback picker")
	}
}
