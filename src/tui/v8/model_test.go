package main

import (
	"testing"

	"c4tui/config"
	"c4tui/internal"
)

func TestNewModelWithConfig(t *testing.T) {
	cfg := config.Default()
	cfg.API.BaseURL = "http://localhost:9999"
	m := newModelWithConfig(cfg)

	if m.Width != 0 {
		t.Errorf("expected initial Width 0, got %d", m.Width)
	}
	if m.Height != 0 {
		t.Errorf("expected initial Height 0, got %d", m.Height)
	}
	if m.Language != internal.LangEN {
		t.Errorf("expected default language EN, got %v", m.Language)
	}
	if m.Store == nil {
		t.Error("expected Store to be initialized")
	}
	if m.Backend == nil {
		t.Error("expected Backend to be initialized")
	}
}

func TestModel_InitCmd(t *testing.T) {
	cfg := config.Default()
	cfg.API.BaseURL = "http://localhost:9999"
	m := newModelWithConfig(cfg)
	cmd := m.Init()
	if cmd == nil {
		t.Error("expected non-nil Init command")
	}
}

func TestApp_TypeAssertion(t *testing.T) {
	cfg := config.Default()
	cfg.API.BaseURL = "http://localhost:9999"
	a := newApp(cfg)
	if a.phase != "splash" {
		t.Errorf("expected initial phase 'splash', got %q", a.phase)
	}
	if a.tui.Store == nil {
		t.Error("expected app.tui.Store to be initialized")
	}
}
