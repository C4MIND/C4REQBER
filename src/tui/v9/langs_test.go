package tui

import (
	"sync"
	"testing"
)

func TestLangs_ConcurrentAddRead_NoRace(t *testing.T) {
	m := NewAppFresh("http://test")
	// 50 writers, 50 readers, 100 iterations each.
	const writers = 50
	const readers = 50
	const iters = 100
	var wg sync.WaitGroup
	wg.Add(writers + readers)
	for w := 0; w < writers; w++ {
		go func(wid int) {
			defer wg.Done()
			for i := 0; i < iters; i++ {
				code := []string{"en", "ru", "zh", "ja", "de", "ar", "hi"}[(wid+i)%7]
				m.addLangSeen(code)
			}
		}(w)
	}
	for r := 0; r < readers; r++ {
		go func() {
			defer wg.Done()
			for i := 0; i < iters; i++ {
				_ = m.snapshotLangsSeen()
				_ = m.langsSeenLen()
				_ = m.hasLangSeen("en")
			}
		}()
	}
	wg.Wait()
	// After all goroutines, map should be non-empty.
	if m.langsSeenLen() == 0 {
		t.Error("expected at least one lang seen after concurrent adds")
	}
}

func TestLangs_AddLangSeenIfAbsent_AtomicCheckThenSet(t *testing.T) {
	m := &model{} // start with empty model, no current lang auto-added
	if !m.addLangSeenIfAbsent("en") {
		t.Error("first add of 'en' should return true")
	}
	if m.addLangSeenIfAbsent("en") {
		t.Error("second add of 'en' should return false (already present)")
	}
	// Empty code is a no-op.
	if m.addLangSeenIfAbsent("") {
		t.Error("empty code should return false")
	}
}

func TestLangs_ReplaceLangsSeen_Overwrites(t *testing.T) {
	m := NewAppFresh("http://test")
	m.addLangSeen("en")
	m.addLangSeen("ru")
	if m.langsSeenLen() != 2 {
		t.Errorf("expected 2 langs, got %d", m.langsSeenLen())
	}
	m.replaceLangsSeen([]string{"zh", "ja", "de"})
	if m.langsSeenLen() != 3 {
		t.Errorf("expected 3 langs after replace, got %d", m.langsSeenLen())
	}
	if m.hasLangSeen("en") {
		t.Error("'en' should have been removed by replace")
	}
	if !m.hasLangSeen("de") {
		t.Error("'de' should be present after replace")
	}
}

func TestLangs_SnapshotLangsSeen_SortedAndIsolated(t *testing.T) {
	m := NewAppFresh("http://test")
	m.addLangSeen("ru")
	m.addLangSeen("en")
	m.addLangSeen("zh")
	snap := m.snapshotLangsSeen()
	// Must be sorted alphabetically.
	if len(snap) != 3 || snap[0] != "en" || snap[1] != "ru" || snap[2] != "zh" {
		t.Errorf("expected [en, ru, zh], got %v", snap)
	}
	// Mutating the snapshot must not affect the model.
	snap[0] = "MUTATED"
	if m.hasLangSeen("MUTATED") {
		t.Error("snapshot mutation leaked into model — must be a deep copy")
	}
}

func TestLangs_NilMapHandled(t *testing.T) {
	// Construct a model manually and ensure addLangSeen handles nil map.
	m := &model{}
	m.addLangSeen("en")
	if !m.hasLangSeen("en") {
		t.Error("addLangSeen should init the map if nil")
	}
}

func TestLangs_ConcurrentSnapshotWhileAdd(t *testing.T) {
	// Stress: one snapshotter racing against an adder for 1000 iters.
	// Run with -race to verify no race.
	m := NewAppFresh("http://test")
	stop := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		for i := 0; i < 1000; i++ {
			select {
			case <-stop:
				return
			default:
			}
			m.addLangSeen("xx")
		}
	}()
	go func() {
		defer wg.Done()
		for i := 0; i < 1000; i++ {
			select {
			case <-stop:
				return
			default:
			}
			_ = m.snapshotLangsSeen()
		}
	}()
	wg.Wait()
}
