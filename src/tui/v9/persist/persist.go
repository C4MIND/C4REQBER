// Package persist provides persistent state for the TUI v9 (achievements).
package persist

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Achievement records one unlocked achievement for persistence.
type Achievement struct {
	Kind       int       `json:"kind"`
	UnlockedAt time.Time `json:"unlocked_at"`
}

// State is the persisted TUI v9 state (currently just achievements).
type State struct {
	LangsSeen      []string      `json:"langs_seen"`
	Achievements   []Achievement `json:"achievements"`
	DiscoveryCount int           `json:"discovery_count"`
	LLMTier        string        `json:"llm_tier,omitempty"`
	ColorProfile   string        `json:"color_profile,omitempty"`
	Lang           string        `json:"lang,omitempty"`
	FirstRun       bool          `json:"first_run"`
	UpdatedAt      time.Time     `json:"updated_at"`
}

// Store manages loading/saving persistent state.
type Store struct {
	mu    sync.Mutex
	path  string
	state State
}

func DefaultPath() string {
	home, _ := os.UserHomeDir()
	// Align with Python side (~/.c4reqber) for desktop app consistency.
	// Fallback to XDG-style ~/.config/c4reqber if .c4reqber does not exist yet.
	c4dir := filepath.Join(home, ".c4reqber")
	if _, err := os.Stat(c4dir); os.IsNotExist(err) {
		c4dir = filepath.Join(home, ".config", "c4reqber")
	}
	return filepath.Join(c4dir, "tui-v9-state.json")
}

// New creates a Store, loading existing state if available.
func New(path string) (*Store, error) {
	if path == "" {
		path = DefaultPath()
	}
	// Default: first run is true until saved
	s := &Store{path: path, state: State{FirstRun: true}}
	if err := s.load(); err != nil && !os.IsNotExist(err) {
		// Corrupt/unreadable state file. Do NOT propagate the error: the caller
		// drops the store on error, which permanently disables persistence and
		// never repairs the bad file. Instead reset to a fresh default and keep
		// a usable store — the next Save overwrites the bad file, self-healing.
		s.state = State{FirstRun: true}
		return s, nil
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
	// Write atomically: a crash/full-disk mid-write must not truncate the live
	// state file (which would then disable persistence on next launch). Write to
	// a temp file and rename over the target.
	tmp := s.path + ".tmp"
	if err := os.WriteFile(tmp, data, 0644); err != nil {
		return err
	}
	return os.Rename(tmp, s.path)
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

// Settings is a convenience type for tier/profile/lang persistence.
type Settings struct {
	LLMTier      string `json:"llm_tier"`
	ColorProfile string `json:"color_profile"`
	Lang         string `json:"lang"`
}

// GetSettings returns the persisted settings (zero values if unset).
func (s *Store) GetSettings() Settings {
	s.mu.Lock()
	defer s.mu.Unlock()
	return Settings{
		LLMTier:      s.state.LLMTier,
		ColorProfile: s.state.ColorProfile,
		Lang:         s.state.Lang,
	}
}

// SetSettings persists tier/profile/lang.
func (s *Store) SetSettings(set Settings) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if set.LLMTier != "" {
		s.state.LLMTier = set.LLMTier
	}
	if set.ColorProfile != "" {
		s.state.ColorProfile = set.ColorProfile
	}
	if set.Lang != "" {
		s.state.Lang = set.Lang
	}
}

// IsFirstRun returns true if this is the first time the app started.
func (s *Store) IsFirstRun() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.state.FirstRun
}

// MarkFirstRun resets the first-run flag so the wizard shows again
// on next launch. Inverse of MarkFirstRunDone.
func (s *Store) MarkFirstRun() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.state.FirstRun = true
}

// MarkFirstRunDone flips the first-run flag.
func (s *Store) MarkFirstRunDone() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.state.FirstRun = false
}
