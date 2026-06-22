package persist

import (
	"os"
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

// TestFeedStore_LoadRecent_Dedup guards the v9.13.x fix: achievement cards
// (and any other same-Kind-same-Title entries) that slipped into the feed
// before the LoadFromStore fix must be collapsed on read, so users don't
// see duplicate "First Discovery" / "Quality S" rows forever.
func TestFeedStore_LoadRecent_Dedup(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	now := time.Now()
	// Three duplicate "First Discovery" cards, plus two unique ones.
	_ = f.Append(FeedEntry{Kind: 7, Title: "First Discovery", Time: now.Add(-3 * time.Minute)})
	_ = f.Append(FeedEntry{Kind: 2, Title: "Quality S", Time: now.Add(-2 * time.Minute)})
	_ = f.Append(FeedEntry{Kind: 7, Title: "First Discovery", Time: now.Add(-1 * time.Minute)})
	_ = f.Append(FeedEntry{Kind: 1, Title: "Discovery #1", Time: now})
	_ = f.Append(FeedEntry{Kind: 7, Title: "First Discovery", Time: now.Add(30 * time.Second)})

	got, err := f.LoadRecent(50)
	if err != nil {
		t.Fatal(err)
	}
	// Expected: 3 unique (First Discovery, Quality S, Discovery #1).
	if len(got) != 3 {
		t.Errorf("expected 3 deduped entries, got %d: %+v", len(got), titlesOf(got))
	}
	// Newest "First Discovery" must win (it was appended last).
	seenFirst := 0
	for _, e := range got {
		if e.Title == "First Discovery" {
			seenFirst++
		}
	}
	if seenFirst != 1 {
		t.Errorf("expected exactly 1 First Discovery, got %d", seenFirst)
	}
}

// TestFeedStore_LoadRecent_KeepsBookmarks guards the contract that user
// bookmarks are NEVER deduped (they're explicit user pins, even if the
// title matches a recurring card).
func TestFeedStore_LoadRecent_KeepsBookmarks(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	now := time.Now()
	_ = f.Append(FeedEntry{Kind: 7, Title: "First Discovery", Time: now.Add(-2 * time.Minute), Bookmark: true})
	_ = f.Append(FeedEntry{Kind: 7, Title: "First Discovery", Time: now.Add(-1 * time.Minute)})
	_ = f.Append(FeedEntry{Kind: 7, Title: "First Discovery", Time: now, Bookmark: true})

	got, err := f.LoadRecent(50)
	if err != nil {
		t.Fatal(err)
	}
	// Expected: 1 non-bookmarked "First Discovery" + 2 bookmarked = 3
	bookmarks := 0
	for _, e := range got {
		if e.Title == "First Discovery" && e.Bookmark {
			bookmarks++
		}
	}
	if bookmarks != 2 {
		t.Errorf("expected 2 bookmarked First Discoveries, got %d", bookmarks)
	}
	if len(got) != 3 {
		t.Errorf("expected 3 total (1 normal + 2 bookmarks), got %d: %+v", len(got), titlesOf(got))
	}
}

// TestFeedStore_LoadRecent_DedupWindow guards the over-read of n*2 lines
// before dedup. We append >n*2 unique entries, plus duplicates of the
// oldest kind, then request n. We must get the most recent n, not have
// the dedup window swallow a unique entry.
func TestFeedStore_LoadRecent_DedupWindow(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	now := time.Now()
	// 20 unique entries spanning t-20min to t-1min, plus 3 duplicates of
	// the oldest kind spread throughout.
	for i := 0; i < 20; i++ {
		_ = f.Append(FeedEntry{
			Kind:  100 + i,
			Title: "unique_" + string(rune('a'+i)),
			Time:  now.Add(time.Duration(i-20) * time.Minute),
		})
	}
	// 3 duplicates of the "first" kind (t-20min title).
	_ = f.Append(FeedEntry{Kind: 100, Title: "unique_a", Time: now.Add(-15 * time.Minute)})
	_ = f.Append(FeedEntry{Kind: 100, Title: "unique_a", Time: now.Add(-10 * time.Minute)})
	_ = f.Append(FeedEntry{Kind: 100, Title: "unique_a", Time: now.Add(-5 * time.Minute)})

	got, err := f.LoadRecent(10)
	if err != nil {
		t.Fatal(err)
	}
	// Should get the 10 most recent entries; "unique_a" duplicates dedup'd.
	if len(got) != 10 {
		t.Errorf("expected 10 entries, got %d", len(got))
	}
	// Most recent first.
	if got[0].Time.Before(got[len(got)-1].Time) {
		t.Error("expected most-recent-first ordering")
	}
}

// TestFeedPath_Preferred guards the new unified path (~/.c4reqber) used
// when the directory exists, before the legacy XDG fallback.
func TestFeedPath_Preferred(t *testing.T) {
	tmp := t.TempDir()
	c4dir := filepath.Join(tmp, ".c4reqber")
	if err := os.MkdirAll(c4dir, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	want := filepath.Join(c4dir, "tui-v9-feed.jsonl")
	if f.Path() != want {
		t.Errorf("Path() = %q, want %q (preferred ~/.c4reqber)", f.Path(), want)
	}
}

func titlesOf(es []FeedEntry) []string {
	out := make([]string, len(es))
	for i, e := range es {
		out[i] = e.Title
	}
	return out
}

// BenchmarkFeedStoreLoadRecent_Dedup benchmarks the v9.13.x fix that
// dedupes entries by (Kind, Title) on read. With 1000 entries and 50%
// duplicates, the dedup should remain well under 10ms (it's O(n) with
// a small map lookup per entry, plus an n*2 over-read window).
func BenchmarkFeedStoreLoadRecent_Dedup(b *testing.B) {
	tmp := b.TempDir()
	b.Setenv("HOME", tmp)
	f, _ := NewFeedStore(50)
	now := time.Now()
	// Pre-populate: 500 unique + 500 duplicates of the first 500.
	for i := 0; i < 500; i++ {
		_ = f.Append(FeedEntry{
			Kind:  i,
			Title: "unique_" + string(rune('a'+i%26)),
			Time:  now.Add(time.Duration(i) * time.Millisecond),
		})
	}
	for i := 0; i < 500; i++ {
		_ = f.Append(FeedEntry{
			Kind:  i,
			Title: "unique_" + string(rune('a'+i%26)),
			Time:  now.Add(time.Duration(500+i) * time.Millisecond),
		})
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = f.LoadRecent(50)
	}
}
