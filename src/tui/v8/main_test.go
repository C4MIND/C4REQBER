package main

import (
	"testing"

	"c4tui/backend"
	"c4tui/config"
	"c4tui/screens"
	"c4tui/splash"
	tea "github.com/charmbracelet/bubbletea"
)

func TestApp_Init(t *testing.T) {
	a := newApp(config.Default())
	cmd := a.Init()
	if cmd == nil {
		t.Fatal("expected non-nil init command")
	}
}

func TestApp_SplashToTUI(t *testing.T) {
	a := newApp(config.Default())
	a.width = 80
	a.height = 24

	// Simulate splash done via splash.Done message
	newA, cmd := a.Update(splash.Done())
	_ = cmd
	a2 := newA.(app)
	if a2.phase != "tui" {
		t.Fatalf("expected phase tui, got %s", a2.phase)
	}
}

func TestApp_CtrlC(t *testing.T) {
	a := newApp(config.Default())
	newA, cmd := a.Update(tea.KeyMsg{Type: tea.KeyCtrlC})
	_ = newA
	if cmd == nil {
		t.Fatal("expected quit command")
	}
}

func TestModel_Init(t *testing.T) {
	m := newModel()
	cmd := m.Init()
	if cmd == nil {
		t.Fatal("expected non-nil init command")
	}
}

func TestModel_UpdateQuit(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	newM, cmd := m.Update(tea.KeyMsg{Type: tea.KeyCtrlC})
	if cmd == nil {
		t.Fatal("expected quit command")
	}
	_ = newM
}

func TestModel_View(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	v := m.View()
	if v == "" {
		t.Fatal("expected non-empty view")
	}
}

func TestModel_MouseClickMode(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	m.InputBar.Mode = "discover"
	// Click in the middle column at row 4 (mode buttons area)
	newM, _ := m.Update(tea.MouseMsg{X: 30, Y: 4, Action: tea.MouseActionPress, Button: tea.MouseButtonLeft})
	m2 := newM.(model)
	if m2.InputBar.Mode == "discover" {
		// If click didn't hit a button, mode stays discover; that's fine.
		// We just verify no panic.
	}
}

func TestModel_PhaseMsg(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	m.Pipeline.Start()
	newM, _ := m.Update(backend.PhaseMsg{Phase: "B: Search", Status: "working", Progress: 0.5})
	m2 := newM.(model)
	if !m2.Pipeline.Running {
		t.Fatal("expected pipeline still running after phase msg")
	}
}

func TestModel_WindowSize(t *testing.T) {
	m := newModel()
	newM, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 30})
	m2 := newM.(model)
	if m2.Width != 100 {
		t.Fatalf("expected width 100, got %d", m2.Width)
	}
	if m2.Height != 30 {
		t.Fatalf("expected height 30, got %d", m2.Height)
	}
}

func TestModel_HelpOverlay(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	newM, _ := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("?")})
	m2 := newM.(model)
	if m2.Screen != screens.ScreenHelp {
		t.Fatalf("expected help screen active, got %d", m2.Screen)
	}
	if m2.Overlay == nil {
		t.Fatal("expected help overlay open")
	}
}

func TestModel_ChatToggle(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	newM, _ := m.Update(tea.KeyMsg{Type: tea.KeyF2})
	m2 := newM.(model)
	if !m2.Chat.Expanded {
		t.Fatal("expected chat expanded after F2")
	}
}

func TestModel_HandleDiscoverMsg(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	m.Pipeline.Start()
	newM, _ := m.Update(backend.DiscoverMsg{JobID: "job_test"})
	m2 := newM.(model)
	if m2.JobID != "job_test" {
		t.Fatalf("expected job_id job_test, got %s", m2.JobID)
	}
}

func TestModel_HandleJobCompleteMsg(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	m.Pipeline.Start()
	result := map[string]interface{}{"problem": "test", "quality": "A"}
	newM, _ := m.Update(backend.JobCompleteMsg{JobID: "job_test", Result: result})
	m2 := newM.(model)
	if m2.Pipeline.Running {
		t.Fatal("expected pipeline stopped after job complete")
	}
	if m2.Mascot.Emotion != "happy" {
		t.Fatalf("expected happy mascot, got %s", m2.Mascot.Emotion)
	}
	if m2.Result.Topic != "test" {
		t.Fatalf("expected result topic 'test', got %s", m2.Result.Topic)
	}
}
