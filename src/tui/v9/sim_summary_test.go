package tui

import (
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
)

func TestCapSummaryCardBasic(t *testing.T) {
	r := &capsim.Report{
		Platform:       capsim.Platform{System: "Darwin", Arch: "arm64"},
		ProbeLatencyMS: 1200,
		Engines: []capsim.Engine{
			{ID: "newton", Domain: capsim.DomainPhysics, Status: capsim.StatusAvailable},
			{ID: "openmm", Domain: capsim.DomainBiology, Status: capsim.StatusAvailable},
			{ID: "fenicsx", Domain: capsim.DomainPhysics, Status: capsim.StatusUnavailable},
		},
	}
	c := capSummaryCard(r)
	if c.Kind != 6 /* KindSimulation */ {
		t.Errorf("expected simulation card, got kind %d", c.Kind)
	}
	if c.Sim.Engine != "capsim" {
		t.Errorf("expected engine capsim, got %s", c.Sim.Engine)
	}
	if c.Sim.EngineStatus != "available" {
		t.Errorf("expected available, got %s", c.Sim.EngineStatus)
	}
	if c.Body == "" {
		t.Error("body should not be empty")
	}
	if len(c.Sim.PatternsTried) == 0 {
		t.Error("summary should have one PatternsTried per domain")
	}
}

func TestCapUnavailableCardsFilters(t *testing.T) {
	r := &capsim.Report{
		Engines: []capsim.Engine{
			{ID: "newton", Status: capsim.StatusAvailable},
			{ID: "fenicsx", Status: capsim.StatusUnavailable, InstallHint: "conda install fenicsx"},
			{ID: "gromacs", Status: capsim.StatusUnavailable, InstallHint: "apt install gromacs"},
			{ID: "openmm", Status: capsim.StatusAvailable},
		},
	}
	cards := capUnavailableCards(r, 10)
	if len(cards) != 2 {
		t.Fatalf("expected 2 unavailable cards, got %d", len(cards))
	}
	if cards[0].Sim.Engine != "fenicsx" {
		t.Errorf("first should be fenicsx, got %s", cards[0].Sim.Engine)
	}
	if cards[0].Sim.InstallHint == "" {
		t.Error("unavailable card should carry install hint")
	}
}

func TestCapUnavailableCardsRespectsMax(t *testing.T) {
	r := &capsim.Report{
		Engines: []capsim.Engine{
			{ID: "a", Status: capsim.StatusUnavailable},
			{ID: "b", Status: capsim.StatusUnavailable},
			{ID: "c", Status: capsim.StatusUnavailable},
			{ID: "d", Status: capsim.StatusUnavailable},
		},
	}
	cards := capUnavailableCards(r, 2)
	if len(cards) != 2 {
		t.Errorf("expected 2 (capped), got %d", len(cards))
	}
}
