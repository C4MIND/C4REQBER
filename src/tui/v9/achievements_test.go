package tui

import (
	"path/filepath"
	"sync"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/persist"
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

// TestAchievementSystem_LoadFromStore guards the v9.13.x regression where
// every TUI restart re-unlocked previously-unlocked achievements, which
// re-appended achievement cards in the feed on every session.
func TestAchievementSystem_LoadFromStore(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, err := persist.New(path)
	if err != nil {
		t.Fatal(err)
	}
	// Mark 3 achievements as already unlocked in the store.
	s.AddAchievement(int(AchFirstDiscovery))
	s.AddAchievement(int(AchQualityS))
	s.AddAchievement(int(AchLinguist))

	as := NewAchievements()
	if as.Unlocked != 0 {
		t.Fatalf("fresh system should have 0 unlocked, got %d", as.Unlocked)
	}
	as.LoadFromStore(s)

	if as.Unlocked != 3 {
		t.Errorf("expected 3 hydrated unlocks, got %d", as.Unlocked)
	}
	if !as.Items[AchFirstDiscovery].Unlocked {
		t.Error("AchFirstDiscovery should be hydrated as unlocked")
	}
	if !as.Items[AchQualityS].Unlocked {
		t.Error("AchQualityS should be hydrated as unlocked")
	}
	if !as.Items[AchLinguist].Unlocked {
		t.Error("AchLinguist should be hydrated as unlocked")
	}
	// AchMultiPaper (not in store) should still be locked.
	if as.Items[AchMultiPaper].Unlocked {
		t.Error("AchMultiPaper should still be locked (not in store)")
	}
}

// TestAchievementSystem_LoadFromStore_NilStore guards the
// "load from store must not panic when store is nil" contract.
func TestAchievementSystem_LoadFromStore_NilStore(t *testing.T) {
	as := NewAchievements()
	// Must not panic.
	as.LoadFromStore(nil)
	if as.Unlocked != 0 {
		t.Errorf("LoadFromStore(nil) should be a no-op, got Unlocked=%d", as.Unlocked)
	}
}

// TestAchievementSystem_LoadFromStore_Idempotent: loading the same store
// twice must not double-count.
func TestAchievementSystem_LoadFromStore_Idempotent(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := persist.New(path)
	s.AddAchievement(int(AchFirstDiscovery))

	as := NewAchievements()
	as.LoadFromStore(s)
	as.LoadFromStore(s)
	as.LoadFromStore(s)
	if as.Unlocked != 1 {
		t.Errorf("triple load should still be 1, got %d", as.Unlocked)
	}
}

// TestAchievementSystem_Check_NoReUnlockAfterLoadFromStore locks the
// end-to-end fix: after hydration, Check() must NOT re-unlock the same
// achievement (which used to re-append the achievement card every
// session — the root cause of the duplicate-cards-in-feed bug).
func TestAchievementSystem_Check_NoReUnlockAfterLoadFromStore(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := persist.New(path)
	s.AddAchievement(int(AchFirstDiscovery))

	as := NewAchievements()
	as.LoadFromStore(s)
	// FirstDiscovery: needs 1 discovery, we have 0 → still no re-unlock.
	// Pass discoveries=1 to TRIGGER a re-evaluation; the loaded-first-
	// discovery should NOT show up in the unlocked list.
	unlocked := as.Check(1, 0.5, 1, 0, []string{"EN"})
	for _, a := range unlocked {
		if a.Kind == AchFirstDiscovery {
			t.Errorf("FirstDiscovery re-unlocked after LoadFromStore: %+v", a)
		}
	}
}

// TestAchievementSystem_ConcurrentCheck guards the sync.Mutex added to
// Check() in v9.13.x. Run under `go test -race`.
func TestAchievementSystem_ConcurrentCheck(t *testing.T) {
	as := NewAchievements()
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			as.Check(n+1, 0.95, 5, 10, []string{"EN", "RU", "ZH"})
			as.CheckSimAchievements([]cards.Card{
				{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "newton", EngineStatus: "success"}},
				{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "jaxsim", EngineStatus: "success"}},
				{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "openmm", EngineStatus: "success"}},
				{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "tellurium", EngineStatus: "success"}},
				{Kind: cards.KindSimulation, Sim: cards.SimFields{Engine: "vina", EngineStatus: "success"}},
			})
		}(i)
	}
	wg.Wait()
	if as.Unlocked < 4 {
		t.Errorf("after concurrent Check, expected ≥4 unlocks, got %d", as.Unlocked)
	}
}
