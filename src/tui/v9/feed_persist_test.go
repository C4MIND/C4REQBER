package tui

import (
	"fmt"
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

func TestNewAppRestorePreservesIDsAndMouseZones(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)

	original := NewAppFresh("http://test")
	const persistedID = cards.ID(1_000_000)
	original.appendCard(cards.Card{
		ID:    persistedID,
		Kind:  cards.KindHypothesis,
		Title: "restored hypothesis",
		Body:  "evidence",
	})

	restored := NewApp("http://test")
	var found bool
	for _, card := range restored.feed {
		if card.Title == "restored hypothesis" {
			found = true
			if card.ID != persistedID {
				t.Fatalf("restored card ID = %d, want %d", card.ID, persistedID)
			}
		}
	}
	if !found {
		t.Fatal("persisted card was not restored")
	}

	wantZone := fmt.Sprintf("card-%d", persistedID)
	var hasZone bool
	for _, zone := range restored.zoneIDs {
		if zone == wantZone {
			hasZone = true
		}
	}
	if !hasZone {
		t.Fatalf("restored card mouse zone %q not rebuilt: %v", wantZone, restored.zoneIDs)
	}

	restored.appendCard(cards.Card{Kind: cards.KindPaper, Title: "new card"})
	if got := restored.feed[len(restored.feed)-1].ID; got <= persistedID {
		t.Fatalf("new card ID %d collided with restored allocator floor %d", got, persistedID)
	}
}
