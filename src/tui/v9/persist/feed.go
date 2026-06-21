// Package persist — feed.jsonl (append-only feed) and input-history.json.
// Per §10 of the unified plan, the live model gets these in S2. They
// are kept separate from the main state.json so:
//   - feed.jsonl is append-only, one line per card, growth-bounded
//   - input-history.json is small, dedup-MRU
package persist

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// FeedEntry is one row in feed.jsonl. Mirrors the Card struct but only
// the fields worth persisting across sessions.
type FeedEntry struct {
	ID       uint64    `json:"id"`
	Kind     int       `json:"kind"`
	Title    string    `json:"title"`
	Body     string    `json:"body,omitempty"`
	Time     time.Time `json:"time"`
	Status   string    `json:"status,omitempty"`
	Bookmark bool      `json:"bookmarked,omitempty"`

	// Sim-specific (optional)
	SimEngine       string  `json:"sim_engine,omitempty"`
	SimStatus       string  `json:"sim_status,omitempty"`
	SimVerdict      string  `json:"sim_verdict,omitempty"`
	SimCostUSD      float64 `json:"sim_cost_usd,omitempty"`
	SimInstallHint  string  `json:"sim_install_hint,omitempty"`
	SimHypothesisID uint64  `json:"sim_hypothesis_id,omitempty"`
}

// FeedStore manages the append-only feed.jsonl.
type FeedStore struct {
	mu     sync.Mutex
	path   string
	maxLen int
}

// NewFeedStore opens the feed at ~/.c4reqber/tui-v9-feed.jsonl (preferred)
// falling back to ~/.config/c4reqber (XDG migration), with the given cap.
func NewFeedStore(maxLen int) (*FeedStore, error) {
	if maxLen <= 0 {
		maxLen = 50
	}
	home, _ := os.UserHomeDir()
	// Align with Python + persist.DefaultPath for unified desktop config dir
	dir := filepath.Join(home, ".c4reqber")
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		dir = filepath.Join(home, ".config", "c4reqber")
	}
	p := filepath.Join(dir, "tui-v9-feed.jsonl")
	return &FeedStore{path: p, maxLen: maxLen}, nil
}

// Path returns the feed file path (used by tests and the model for "last opened").
func (f *FeedStore) Path() string { return f.path }

// Append adds one entry. Atomic write — opens file in O_APPEND mode.
func (f *FeedStore) Append(e FeedEntry) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if err := os.MkdirAll(filepath.Dir(f.path), 0755); err != nil {
		return err
	}
	file, err := os.OpenFile(f.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer file.Close()
	data, err := json.Marshal(e)
	if err != nil {
		return err
	}
	if _, err := file.Write(append(data, '\n')); err != nil {
		return err
	}
	return nil
}

// LoadRecent reads the last N entries (most recent first).
func (f *FeedStore) LoadRecent(n int) ([]FeedEntry, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	file, err := os.Open(f.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil // no feed yet
		}
		return nil, err
	}
	defer file.Close()

	// Read all lines
	var lines [][]byte
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 64*1024), 1024*1024) // 1MB max line
	for scanner.Scan() {
		if len(scanner.Bytes()) > 0 {
			lines = append(lines, append([]byte{}, scanner.Bytes()...))
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	// Take last n
	if n > 0 && len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	out := make([]FeedEntry, 0, len(lines))
	for _, raw := range lines {
		var e FeedEntry
		if err := json.Unmarshal(raw, &e); err == nil {
			out = append(out, e)
		}
	}
	// Reverse to most-recent-first
	for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
		out[i], out[j] = out[j], out[i]
	}
	return out, nil
}

// Prune keeps the most recent maxLen entries (bookmarked always kept).
// On a 50-cap file this is sub-millisecond.
func (f *FeedStore) Prune() error {
	entries, err := f.LoadRecent(f.maxLen * 4) // over-read
	if err != nil {
		return err
	}
	// Sort by time descending
	// (LoadRecent already returns most-recent-first)
	bookmarked := []FeedEntry{}
	recent := []FeedEntry{}
	for _, e := range entries {
		if e.Bookmark {
			bookmarked = append(bookmarked, e)
		} else {
			recent = append(recent, e)
		}
	}
	// Cap recent at maxLen, keep all bookmarked
	if len(recent) > f.maxLen {
		recent = recent[:f.maxLen]
	}
	merged := append(bookmarked, recent...)

	// Rewrite file atomically
	tmp := f.path + ".tmp"
	file, err := os.Create(tmp)
	if err != nil {
		return err
	}
	enc := json.NewEncoder(file)
	for _, e := range merged {
		if err := enc.Encode(e); err != nil {
			file.Close()
			os.Remove(tmp)
			return err
		}
	}
	if err := file.Close(); err != nil {
		os.Remove(tmp)
		return err
	}
	// Only promote the rewritten file once it's fully and successfully written,
	// so a mid-write failure can never truncate the live feed (and silently
	// drop the bookmarked entries this function is trying to preserve).
	return os.Rename(tmp, f.path)
}

// InputHistory persists the last N queries, deduped MRU.
type InputHistory struct {
	mu     sync.Mutex
	path   string
	limit  int
	items  []HistoryItem
}

type HistoryItem struct {
	Text     string    `json:"text"`
	Mode     string    `json:"mode"`
	LastUsed time.Time `json:"last_used"`
}

// NewInputHistory creates a store at ~/.c4reqber/tui-v9-input-history.json (unified)
// or ~/.config fallback, with the given cap (default 200).
func NewInputHistory(limit int) (*InputHistory, error) {
	if limit <= 0 {
		limit = 200
	}
	home, _ := os.UserHomeDir()
	dir := filepath.Join(home, ".c4reqber")
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		dir = filepath.Join(home, ".config", "c4reqber")
	}
	p := filepath.Join(dir, "tui-v9-input-history.json")
	h := &InputHistory{path: p, limit: limit}
	h.load()
	return h, nil
}

func (h *InputHistory) load() {
	data, err := os.ReadFile(h.path)
	if err != nil {
		return
	}
	_ = json.Unmarshal(data, &h.items)
}

func (h *InputHistory) save() error {
	// Caller MUST hold h.mu.
	data, err := json.MarshalIndent(h.items, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(h.path), 0755); err != nil {
		return err
	}
	return os.WriteFile(h.path, data, 0644)
}

// Add inserts a query at the head (MRU). Dedupes against existing
// entries with the same text+mode.
func (h *InputHistory) Add(text, mode string) error {
	text = strings.TrimSpace(text)
	if text == "" {
		return nil
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	now := time.Now()
	// Remove any existing duplicate
	for i, it := range h.items {
		if it.Text == text && it.Mode == mode {
			h.items = append(h.items[:i], h.items[i+1:]...)
			break
		}
	}
	// Insert at head
	h.items = append([]HistoryItem{{Text: text, Mode: mode, LastUsed: now}}, h.items...)
	// Cap
	if len(h.items) > h.limit {
		h.items = h.items[:h.limit]
	}
	return h.save()
}

// Recent returns the last n items in MRU order.
func (h *InputHistory) Recent(n int) []HistoryItem {
	h.mu.Lock()
	defer h.mu.Unlock()
	if n <= 0 || n > len(h.items) {
		n = len(h.items)
	}
	out := make([]HistoryItem, n)
	copy(out, h.items[:n])
	return out
}

// ensure import is used
var _ = fmt.Sprintf
