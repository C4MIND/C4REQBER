package tui

import "testing"

func TestConnGlyphAndLabel(t *testing.T) {
	cases := []struct {
		state ConnectionState
		want  string
	}{
		{ConnLive, "●"},
		{ConnPolling, "◐"},
		{ConnOffline, "○"},
		{ConnUnknown, "?"},
	}
	for _, c := range cases {
		if got := ConnGlyph(c.state); got != c.want {
			t.Errorf("ConnGlyph(%d) = %q, want %q", c.state, got, c.want)
		}
	}
}

func TestStatusBarEmptyWhenToggledOff(t *testing.T) {
	m := NewAppFresh("http://test")
	m.showStatusBar = false
	m.width = 160
	if got := m.renderStatusBar(); got != "" {
		t.Errorf("expected empty status bar, got %q", got)
	}
}

func TestStatusBarEmptyWhenTooNarrow(t *testing.T) {
	m := NewAppFresh("http://test")
	m.showStatusBar = true
	m.width = 80 // T0/T1 — should suppress
	if got := m.renderStatusBar(); got != "" {
		t.Errorf("T0 should not render status bar, got %q", got)
	}
}

func TestStatusBarRendersAtT2(t *testing.T) {
	m := NewAppFresh("http://test")
	m.showStatusBar = true
	m.width = 160
	m.height = 40
	m.connState = ConnLive
	m.follow = true
	m.capsimReport = nil
	got := m.renderStatusBar()
	if got == "" {
		t.Fatal("T2 with showStatusBar=true should render")
	}
	// Should contain the live glyph
	if !contains(got, "●") {
		t.Errorf("expected live glyph in %q", got)
	}
	// Should mention follow
	if !contains(got, "follow") {
		t.Errorf("expected follow label in %q", got)
	}
}

// contains is a small helper to avoid pulling strings for substring checks.
func contains(s, sub string) bool {
	return len(s) >= len(sub) && (len(sub) == 0 || indexOf(s, sub) >= 0)
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}
