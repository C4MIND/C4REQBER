package widgets

import (
	"strings"
	"testing"

	"c4tui/config"
	tea "github.com/charmbracelet/bubbletea"
)

func TestChat_Add(t *testing.T) {
	c := NewChat(config.Default())
	c.Add("hello world")
	if len(c.Lines) != 1 {
		t.Fatalf("expected 1 line, got %d", len(c.Lines))
	}
	if !strings.Contains(c.Lines[0], "hello world") {
		t.Fatalf("expected line to contain 'hello world', got %s", c.Lines[0])
	}
}

func TestChat_AddMultiple(t *testing.T) {
	c := NewChat(config.Default())
	c.Add("first")
	c.Add("second")
	if len(c.Lines) != 2 {
		t.Fatalf("expected 2 lines, got %d", len(c.Lines))
	}
}

func TestChat_ExpandedView(t *testing.T) {
	c := NewChat(config.Default())
	c.Expanded = true
	c.Add("test message")
	v := c.View(80)
	if v == "" {
		t.Fatal("expected non-empty expanded view")
	}
}

func TestChat_CollapsedView(t *testing.T) {
	c := NewChat(config.Default())
	c.Expanded = false
	v := c.View(80)
	if v == "" {
		t.Fatal("expected non-empty collapsed view")
	}
}

func TestChat_Update(t *testing.T) {
	c := NewChat(config.Default())
	c.Expanded = true
	newC, cmd := c.Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	_ = newC
	_ = cmd
}

func TestChat_StyleLine(t *testing.T) {
	c := NewChat(config.Default())
	tests := []struct {
		input string
		want  string
	}{
		{"[err] fail", "fail"},
		{"[warn] caution", "caution"},
		{"[pipeline] ok", "ok"},
		{"normal", "normal"},
	}
	for _, tt := range tests {
		got := c.styleLine(tt.input)
		if !strings.Contains(got, tt.want) {
			t.Fatalf("styleLine(%q) should contain %q, got %q", tt.input, tt.want, got)
		}
	}
}
