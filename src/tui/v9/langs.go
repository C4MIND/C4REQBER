package tui

import (
	"sync"
)

// addLangSeen records a lang code in the model's langsSeen map under
// a write lock. Use this instead of writing to m.langsSeen directly.
func (m *model) addLangSeen(code string) {
	if code == "" {
		return
	}
	m.langsMu.Lock()
	defer m.langsMu.Unlock()
	if m.langsSeen == nil {
		m.langsSeen = make(map[string]bool)
	}
	m.langsSeen[code] = true
}

// hasLangSeen reports whether code is in the langsSeen map. The
// result is a snapshot — callers that need atomic check-then-set
// should use addLangSeenIfAbsent instead.
func (m *model) hasLangSeen(code string) bool {
	m.langsMu.RLock()
	defer m.langsMu.RUnlock()
	return m.langsSeen[code]
}

// addLangSeenIfAbsent is an atomic check-then-set. Returns true if
// the code was newly added, false if it was already present.
func (m *model) addLangSeenIfAbsent(code string) bool {
	if code == "" {
		return false
	}
	m.langsMu.Lock()
	defer m.langsMu.Unlock()
	if m.langsSeen == nil {
		m.langsSeen = make(map[string]bool)
	}
	if m.langsSeen[code] {
		return false
	}
	m.langsSeen[code] = true
	return true
}

// snapshotLangsSeen returns a copy of the langsSeen map. The copy is
// safe to iterate without holding the lock. Returned slice is
// deterministically ordered (sorted) for stable test output and
// stable disk writes.
func (m *model) snapshotLangsSeen() []string {
	m.langsMu.RLock()
	defer m.langsMu.RUnlock()
	out := make([]string, 0, len(m.langsSeen))
	for k := range m.langsSeen {
		out = append(out, k)
	}
	// sort is in stdlib; do it inline to avoid pulling sort here
	// (caller usually wants sorted output anyway).
	if len(out) > 1 {
		simpleSortStrings(out)
	}
	return out
}

// replaceLangsSeen overwrites the langsSeen map under a write lock.
// Used by the persistence layer when loading state from disk.
func (m *model) replaceLangsSeen(codes []string) {
	m.langsMu.Lock()
	defer m.langsMu.Unlock()
	m.langsSeen = make(map[string]bool, len(codes))
	for _, c := range codes {
		if c != "" {
			m.langsSeen[c] = true
		}
	}
}

// simpleSortStrings is an insertion sort for small slices. We avoid
// the sort package to keep this file dependency-free and to make the
// O(n) cost for typical sizes (≤10 langs) negligible.
func simpleSortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j-1] > s[j]; j-- {
			s[j-1], s[j] = s[j], s[j-1]
		}
	}
}

// langsSeenLen returns the current size of the map under a read
// lock. Useful for tests and metrics.
func (m *model) langsSeenLen() int {
	m.langsMu.RLock()
	defer m.langsMu.RUnlock()
	return len(m.langsSeen)
}

// Compile-time guard: ensure sync.RWMutex is used (so the import
// stays even if all direct calls are inlined).
var _ = sync.RWMutex{}
