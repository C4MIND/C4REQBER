package persist

import (
	"os"
	"path/filepath"
	"testing"
)

func TestStoreCreateAndLoad(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, err := New(path)
	if err != nil {
		t.Fatal(err)
	}
	// No state yet
	if got := s.Snapshot(); len(got.Achievements) != 0 {
		t.Errorf("new store should have 0 achievements, got %d", len(got.Achievements))
	}
}

func TestStoreAddAchievement(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := New(path)
	if s.HasAchievement(3) {
		t.Error("achievement 3 should not exist")
	}
	s.AddAchievement(3)
	if !s.HasAchievement(3) {
		t.Error("achievement 3 should exist after Add")
	}
	// Idempotent
	s.AddAchievement(3)
	count := 0
	for _, a := range s.Snapshot().Achievements {
		if a.Kind == 3 {
			count++
		}
	}
	if count != 1 {
		t.Errorf("idempotent: should have 1 instance, got %d", count)
	}
}

func TestStoreAddLangSeen(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := New(path)
	s.AddLangSeen("EN")
	s.AddLangSeen("RU")
	s.AddLangSeen("EN") // dup
	got := s.Snapshot()
	if len(got.LangsSeen) != 2 {
		t.Errorf("expected 2 unique langs, got %d", len(got.LangsSeen))
	}
}

func TestStoreSaveLoad(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := New(path)
	s.AddAchievement(5)
	s.AddLangSeen("ZH")
	s.IncrementDiscovery()
	if err := s.Save(); err != nil {
		t.Fatal(err)
	}
	// Reload
	s2, err := New(path)
	if err != nil {
		t.Fatal(err)
	}
	if !s2.HasAchievement(5) {
		t.Error("achievement 5 should be reloaded")
	}
	got := s2.Snapshot()
	if len(got.LangsSeen) != 1 || got.LangsSeen[0] != "ZH" {
		t.Errorf("langs_seen reload wrong: %v", got.LangsSeen)
	}
	if got.DiscoveryCount != 1 {
		t.Errorf("discovery count: %d", got.DiscoveryCount)
	}
}

func TestStoreReset(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := New(path)
	s.AddAchievement(7)
	s.AddLangSeen("JA")
	s.IncrementDiscovery()
	s.Reset()
	got := s.Snapshot()
	if len(got.Achievements) != 0 {
		t.Error("Reset should clear achievements")
	}
	if len(got.LangsSeen) != 0 {
		t.Error("Reset should clear langs")
	}
	if got.DiscoveryCount != 0 {
		t.Error("Reset should clear count")
	}
}

func TestStoreDefaultPath(t *testing.T) {
	p := DefaultPath()
	if p == "" {
		t.Error("default path is empty")
	}
	if filepath.Base(p) != "tui-v9-state.json" {
		t.Errorf("filename wrong: %s", p)
	}
}

func TestStoreLoadMissingFile(t *testing.T) {
	// Test that loading from a nonexistent file doesn't fail
	dir := t.TempDir()
	path := filepath.Join(dir, "nonexistent.json")
	s, err := New(path)
	if err != nil {
		t.Errorf("New on missing file should not fail, got: %v", err)
	}
	_ = s
}

func TestStoreConcurrentAccess(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "state.json")
	s, _ := New(path)
	// Just verify no race condition under concurrent reads/writes
	done := make(chan bool, 4)
	for i := 0; i < 4; i++ {
		go func(n int) {
			for j := 0; j < 10; j++ {
				s.AddAchievement(n*10 + j)
			}
			done <- true
		}(i)
	}
	for i := 0; i < 4; i++ {
		<-done
	}
	got := s.Snapshot()
	if len(got.Achievements) != 40 {
		t.Errorf("concurrent: expected 40, got %d", len(got.Achievements))
	}
}

// Test persistence: file is created on Save
func TestStoreCreatesFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "subdir", "state.json")
	s, _ := New(path)
	s.AddAchievement(1)
	if err := s.Save(); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(path); err != nil {
		t.Errorf("file should exist: %v", err)
	}
}
