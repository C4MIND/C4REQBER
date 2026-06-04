package widgets

import (
	"testing"

	"c4tui/config"
	tea "github.com/charmbracelet/bubbletea"
)

func TestHeader_Init(t *testing.T) {
	h := NewHeader(config.Default())
	cmd := h.Init()
	if cmd == nil {
		t.Fatal("expected non-nil init command")
	}
}

func TestHeader_UpdateTime(t *testing.T) {
	h := NewHeader(config.Default())
	newH, cmd := h.Update(clockTickMsg{})
	if newH.Clock == "" {
		t.Fatal("expected clock to be set")
	}
	if cmd == nil {
		t.Fatal("expected next tick command")
	}
}

func TestHeader_HealthCheck(t *testing.T) {
	h := NewHeader(config.Default())
	h.HealthCheck = func() bool { return true }
	newH, cmd := h.Update(clockTickMsg{})
	// Health check is now async — execute the returned batch command
	if cmd == nil {
		t.Fatal("expected health check command")
	}
	var result healthResultMsg
	found := false
	batch, ok := cmd().(tea.BatchMsg)
	if !ok {
		t.Fatalf("expected BatchMsg, got %T", cmd())
	}
	for _, c := range batch {
		if msg := c(); msg != nil {
			if r, ok := msg.(healthResultMsg); ok {
				result = r
				found = true
			}
		}
	}
	if !found {
		t.Fatal("expected healthResultMsg in batch")
	}
	newH, _ = newH.Update(result)
	if !newH.Online {
		t.Fatal("expected online status to be true")
	}

	h.HealthCheck = func() bool { return false }
	newH, cmd = h.Update(clockTickMsg{})
	found = false
	batch, _ = cmd().(tea.BatchMsg)
	for _, c := range batch {
		if msg := c(); msg != nil {
			if r, ok := msg.(healthResultMsg); ok {
				result = r
				found = true
			}
		}
	}
	if !found {
		t.Fatal("expected healthResultMsg in batch")
	}
	newH, _ = newH.Update(result)
	if newH.Online {
		t.Fatal("expected online status to be false")
	}
}

func TestHeader_View(t *testing.T) {
	h := Header{
		Discoveries: 5,
		Online:      true,
		Clock:       "12:00:00",
	}
	v := h.View(80)
	if v == "" {
		t.Fatal("expected non-empty view")
	}
}

func TestHeader_ResearchTicker(t *testing.T) {
	h := NewHeader(config.Default())
	// Initial state should be discovery phase
	v1 := h.View(80)
	if v1 == "" {
		t.Fatal("expected non-empty view")
	}
	// After ticker tick, phase should flip
	newH, _ := h.Update(tickerTickMsg{})
	if newH.researchPhase != 1 {
		t.Fatalf("expected researchPhase 1 (problem), got %d", newH.researchPhase)
	}
	// After another tick, phase should flip back
	newH2, _ := newH.Update(tickerTickMsg{})
	if newH2.researchPhase != 0 {
		t.Fatalf("expected researchPhase 0 (discovery), got %d", newH2.researchPhase)
	}
}

func TestHeader_LanguageFlag(t *testing.T) {
	h := NewHeader(config.Default())
	if h.Flag == "" {
		t.Fatal("expected flag to be set")
	}
	v := h.View(80)
	if v == "" {
		t.Fatal("expected non-empty view")
	}
}
