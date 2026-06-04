package internal

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// SessionRecord is a single discovery saved to the session store.
type SessionRecord struct {
	Topic     string    `json:"topic"`
	Mode      string    `json:"mode"`
	Quality   string    `json:"quality"`
	Papers    int       `json:"papers"`
	Hyps      int       `json:"hyps"`
	Timestamp time.Time `json:"timestamp"`
}

// Store persists session data to ~/.c4reqber/sessions.json.
type Store struct {
	path string
	mu   sync.Mutex

	History          []SessionRecord `json:"history"`
	LastInput        string          `json:"last_input"`
	DiscoveriesCount int             `json:"discoveries_count"`
	SessionStart     time.Time       `json:"session_start"`

	dirty     bool
	saveTimer *time.Timer
}

// NewStore creates a store backed by the default path.
func NewStore() *Store {
	home, err := os.UserHomeDir()
	if err != nil {
		home = "."
	}
	path := filepath.Join(home, ".c4reqber", "sessions.json")
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		// Fall back to current directory if home is not writable
		path = filepath.Join(".", ".c4reqber", "sessions.json")
		_ = os.MkdirAll(filepath.Dir(path), 0755)
	}
	s := &Store{path: path, SessionStart: time.Now()}
	s.load()
	return s
}

func (s *Store) load() {
	data, err := os.ReadFile(s.path)
	if err != nil {
		return // no prior sessions — start fresh
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if err := json.Unmarshal(data, s); err != nil {
		// Corrupted sessions file — start fresh but keep the path
		s.History = nil
		s.LastInput = ""
		s.DiscoveriesCount = 0
	}
}

// Save writes the store to disk, creating a backup of the previous version.
func (s *Store) Save() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal store: %w", err)
	}
	// Backup existing file before overwriting
	if _, err := os.Stat(s.path); err == nil {
		if renameErr := os.Rename(s.path, s.path+".bak"); renameErr != nil {
			return fmt.Errorf("backup store: %w", renameErr)
		}
	}
	return os.WriteFile(s.path, data, 0644)
}

// Add appends a discovery record and schedules a debounced persist.
func (s *Store) Add(r SessionRecord) error {
	s.mu.Lock()
	s.History = append(s.History, r)
	if len(s.History) > 100 {
		s.History = s.History[len(s.History)-100:]
	}
	s.DiscoveriesCount++
	s.mu.Unlock()
	s.scheduleSave()
	return nil
}

// Recent returns the last n records (newest first).
func (s *Store) Recent(n int) []SessionRecord {
	s.mu.Lock()
	defer s.mu.Unlock()
	if n > len(s.History) {
		n = len(s.History)
	}
	out := make([]SessionRecord, n)
	for i := 0; i < n; i++ {
		out[i] = s.History[len(s.History)-1-i]
	}
	return out
}

// SetLastInput updates the last input field and schedules a debounced persist.
func (s *Store) SetLastInput(v string) error {
	s.mu.Lock()
	s.LastInput = v
	s.mu.Unlock()
	s.scheduleSave()
	return nil
}

// Flush immediately persists the store to disk (useful for tests and shutdown).
func (s *Store) Flush() error {
	if s == nil {
		return nil
	}
	s.mu.Lock()
	if s.saveTimer != nil {
		s.saveTimer.Stop()
	}
	s.dirty = false
	s.mu.Unlock()
	return s.Save()
}

// scheduleSave debounces disk writes to avoid blocking the TUI event loop.
func (s *Store) scheduleSave() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.dirty = true
	if s.saveTimer != nil {
		s.saveTimer.Stop()
	}
	s.saveTimer = time.AfterFunc(2*time.Second, func() {
		defer func() {
			if r := recover(); r != nil {
				// Prevent background save panics from crashing the TUI
			}
		}()
		s.mu.Lock()
		if !s.dirty {
			s.mu.Unlock()
			return
		}
		s.dirty = false
		s.mu.Unlock()
		if err := s.Save(); err != nil {
			// Log to stderr — TUI should not crash on disk errors,
			// but the user deserves to know their session may not persist.
			fmt.Fprintf(os.Stderr, "c4tui: failed to save session: %v\n", err)
		}
	})
}
