package tui

import "testing"

func TestComputeLayoutT0(t *testing.T) {
	l := ComputeLayout(80, 24, false)
	if l.Tier != TierMinimal {
		t.Errorf("T0 expected, got tier %d", l.Tier)
	}
	if l.Input.H != 1 {
		t.Errorf("T0 input should be 1 row, got %d", l.Input.H)
	}
	if l.Footer.H != 1 {
		t.Errorf("T0 footer should be 1 row, got %d", l.Footer.H)
	}
	if l.HasRightRail {
		t.Error("T0 should not have right rail")
	}
	if l.IsCompact != true {
		t.Error("T0 should be compact")
	}
}

func TestComputeLayoutT1(t *testing.T) {
	l := ComputeLayout(120, 30, false)
	if l.Tier != TierCompact {
		t.Errorf("T1 expected, got tier %d", l.Tier)
	}
	if l.Input.H != 3 {
		t.Errorf("T1 input should be 3 rows, got %d", l.Input.H)
	}
	if l.Footer.H != 1 {
		t.Errorf("T1 footer should be 1 row, got %d", l.Footer.H)
	}
	if l.StatusBar.H != 0 {
		t.Error("T1 should not have status bar (too narrow)")
	}
}

func TestComputeLayoutT2(t *testing.T) {
	l := ComputeLayout(160, 45, true)
	if l.Tier != TierStandard {
		t.Errorf("T2 expected, got tier %d", l.Tier)
	}
	if l.Footer.H != 2 {
		t.Errorf("T2 footer should be 2 rows, got %d", l.Footer.H)
	}
	if l.StatusBar.H != 1 {
		t.Errorf("T2 with showStatusBar=true should have 1-row status bar, got %d", l.StatusBar.H)
	}
	if l.HasRightRail {
		t.Error("T2 should not have right rail")
	}
}

func TestComputeLayoutT3(t *testing.T) {
	l := ComputeLayout(220, 60, true)
	if l.Tier != TierSpacious {
		t.Errorf("T3 expected, got tier %d", l.Tier)
	}
	if !l.HasRightRail {
		t.Error("T3 should have right rail")
	}
	if l.RightRail.W < 20 {
		t.Errorf("T3 right rail should be ≥20 cols, got %d", l.RightRail.W)
	}
	if l.Feed.W+l.RightRail.W > l.Width {
		t.Errorf("feed (%d) + rightRail (%d) > width (%d)", l.Feed.W, l.RightRail.W, l.Width)
	}
}

func TestComputeLayoutHeightDemotion(t *testing.T) {
	// 200x10 would normally be T3, but height < 18 → demote to T0
	l := ComputeLayout(200, 10, true)
	if l.Tier != TierMinimal {
		t.Errorf("height-demote: 200x10 should be T0, got T%d", l.Tier)
	}
	// 200x20 would normally be T3, but height < 24 → demote to T1
	l2 := ComputeLayout(200, 20, true)
	if l2.Tier > TierCompact {
		t.Errorf("height-demote: 200x20 should be ≤T1, got T%d", l2.Tier)
	}
}

func TestComputeLayoutFeedNeverZero(t *testing.T) {
	// Even in extreme conditions, the feed should be at least 3 rows
	for _, dims := range [][2]int{{60, 18}, {100, 24}, {200, 50}, {300, 100}} {
		l := ComputeLayout(dims[0], dims[1], true)
		if l.Feed.H < 3 {
			t.Errorf("feed too small at %dx%d: %d", dims[0], dims[1], l.Feed.H)
		}
		if l.Feed.W < 30 {
			t.Errorf("feed too narrow at %dx%d: %d", dims[0], dims[1], l.Feed.W)
		}
	}
}
