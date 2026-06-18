package tui

import (
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestVerdictChipsNoSims(t *testing.T) {
	m := NewAppFresh("http://test")
	if got := verdictChips(m, 42); got != "" {
		t.Errorf("expected empty for unknown hyp id, got %q", got)
	}
}

func TestVerdictChipsWithLinkedSim(t *testing.T) {
	m := NewAppFresh("http://test")
	hypID := cards.NextID()
	m.appendCard(cardHyp("test hypothesis", hypID))
	m.appendCard(cardSim(hypID, "openmm", "supports_hypothesis"))
	m.appendCard(cardSim(hypID, "fenicsx", "refutes_hypothesis"))
	got := verdictChips(m, hypID)
	if got == "" {
		t.Fatal("expected chips for linked sims")
	}
	if !strContains(got, "1/2 supported") {
		t.Errorf("expected '1/2 supported' in %q", got)
	}
	if !strContains(got, "1 refuted") {
		t.Errorf("expected '1 refuted' in %q", got)
	}
}

func TestVerdictChipsOnlyInconclusive(t *testing.T) {
	m := NewAppFresh("http://test")
	hypID := cards.NextID()
	m.appendCard(cardHyp("h", hypID))
	m.appendCard(cardSim(hypID, "openmm", "inconclusive"))
	m.appendCard(cardSim(hypID, "gromacs", "inconclusive"))
	got := verdictChips(m, hypID)
	if got == "" {
		t.Fatal("expected chips")
	}
	if !strContains(got, "2 inconclusive") {
		t.Errorf("expected '2 inconclusive' in %q", got)
	}
}

func cardHyp(title string, id cards.ID) cards.Card {
	return cards.Card{ID: id, Kind: cards.KindHypothesis, Title: title, Body: "h body", Time: time.Now()}
}

func cardSim(hypID cards.ID, engine, verdict string) cards.Card {
	return cards.Card{
		ID:    cards.NextID(),
		Kind:  cards.KindSimulation,
		Title: engine + " test",
		Body:  "x",
		Time:  time.Now(),
		Sim: cards.SimFields{
			Engine:       engine,
			EngineStatus: "success",
			Verdict:      verdict,
			HypothesisID: hypID,
		},
	}
}

func strContains(s, sub string) bool {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}
