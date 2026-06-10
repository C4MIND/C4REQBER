package main

import (
	"sync"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
)

func TestDedupFilter_NoTmux_PassThrough(t *testing.T) {
	// When TMUX is not set, the filter must be a complete no-op.
	t.Setenv("TMUX", "")
	t.Setenv("TMUX_PANE", "")
	resetTmuxCacheForTest()

	d := newDedupFilter()
	// Fire two identical 'a' keys back-to-back. In native mode, BOTH
	// must pass (the filter is a no-op).
	for i := 0; i < 2; i++ {
		if got := d.Filter(nil, tea.KeyPressMsg{Code: 'a'}); got == nil {
			t.Fatalf("filter dropped a key in native mode (call %d) — must be a no-op", i)
		}
	}
}

func TestDedupFilter_Tmux_DropsDuplicates(t *testing.T) {
	t.Setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
	resetTmuxCacheForTest()

	d := newDedupFilter()

	// First 'w' should pass.
	if got := d.Filter(nil, tea.KeyPressMsg{Code: 'w'}); got == nil {
		t.Fatal("first 'w' should pass through")
	}
	// Second 'w' within 50ms should be dropped.
	if got := d.Filter(nil, tea.KeyPressMsg{Code: 'w'}); got != nil {
		t.Fatal("second 'w' within 50ms should be dropped")
	}
	// Third 'w' (still within 50ms) should also be dropped.
	if got := d.Filter(nil, tea.KeyPressMsg{Code: 'w'}); got != nil {
		t.Fatal("third 'w' within 50ms should be dropped")
	}
	// Different key 'h' should pass.
	if got := d.Filter(nil, tea.KeyPressMsg{Code: 'h'}); got == nil {
		t.Fatal("different key 'h' should pass through")
	}
	// 'h' again within 50ms should be dropped (lastKey is now 'h').
	if got := d.Filter(nil, tea.KeyPressMsg{Code: 'h'}); got != nil {
		t.Fatal("'h' again within 50ms should be dropped (lastKey is 'h')")
	}
	// A different key 'w' (after the 50ms window for 'h') should pass.
	time.Sleep(KeyDedupWindow + 5*time.Millisecond)
	if got := d.Filter(nil, tea.KeyPressMsg{Code: 'w'}); got == nil {
		t.Fatal("'w' after window should pass (different from lastKey 'h')")
	}
}

func TestDedupFilter_Tmux_AllowsGenuinelyDoubleKeypresses(t *testing.T) {
	t.Setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
	resetTmuxCacheForTest()

	d := newDedupFilter()

	// First 's' passes.
	if d.Filter(nil, tea.KeyPressMsg{Code: 's'}) == nil {
		t.Fatal("first 's' should pass")
	}
	// Wait > KeyDedupWindow so the next 's' is NOT a duplicate.
	time.Sleep(KeyDedupWindow + 10*time.Millisecond)
	// Second 's' should pass too (real keystroke, not a tmux echo).
	if d.Filter(nil, tea.KeyPressMsg{Code: 's'}) == nil {
		t.Fatal("second 's' after 60ms should pass (real keypress)")
	}
}

func TestDedupFilter_Tmux_PassesNonKeyMessages(t *testing.T) {
	t.Setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
	resetTmuxCacheForTest()

	d := newDedupFilter()

	// Non-key messages must always pass through, even in tmux mode.
	mouse := tea.MouseClickMsg{X: 10, Y: 5, Button: tea.MouseLeft}
	if got := d.Filter(nil, mouse); got == nil {
		t.Fatal("MouseClickMsg must not be dropped by key dedup filter")
	}
	ws := tea.WindowSizeMsg{Width: 200, Height: 50}
	if got := d.Filter(nil, ws); got == nil {
		t.Fatal("WindowSizeMsg must not be dropped by key dedup filter")
	}
	// Tick messages also pass (they're not keys).
	tick := tickMsg(time.Now())
	if got := d.Filter(nil, tick); got == nil {
		t.Fatal("tickMsg must not be dropped by key dedup filter")
	}
}

func TestDedupFilter_ConcurrentAccess(t *testing.T) {
	// Stress test: 50 goroutines, each sending 50 events with mixed keys.
	// Run with `go test -race` to verify the mutex is correct.
	t.Setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
	resetTmuxCacheForTest()

	d := newDedupFilter()
	const goroutines = 50
	const eventsPer = 50
	var wg sync.WaitGroup
	wg.Add(goroutines)
	for g := 0; g < goroutines; g++ {
		go func(gid int) {
			defer wg.Done()
			for i := 0; i < eventsPer; i++ {
				// Mix different keys to exercise the lock with
				// varying state transitions.
				kp := tea.KeyPressMsg{Code: rune('a' + (gid+i)%26)}
				_ = d.Filter(nil, kp)
			}
		}(g)
	}
	wg.Wait()
}

func TestTmuxDetected_CachesAfterFirstCall(t *testing.T) {
	// Set TMUX before first call.
	t.Setenv("TMUX", "/tmp/tmux-test,1,0")
	resetTmuxCacheForTest()

	if !tmuxDetected() {
		t.Fatal("tmuxDetected should return true when TMUX is set")
	}
	// Now unset TMUX; tmuxDetected must still return true (cached).
	t.Setenv("TMUX", "")
	if !tmuxDetected() {
		t.Fatal("tmuxDetected should cache the first result")
	}
}

func TestDedupFilter_HandlesSpecialKeys(t *testing.T) {
	t.Setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
	resetTmuxCacheForTest()

	d := newDedupFilter()
	// Tab should not be deduped with Enter — different .String() values.
	if d.Filter(nil, tea.KeyPressMsg{Code: '\t'}) == nil {
		t.Fatal("Tab should pass on first call")
	}
	// Same Tab within 50ms should be dropped (lastKey is "tab").
	if got := d.Filter(nil, tea.KeyPressMsg{Code: '\t'}); got != nil {
		t.Fatal("same Tab within window should be dropped")
	}
	// Enter is a different key — should pass (and update lastKey to "enter").
	if d.Filter(nil, tea.KeyPressMsg{Code: '\r'}) == nil {
		t.Fatal("Enter should pass (different key from tab)")
	}
	// Enter again within 50ms should be dropped.
	if got := d.Filter(nil, tea.KeyPressMsg{Code: '\r'}); got != nil {
		t.Fatal("same Enter within window should be dropped")
	}
}

// tickMsg is a minimal non-key message for testing.
type tickMsg time.Time

func (t tickMsg) String() string { return "tick" }
