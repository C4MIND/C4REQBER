package widgets

import (
	"c4tui/config"
	"testing"

	tea "github.com/charmbracelet/bubbletea"
)

func TestC4Grid_Navigation(t *testing.T) {
	g := NewC4Grid(config.Default())
	if g.State != [3]int{1, 1, 0} {
		t.Fatalf("unexpected initial state %v", g.State)
	}

	// Move right on Time axis (default ActiveAxis=0)
	g, _ = g.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("right")})
	if g.State[0] != 2 {
		t.Fatalf("expected time=2 after right, got %v", g.State)
	}

	// Cycle axis to Scale
	g, _ = g.Update(tea.KeyMsg{Type: tea.KeyTab})
	if g.ActiveAxis != 1 {
		t.Fatalf("expected active axis 1 after tab, got %d", g.ActiveAxis)
	}

	// Move up on Scale axis (adds 1)
	g, _ = g.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("up")})
	if g.State[1] != 2 {
		t.Fatalf("expected scale=2 after up, got %v", g.State)
	}

	// Move down on Scale axis (subtracts 1)
	g, _ = g.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("down")})
	if g.State[1] != 1 {
		t.Fatalf("expected scale=1 after down, got %v", g.State)
	}
}

func TestC4Grid_Wrap(t *testing.T) {
	g := NewC4Grid(config.Default())
	// Move left twice from 1 -> 0 -> 2 (wrap)
	g, _ = g.Update(key("left"))
	g, _ = g.Update(key("left"))
	if g.State[0] != 2 {
		t.Fatalf("expected wrap to 2, got %v", g.State)
	}
}

func key(s string) tea.KeyMsg {
	return tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune(s)}
}
