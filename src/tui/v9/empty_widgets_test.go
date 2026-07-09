package tui

import (
	"strings"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

func TestEmptyWidgets_RendersAllCards(t *testing.T) {
	m := NewAppFresh("http://test")
	widgets := m.emptyWidgets()
	if len(widgets) < 5 {
		t.Errorf("expected at least 5 base-layout widgets, got %d", len(widgets))
	}
	// First card should be the CardEmpty placeholder.
	if widgets[0].Kind != CardEmpty {
		t.Errorf("first widget should be CardEmpty, got %v", widgets[0].Kind)
	}
	// All other widgets should be CardPhase.
	for i, w := range widgets[1:] {
		if w.Kind != CardPhase {
			t.Errorf("widget %d should be CardPhase, got %v", i+1, w.Kind)
		}
	}
}

func TestRenderEmptyWidgets_NonTrivialHeight(t *testing.T) {
	// The empty widgets must collectively produce enough content
	// to fill a 45-line viewport. Otherwise the feed shows a
	// black void ("чернота") below the widgets.
	m := NewAppFresh("http://test")
	out := m.renderEmptyWidgets()
	if len(out) == 0 {
		t.Fatal("renderEmptyWidgets returned empty string")
	}
	// Count newlines — should be at least 20 (7 widgets × ~3-5 lines)
	lines := strings.Count(out, "\n") + 1
	if lines < 20 {
		t.Errorf("base-layout widgets produce only %d lines, expected at least 20", lines)
	}
}

func TestFeedIsEmpty_OnlyCardEmpty(t *testing.T) {
	m := NewAppFresh("http://test")
	// Initial state: only CardEmpty cards in feed (added by NewAppFresh).
	if !m.feedIsEmpty() {
		t.Errorf("expected feedIsEmpty to be true initially, got false (feed len=%d)", len(m.feed))
	}
	// Add a non-empty card; feedIsEmpty should be false.
	m.appendCard(Card{Kind: CardPhase, Title: "test", Body: "test", Time: timeNow()})
	if m.feedIsEmpty() {
		t.Errorf("expected feedIsEmpty to be false after adding CardPhase, got true")
	}
}

func TestTipExample_Rotates(t *testing.T) {
	m := NewAppFresh("http://test")
	// At different tick values, tipExample should return different
	// examples (the rotation logic uses tick/120).
	seen := map[string]bool{}
	for i := 0; i < 30; i++ {
		m.tick = i * 100
		seen[m.tipExample()] = true
	}
	if len(seen) < 3 {
		t.Errorf("tipExample should rotate through multiple examples, only saw %d unique", len(seen))
	}
}

func TestTipShortcuts_PlatformAware(t *testing.T) {
	// tipShortcuts renders via the global i18n lang; pin EN so a leaked
	// non-English lang from another test can't flip the asserted labels.
	original := i18n.GetLang()
	defer SetLang(original)
	SetLang(i18n.LangEN)
	m := NewAppFresh("http://test")
	out := m.tipShortcuts()
	if !strings.Contains(out, m.keymap.Label(ActRun)) {
		t.Errorf("tipShortcuts should contain keymap label for ActRun (%q), got: %q",
			m.keymap.Label(ActRun), out)
	}
	if !strings.Contains(out, "Help") {
		t.Errorf("tipShortcuts should contain 'Help' text, got: %q", out)
	}
}

func TestEmptyWidgets_StableTimestamps(t *testing.T) {
	// All widgets in the same empty state must have distinct
	// timestamps (so bubblezone IDs are unique across cards).
	m := NewAppFresh("http://test")
	widgets := m.emptyWidgets()
	seen := map[int64]bool{}
	for i, w := range widgets {
		ts := w.Time.UnixNano()
		if seen[ts] {
			t.Errorf("widget %d has duplicate timestamp %d", i, ts)
		}
		seen[ts] = true
	}
}
