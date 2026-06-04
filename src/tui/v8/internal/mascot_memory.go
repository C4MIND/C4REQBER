package internal

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// MascotMemory holds persistent companion stats.
type MascotMemory struct {
	Energy      int `json:"energy"`
	Curiosity   int `json:"curiosity"`
	Bond        int `json:"bond"`
	Discoveries int `json:"discoveries"`
}

var (
	mascotSaveCh   chan MascotMemory
	mascotSaveOnce sync.Once
)

func initMascotSaveWorker() {
	mascotSaveCh = make(chan MascotMemory, 4)
	go func() {
		for m := range mascotSaveCh {
			_ = SaveMascotMemory(m)
		}
	}()
}

// DefaultMascotMemory returns fresh stats.
func DefaultMascotMemory() MascotMemory {
	return MascotMemory{Energy: 100, Curiosity: 50, Bond: 10, Discoveries: 0}
}

// LoadMascotMemory reads stats from disk.
func LoadMascotMemory() MascotMemory {
	path := mascotMemoryPath()
	data, err := os.ReadFile(path)
	if err != nil {
		return DefaultMascotMemory()
	}
	var m MascotMemory
	if err := json.Unmarshal(data, &m); err != nil {
		return DefaultMascotMemory()
	}
	return m
}

// SaveMascotMemory writes stats to disk.
func SaveMascotMemory(m MascotMemory) error {
	path := mascotMemoryPath()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return fmt.Errorf("create mascot memory dir: %w", err)
	}
	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal mascot memory: %w", err)
	}
	return os.WriteFile(path, data, 0644)
}

func mascotMemoryPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		home = "."
	}
	return filepath.Join(home, ".c4reqber", "cube_memory.json")
}

// Personality returns the personality tier based on discoveries.
func (m MascotMemory) Personality() string {
	switch {
	case m.Discoveries < 3:
		return "curious"
	case m.Discoveries < 10:
		return "learning"
	case m.Discoveries < 25:
		return "confident"
	case m.Discoveries < 50:
		return "expert"
	default:
		return "master"
	}
}

// OnDiscovery increments stats after a successful discovery.
// Persists to disk asynchronously so the TUI event loop never blocks.
func (m *MascotMemory) OnDiscovery() {
	m.Discoveries++
	m.Energy = min(100, m.Energy+5)
	m.Curiosity = min(100, m.Curiosity+10)
	m.Bond = min(100, m.Bond+2)
	mascotSaveOnce.Do(initMascotSaveWorker)
	select {
	case mascotSaveCh <- *m:
	default:
		// Channel full — drop save to avoid blocking
	}
}
