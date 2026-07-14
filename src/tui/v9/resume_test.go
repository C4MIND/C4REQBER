package tui

import (
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/persist"
)

func TestNewAppRestoresFromFeed(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	// Pre-populate feed.jsonl with 3 entries
	fs, _ := persist.NewFeedStore(50)
	now := time.Now()
	_ = fs.Append(persist.FeedEntry{Title: "old-1", Kind: int(cards.KindHypothesis), Time: now.Add(-2 * time.Hour)})
	_ = fs.Append(persist.FeedEntry{Title: "old-2", Kind: int(cards.KindHypothesis), Time: now.Add(-1 * time.Hour)})
	_ = fs.Append(persist.FeedEntry{Title: "old-3", Kind: int(cards.KindHypothesis), Time: now})

	// Create app — should restore the 3 entries
	m := NewApp("http://test")
	defer m.feedStore.Prune()
	// Count non-empty entries (NewApp appends an Empty card as placeholder;
	// restore happens before that, so the feed has 4 cards total: 3 restored + 1 empty)
	restoredCount := 0
	for _, c := range m.feed {
		if c.Kind != cards.KindEmpty {
			restoredCount++
		}
	}
	if restoredCount != 3 {
		t.Errorf("expected 3 restored cards, got %d (feed size %d)", restoredCount, len(m.feed))
	}
	// Verify chronological order: oldest first
	if m.feed[0].Title != "old-1" {
		t.Errorf("expected first restored to be 'old-1', got %q", m.feed[0].Title)
	}
	if m.feed[2].Title != "old-3" {
		t.Errorf("expected third to be 'old-3' (newest before placeholder), got %q", m.feed[2].Title)
	}
}

func TestNewAppWithNoFeedFileStartsEmpty(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	// Pre-mark first-run done so wizard doesn't take over the screen
	store, _ := persist.New(persist.DefaultPath())
	store.MarkFirstRunDone()
	_ = store.Save()
	m := NewApp("http://test")
	defer m.feedStore.Prune()
	// The empty placeholder card should be there (wizard not active)
	if len(m.feed) != 1 {
		t.Errorf("expected 1 (empty placeholder), got %d (kinds: %v)", len(m.feed), feedKinds(m))
	}
	if m.feed[0].Kind != cards.KindEmpty {
		t.Errorf("expected empty card kind, got %d", m.feed[0].Kind)
	}
}

func feedKinds(m *model) []int {
	out := make([]int, len(m.feed))
	for i, c := range m.feed {
		out[i] = int(c.Kind)
	}
	return out
}
