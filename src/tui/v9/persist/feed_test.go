package persist

import (
	"path/filepath"
	"testing"
	"time"
)

func TestFeedStoreAppendAndLoad(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, err := NewFeedStore(50)
	if err != nil {
		t.Fatal(err)
	}
	if err := f.Append(FeedEntry{Title: "first", Time: time.Now()}); err != nil {
		t.Fatal(err)
	}
	if err := f.Append(FeedEntry{Title: "second", Time: time.Now()}); err != nil {
		t.Fatal(err)
	}
	got, err := f.LoadRecent(10)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 2 {
		t.Fatalf("expected 2, got %d", len(got))
	}
	if got[0].Title != "second" {
		t.Errorf("expected 'second' first, got %q", got[0].Title)
	}
}

func TestFeedStorePruneKeepsBookmarks(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(2) // cap 2
	for i := 0; i < 5; i++ {
		bookmark := i == 2
		_ = f.Append(FeedEntry{
			Title:    "entry_" + string(rune('a'+i)),
			Time:     time.Now(),
			Bookmark: bookmark,
		})
	}
	if err := f.Prune(); err != nil {
		t.Fatal(err)
	}
	got, _ := f.LoadRecent(100)
	// Cap is 2 non-bookmarked; +1 bookmarked = 3 total
	if len(got) != 3 {
		t.Errorf("expected 3 (2 recent + 1 bookmarked), got %d", len(got))
	}
	hasBookmark := false
	for _, e := range got {
		if e.Bookmark {
			hasBookmark = true
		}
	}
	if !hasBookmark {
		t.Error("bookmark was pruned")
	}
}

func TestInputHistoryAddAndDedup(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	h, err := NewInputHistory(10)
	if err != nil {
		t.Fatal(err)
	}
	_ = h.Add("hello", "discover")
	_ = h.Add("world", "discover")
	_ = h.Add("hello", "discover") // should dedup + move to top
	recent := h.Recent(10)
	if len(recent) != 2 {
		t.Fatalf("expected 2 (dedup), got %d", len(recent))
	}
	if recent[0].Text != "hello" {
		t.Errorf("after dedup, 'hello' should be at top, got %q", recent[0].Text)
	}
}

func TestInputHistoryPersistsAcrossInstances(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	h1, _ := NewInputHistory(10)
	_ = h1.Add("persisted", "discover")
	h2, _ := NewInputHistory(10)
	recent := h2.Recent(10)
	if len(recent) != 1 || recent[0].Text != "persisted" {
		t.Errorf("history not persisted: %+v", recent)
	}
}

func TestFeedPath(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	want := filepath.Join(tmp, ".config", "c4reqber", "tui-v9-feed.jsonl")
	if f.Path() != want {
		t.Errorf("Path() = %q, want %q", f.Path(), want)
	}
}

func TestFeedStoreNonExistentLoad(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	got, err := f.LoadRecent(10)
	if err != nil {
		t.Errorf("expected no error on non-existent, got %v", err)
	}
	if len(got) != 0 {
		t.Errorf("expected empty, got %d entries", len(got))
	}
}
