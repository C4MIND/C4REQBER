// Package persist provides persistent state for the TUI v9 (achievements).
package persist

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Achievement records one unlocked achievement for persistence.
type Achievement struct {
	Kind      int       `json:"kind"`
	UnlockedAt time.Time `json:"unlocked_at"`
}

// State is the persisted TUI v9 state (currently just achievements).
type State struct {
	LangsSeen       []string      `json:"langs_seen"`
	Achievements    []Achievement `json:"achievements"`
	DiscoveryCount  int           `json:"discovery_count"`
	UpdatedAt       time.Time     `json:"updated_at"`
}

// Store manages loading/saving persistent state.
type Store struct {
	mu    sync.Mutex
	path  string
	state State
}

func DefaultPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "c4reqber", "tui-v9-state.json")
}

// New creates a Store, loading existing state if available.
func New(path string) (*Store, error) {
	if path == "" {
		path = DefaultPath()
	}
	s := &Store{path: path, state: State{}}
	if err := s.load(); err != nil && !os.IsNotExist(err) {
		return s, fmt.Errorf("load: %w", err)
	}
	return s, nil
}

func (s *Store) load() error {
	data, err := os.ReadFile(s.path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, &s.state)
}

// Save writes current state to disk.
func (s *Store) Save() error {
	s.mu.Lock()
	s.state.UpdatedAt = time.Now()
	data, err := json.MarshalIndent(s.state, "", "  ")
	s.mu.Unlock()
	if err != nil {
		return err
	}
	// Ensure directory exists
	if err := os.MkdirAll(filepath.Dir(s.path), 0755); err != nil {
		return err
	}
	return os.WriteFile(s.path, data, 0644)
}

// HasAchievement checks if a kind is already unlocked.
func (s *Store) HasAchievement(kind int) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, a := range s.state.Achievements {
		if a.Kind == kind {
			return true
		}
	}
	return false
}

// AddAchievement records a new unlock.
func (s *Store) AddAchievement(kind int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, a := range s.state.Achievements {
		if a.Kind == kind {
			return // already have it
		}
	}
	s.state.Achievements = append(s.state.Achievements, Achievement{Kind: kind, UnlockedAt: time.Now()})
}

// AddLangSeen records a language the user has used.
func (s *Store) AddLangSeen(lang string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, l := range s.state.LangsSeen {
		if l == lang {
			return
		}
	}
	s.state.LangsSeen = append(s.state.LangsSeen, lang)
}

// IncrementDiscovery bumps the discovery counter.
func (s *Store) IncrementDiscovery() {
	s.mu.Lock()
	s.state.DiscoveryCount++
	s.mu.Unlock()
}

// Snapshot returns a copy of the state.
func (s *Store) Snapshot() State {
	s.mu.Lock()
	defer s.mu.Unlock()
	cp := s.state
	cp.LangsSeen = append([]string{}, s.state.LangsSeen...)
	cp.Achievements = append([]Achievement{}, s.state.Achievements...)
	return cp
}

// Reset clears all persisted state.
func (s *Store) Reset() error {
	s.mu.Lock()
	s.state = State{}
	s.mu.Unlock()
	return s.Save()
}
