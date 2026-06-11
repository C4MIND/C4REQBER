package tui

import (
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestSimExplorerUnlocksAt5(t *testing.T) {
	as := NewAchievements()
	// 4 distinct successful engines → still locked
	feed := []cards.Card{
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "newton", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "jaxsim", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "openmm", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "tellurium", EngineStatus: "success"}},
	}
	as.CheckSimAchievements(feed)
	if as.Items[7].Unlocked { // AchSimExplorer is index 7
		t.Error("should still be locked at 4 engines")
	}
	// 5th engine unlocks
	feed = append(feed, cards.Card{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "vina", EngineStatus: "success"}})
	unlocked := as.CheckSimAchievements(feed)
	if !as.Items[7].Unlocked {
		t.Error("should unlock at 5 engines")
	}
	if len(unlocked) != 1 {
		t.Errorf("expected 1 unlock, got %d", len(unlocked))
	}
}

func TestSimSaverUnlocksOnRefutes(t *testing.T) {
	as := NewAchievements()
	unlocked := as.CheckSimAchievements([]cards.Card{
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "openmm", Verdict: "supports_hypothesis"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "jaxsim", Verdict: "refutes_hypothesis"}},
	})
	if !as.Items[8].Unlocked { // AchSimSaver
		t.Error("should unlock on refutes verdict")
	}
	if len(unlocked) != 1 {
		t.Errorf("expected 1 unlock, got %d", len(unlocked))
	}
}

func TestSimChefUnlocksAt3Fallbacks(t *testing.T) {
	as := NewAchievements()
	// 2 skipped → still locked
	feed := []cards.Card{
		{Kind: cards.KindSimulation, Sim: cards.SimFields{EngineStatus: "skipped"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{EngineStatus: "unavailable"}},
	}
	as.CheckSimAchievements(feed)
	if as.Items[9].Unlocked { // AchSimChef
		t.Error("should still be locked at 2 fallbacks")
	}
	// 3rd skipped → unlocks
	feed = append(feed, cards.Card{Kind: cards.KindSimulation, Sim: cards.SimFields{EngineStatus: "skipped"}})
	unlocked := as.CheckSimAchievements(feed)
	if !as.Items[9].Unlocked {
		t.Error("should unlock at 3 fallbacks")
	}
	if len(unlocked) != 1 {
		t.Errorf("expected 1 unlock, got %d", len(unlocked))
	}
}

func TestSimDelegateUnlocks(t *testing.T) {
	as := NewAchievements()
	unlocked := as.CheckSimAchievements([]cards.Card{
		{Kind: cards.KindSimulation, Sim: cards.SimFields{EngineStatus: "delegated"}},
	})
	if !as.Items[10].Unlocked { // AchSimDelegate
		t.Error("should unlock on delegated sim")
	}
	if len(unlocked) != 1 {
		t.Errorf("expected 1 unlock, got %d", len(unlocked))
	}
}

func TestSimAchievementsDontRepeat(t *testing.T) {
	as := NewAchievements()
	// Trigger AchSimExplorer once
	feed := []cards.Card{
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "a", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "b", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "c", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "d", EngineStatus: "success"}},
		{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "e", EngineStatus: "success"}},
	}
	first := as.CheckSimAchievements(feed)
	if len(first) != 1 {
		t.Fatalf("expected 1 unlock first time, got %d", len(first))
	}
	second := as.CheckSimAchievements(feed)
	if len(second) != 0 {
		t.Errorf("should not re-unlock; got %d", len(second))
	}
}

func TestSimAchievementsIgnoresNonSimCards(t *testing.T) {
	as := NewAchievements()
	// 100 hypothesis cards — should not affect sim achievements
	feed := make([]cards.Card, 100)
	for i := range feed {
		feed[i] = cards.Card{Kind: cards.KindHypothesis, Title: "h"}
	}
	unlocked := as.CheckSimAchievements(feed)
	if len(unlocked) != 0 {
		t.Errorf("expected 0 sim unlocks from 100 hypothesis cards, got %d", len(unlocked))
	}
}

func TestAchievementTotalCount(t *testing.T) {
	as := NewAchievements()
	if as.Total != 11 {
		t.Errorf("expected 11 total achievements (7 original + 4 sim), got %d", as.Total)
	}
	if len(as.Items) != 11 {
		t.Errorf("expected 11 items, got %d", len(as.Items))
	}
}
