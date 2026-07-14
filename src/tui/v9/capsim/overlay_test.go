package capsim

import (
	"strings"
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

func TestRenderOverlayFallback(t *testing.T) {
	out := RenderCapabilitiesOverlay(120, 40, nil)
	if !strings.Contains(out, "⏚") {
		t.Error("expected title glyph in overlay")
	}
}

func TestRenderOverlayWithData(t *testing.T) {
	r := &Report{
		Platform:       Platform{System: "Darwin", Arch: "arm64"},
		Hardware:       Hardware{GPUName: "Apple M3 Pro", GPUMemoryGB: 18, CPUCount: 12, RAMGB: 36},
		Engines: []Engine{
			{ID: "newton", Name: "Newton", Domain: DomainPhysics, Status: StatusAvailable, Tier: "fast"},
			{ID: "fenicsx", Name: "FEniCSx", Domain: DomainPhysics, Status: StatusUnavailable, Tier: "linux_only", InstallHint: "conda install -c conda-forge fenics-dolfinx"},
			{ID: "openmm", Name: "OpenMM", Domain: DomainBiology, Status: StatusAvailable, Tier: "slow"},
		},
		Verifiers: []Verifier{
			{ID: "lean4", Available: true, Version: "4.0.0"},
		},
		ProbeTimestamp: time.Now(),
		ProbeLatencyMS: 1200,
	}
	out := RenderCapabilitiesOverlay(120, 40, r)
	for _, want := range []string{"Newton", "FEniCSx", "conda install -c conda-forge fenics-dolfinx", "physics", "Verification", "Apple M3 Pro"} {
		if !strings.Contains(out, want) {
			t.Errorf("overlay missing %q", want)
		}
	}
}

func TestShortSummary(t *testing.T) {
	defer i18n.SetLang(i18n.LangEN)
	i18n.SetLang(i18n.LangEN)
	r := &Report{
		Engines: []Engine{
			{Status: StatusAvailable},
			{Status: StatusAvailable},
			{Status: StatusUnavailable},
		},
	}
	got := ShortSummary(r)
	want := "⏚ 2/3 engines"
	if got != want {
		t.Errorf("ShortSummary = %q, want %q", got, want)
	}
	if ShortSummary(nil) != "" {
		t.Error("ShortSummary(nil) should return empty string")
	}
}
