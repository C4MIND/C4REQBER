// Package main — keypress deduplication filter for tmux + bubble tea v2.
//
// Bubble tea v2 + tmux send-keys has a known issue: when keys are sent
// to a pane via `tmux send-keys`, the underlying terminal sometimes
// reports each keypress twice to bubbletea (a quirk of how tmux
// forwards keystrokes through the pane's PTY). This causes
// bubbles/textarea to display double characters like "wwhhaallee"
// instead of "whale".
//
// Production users on iTerm2/Terminal.app/gnome-terminal do not see
// this issue. The filter is a defensive measure that ONLY activates
// when TMUX is set in the environment, so native-terminal users get
// zero overhead and zero risk of dropped keystrokes.
//
// The deduplication window is 50ms — much smaller than human typing
// speed (~150-200ms between keys), so real fast typing still works.
package main

import (
	"os"
	"sync"
	"time"

	tea "charm.land/bubbletea/v2"
)

// KeyDedupWindow is the maximum time between two identical key events
// to consider them duplicates. 50ms is well below human typing speed
// (150-200ms) but enough to swallow tmux's double-forward.
const KeyDedupWindow = 50 * time.Millisecond

// tmuxDetected reports whether we're running under tmux. The result is
// cached on first call (immutable for process lifetime).
var (
	tmuxOnce sync.Once
	tmuxYes  bool
)

func tmuxDetected() bool {
	tmuxOnce.Do(func() {
		tmuxYes = os.Getenv("TMUX") != "" || os.Getenv("TMUX_PANE") != ""
	})
	return tmuxYes
}

// resetTmuxCacheForTest clears the tmux detection cache. Tests use it
// to re-evaluate the TMUX env var after t.Setenv.
func resetTmuxCacheForTest() {
	tmuxOnce = sync.Once{}
	tmuxYes = false
}

// dedupFilter holds the per-filter state for KeyDedupFilter. We
// expose the type so tests can construct a fresh filter and verify
// its behaviour.
type dedupFilter struct {
	mu       sync.Mutex
	lastKey  string
	lastTime time.Time
}

// Filter is the production keypress dedup filter. It is safe for
// concurrent use.
func (d *dedupFilter) Filter(_ tea.Model, msg tea.Msg) tea.Msg {
	// No-op outside tmux — keep native terminals at zero cost.
	if !tmuxDetected() {
		return msg
	}
	kp, ok := msg.(tea.KeyPressMsg)
	if !ok {
		return msg
	}
	key := kp.String()
	now := time.Now()
	d.mu.Lock()
	defer d.mu.Unlock()
	if key == d.lastKey && now.Sub(d.lastTime) < KeyDedupWindow {
		// Drop the duplicate. Returning nil tells bubble tea to
		// skip this message entirely, so the textarea (and any
		// other key handler) never sees it.
		return nil
	}
	d.lastKey = key
	d.lastTime = now
	return msg
}

// newDedupFilter constructs a fresh filter with empty state. Each
// program should get its own filter (one per tea.NewProgram call) to
// avoid cross-program contamination.
func newDedupFilter() *dedupFilter {
	return &dedupFilter{}
}

// KeyDedupFilter returns a tea.ProgramOption that drops duplicate
// KeyPressMsg events arriving within 50ms of each other when running
// under tmux. In native terminals, it is a no-op.
//
// Usage:
//
//	p := tea.NewProgram(app,
//	    tea.WithFPS(60),
//	    KeyDedupFilter(),
//	)
func KeyDedupFilter() tea.ProgramOption {
	df := newDedupFilter()
	return tea.WithFilter(df.Filter)
}
