package tui

import (
	"strings"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestDebugSnapshotBasic(t *testing.T) {
	m := NewAppFresh("http://test")
	m.width = 160
	m.height = 40
	m.simCountThisRun = 5
	m.simSpendThisSession = 0.0123
	m.capsimReport = &capsim.Report{
		Engines: []capsim.Engine{
			{Status: capsim.StatusAvailable},
			{Status: capsim.StatusAvailable},
			{Status: capsim.StatusUnavailable},
		},
	}
	snap := m.CollectDebugSnapshot()
	if snap.Width != 160 || snap.Height != 40 {
		t.Errorf("size = %d × %d, want 160 × 40", snap.Width, snap.Height)
	}
	if snap.SimCountRun != 5 {
		t.Errorf("SimCountRun = %d, want 5", snap.SimCountRun)
	}
	if snap.SimCost != 0.0123 {
		t.Errorf("SimCost = %f, want 0.0123", snap.SimCost)
	}
	if snap.SimCapabilitySummary == "" {
		t.Error("expected capabilities summary when report is set")
	}
}

func TestRenderDebugOverlayContains(t *testing.T) {
	snap := DebugSnapshot{
		Width:    160,
		Height:   40,
		Tick:     1234,
		FeedLen:  5,
		ZoneIDs:  5,
		Bookmarks: 1,
		SimCountRun: 3,
		SimCountTotal: 2,
		SimCost: 0.05,
		SimCapabilitySummary: "⏚ 28/38 engines",
		Follow:   true,
		Focused:  -1,
		MemoryEst: "~0 KB",
		Toast:    "",
	}
	out := RenderDebugOverlay(snap)
	for _, want := range []string{
		"Debug Overlay",
		"160 × 40",
		"Connection",
		"Feed",
		"Sims",
		"Memory",
		"⏚ 28/38 engines",
		"bookmarks: 1",
	} {
		if !strings.Contains(out, want) {
			t.Errorf("debug overlay missing %q", want)
		}
	}
}

func TestRenderDebugOverlayShowsToast(t *testing.T) {
	snap := DebugSnapshot{Toast: "test toast", FeedLen: 1}
	out := RenderDebugOverlay(snap)
	if !strings.Contains(out, "test toast") {
		t.Error("expected toast in debug overlay")
	}
}

func TestDebugSnapshotBookmarksAndSimCount(t *testing.T) {
	m := NewAppFresh("http://test")
	m.appendCard(cards.Card{Kind: cards.KindHypothesis, Title: "h1", Bookmark: true})
	m.appendCard(cards.Card{Kind: cards.KindHypothesis, Title: "h2"})
	m.appendCard(cards.Card{Kind: cards.KindSimulation, Title: "s1", Sim: cards.SimFields{Engine: "openmm"}})
	m.appendCard(cards.Card{Kind: cards.KindSimulation, Title: "s2", Sim: cards.SimFields{Engine: "fenicsx"}})
	snap := m.CollectDebugSnapshot()
	if snap.Bookmarks != 1 {
		t.Errorf("bookmarks = %d, want 1", snap.Bookmarks)
	}
	if snap.SimCountTotal != 2 {
		t.Errorf("SimCountTotal = %d, want 2", snap.SimCountTotal)
	}
}
