package tui

import (
	"testing"
)

func TestAchievementFirstDiscovery(t *testing.T) {
	a := NewAchievements()
	// 0 discoveries → no unlock
	got := a.Check(0, 0, 0, 0, nil)
	if len(got) != 0 {
		t.Errorf("got %d unlocks for 0 discoveries", len(got))
	}
	// 1 discovery → unlock FirstDiscovery
	got = a.Check(1, 0, 0, 0, nil)
	if len(got) != 1 {
		t.Errorf("got %d unlocks for 1 discovery, want 1", len(got))
	}
	if got[0].Kind != AchFirstDiscovery {
		t.Errorf("wrong kind unlocked: %d", got[0].Kind)
	}
}

func TestAchievementQualityS(t *testing.T) {
	a := NewAchievements()
	got := a.Check(1, 0.85, 5, 60, []string{"EN"})
	// 1 discovery + quality 0.85 + 5 papers = First + QualityS + MultiPaper
	if len(got) != 3 {
		t.Errorf("got %d unlocks, want 3 (first + qualityS + multiPaper)", len(got))
	}
	// Specifically check that QualityS is in there
	found := false
	for _, u := range got {
		if u.Kind == AchQualityS {
			found = true
		}
	}
	if !found {
		t.Error("QualityS not unlocked for quality=0.85")
	}
}

func TestAchievementMultiPaper(t *testing.T) {
	a := NewAchievements()
	got := a.Check(1, 0, 5, 60, nil)
	found := false
	for _, u := range got {
		if u.Kind == AchMultiPaper {
			found = true
		}
	}
	if !found {
		t.Error("multi-paper not unlocked for 5 papers")
	}
}

func TestAchievementSpeedster(t *testing.T) {
	a := NewAchievements()
	got := a.Check(1, 0, 0, 20, nil) // 20s < 30s
	found := false
	for _, u := range got {
		if u.Kind == AchSpeedster {
			found = true
		}
	}
	if !found {
		t.Error("speedster not unlocked for 20s discovery")
	}
	got2 := a.Check(1, 0, 0, 60, nil) // 60s > 30s
	for _, u := range got2 {
		if u.Kind == AchSpeedster {
			t.Error("speedster should NOT unlock for 60s discovery")
		}
	}
}

func TestAchievementLinguist(t *testing.T) {
	a := NewAchievements()
	got := a.Check(1, 0, 0, 60, []string{"EN", "RU", "ZH", "JA"})
	found := false
	for _, u := range got {
		if u.Kind == AchLinguist {
			found = true
		}
	}
	if !found {
		t.Error("linguist not unlocked for 4 langs")
	}
}

func TestAchievementStreak(t *testing.T) {
	a := NewAchievements()
	got := a.Check(5, 0, 0, 60, nil)
	found := false
	for _, u := range got {
		if u.Kind == AchStreak {
			found = true
		}
	}
	if !found {
		t.Error("streak not unlocked for 5 discoveries")
	}
}

func TestAchievementIdempotent(t *testing.T) {
	a := NewAchievements()
	got1 := a.Check(1, 0.85, 5, 20, []string{"EN", "RU", "ZH", "JA", "DE", "AR", "HI"})
	// Same params → no new unlocks
	got2 := a.Check(1, 0.85, 5, 20, []string{"EN", "RU", "ZH", "JA", "DE", "AR", "HI"})
	if len(got1) == 0 {
		t.Error("first call should unlock something")
	}
	if len(got2) != 0 {
		t.Errorf("second call (same state) should NOT unlock anything, got %d", len(got2))
	}
}

func TestAchievementAllUnlock(t *testing.T) {
	a := NewAchievements()
	// Optimal conditions
	a.Check(10, 0.95, 5, 15, []string{"EN", "RU", "ZH", "JA", "DE", "AR", "HI"})
	if a.Unlocked != 7 {
		t.Errorf("got %d/7 unlocked", a.Unlocked)
	}
}

func TestCycleLangName(t *testing.T) {
	cycle := []struct{ from, to string }{
		{"en", "ru"}, {"ru", "zh"}, {"zh", "ja"}, {"ja", "de"}, {"de", "ar"}, {"ar", "hi"}, {"hi", "en"},
	}
	for _, c := range cycle {
		got := cycleLangName(langFromString(c.from))
		if string(got) != c.to {
			t.Errorf("cycleLangName(%s) = %s, want %s", c.from, got, c.to)
		}
	}
}
