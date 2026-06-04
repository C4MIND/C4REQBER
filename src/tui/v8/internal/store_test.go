package internal

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestStore_AddAndRecent(t *testing.T) {
	tmpDir := t.TempDir()
	s := &Store{path: filepath.Join(tmpDir, "sessions.json"), SessionStart: time.Now()}
	rec := SessionRecord{Topic: "test", Mode: "discover"}
	if err := s.Add(rec); err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	recent := s.Recent(5)
	if len(recent) != 1 {
		t.Fatalf("expected 1 recent record, got %d", len(recent))
	}
	if recent[0].Topic != "test" {
		t.Errorf("expected topic 'test', got %q", recent[0].Topic)
	}
}

func TestStore_SetLastInput(t *testing.T) {
	s := NewStore()
	if err := s.SetLastInput("hello world"); err != nil {
		t.Fatalf("SetLastInput failed: %v", err)
	}
	if s.LastInput != "hello world" {
		t.Errorf("expected LastInput 'hello world', got %q", s.LastInput)
	}
}

func TestStore_SaveAndLoad(t *testing.T) {
	tmpDir := t.TempDir()
	s := &Store{path: filepath.Join(tmpDir, "test.json")}
	rec := SessionRecord{Topic: "persist", Mode: "turbo"}
	_ = s.Add(rec)
	if err := s.Flush(); err != nil {
		t.Fatalf("Flush failed: %v", err)
	}

	// Load into a new store
	s2 := &Store{path: s.path}
	s2.load()
	if len(s2.History) != 1 {
		t.Fatalf("expected 1 history record after load, got %d", len(s2.History))
	}
	if s2.History[0].Topic != "persist" {
		t.Errorf("expected topic 'persist', got %q", s2.History[0].Topic)
	}
}

func TestStore_SetLastInput_Isolated(t *testing.T) {
	tmpDir := t.TempDir()
	s := &Store{path: filepath.Join(tmpDir, "sessions.json"), SessionStart: time.Now()}
	_ = s.SetLastInput("hello")
	if s.LastInput != "hello" {
		t.Errorf("expected LastInput 'hello', got %q", s.LastInput)
	}
}

func TestStore_BackupOnSave(t *testing.T) {
	tmpDir := t.TempDir()
	s := &Store{path: filepath.Join(tmpDir, "sessions.json")}
	_ = os.WriteFile(s.path, []byte(`{"history":[]}`), 0644)
	_ = s.Save()
	if _, err := os.Stat(s.path + ".bak"); os.IsNotExist(err) {
		t.Error("expected backup file to be created")
	}
}
