package tui

import (
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestAppendCardPersistsToFeedStore(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	m := NewAppFresh("http://test")
	if m.feedStore == nil {
		t.Fatal("feedStore should not be nil when HOME is set")
	}
	before, _ := m.feedStore.LoadRecent(10)
	beforeCount := len(before)
	m.appendCard(cards.Card{Kind: cards.KindHypothesis, Title: "test hyp", Body: "x"})
	after, _ := m.feedStore.LoadRecent(10)
	if len(after) != beforeCount+1 {
		t.Errorf("expected %d, got %d", beforeCount+1, len(after))
	}
	// Verify the new entry is the one we appended (most recent first)
	if after[0].Title != "test hyp" {
		t.Errorf("expected most recent to be 'test hyp', got %q", after[0].Title)
	}
}

func TestAppendCardSimPersistsSimFields(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	m := NewAppFresh("http://test")
	before, _ := m.feedStore.LoadRecent(10)
	beforeCount := len(before)
	m.appendCard(cards.Card{
		Kind:  cards.KindSimulation,
		Title: "openmm run",
		Body:  "x",
		Sim: cards.SimFields{
			Engine:       "openmm",
			EngineStatus: "available",
			Verdict:      "supports_hypothesis",
			CostUSD:      0.005,
			InstallHint:  "conda install x",
		},
	})
	after, _ := m.feedStore.LoadRecent(10)
	if len(after) != beforeCount+1 {
		t.Errorf("expected %d, got %d", beforeCount+1, len(after))
	}
	top := after[0]
	if top.SimEngine != "openmm" {
		t.Errorf("sim engine not persisted: %q", top.SimEngine)
	}
	if top.SimVerdict != "supports_hypothesis" {
		t.Errorf("sim verdict not persisted: %q", top.SimVerdict)
	}
	if top.SimCostUSD != 0.005 {
		t.Errorf("sim cost not persisted: %f", top.SimCostUSD)
	}
}

func TestAppendCardNilFeedStoreDoesNotPanic(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	m := NewAppFresh("http://test")
	m.feedStore = nil // simulate HOME-less environment
	// Should not panic
	m.appendCard(cards.Card{Kind: cards.KindHypothesis, Title: "nohome", Body: "x"})
}
