package styles

import (
	"testing"

	"github.com/charmbracelet/lipgloss"
)

func TestCycleTheme(t *testing.T) {
	SetTheme(DarkTheme)
	if ActiveTheme().Name != "dark" {
		t.Fatalf("expected dark, got %s", ActiveTheme().Name)
	}

	next := CycleTheme()
	if next.Name != "matrix" {
		t.Fatalf("expected matrix, got %s", next.Name)
	}
	if ActiveTheme().Name != "matrix" {
		t.Fatalf("active should be matrix, got %s", ActiveTheme().Name)
	}

	next = CycleTheme()
	if next.Name != "paper" {
		t.Fatalf("expected paper, got %s", next.Name)
	}

	next = CycleTheme()
	if next.Name != "dark" {
		t.Fatalf("expected dark after wrap, got %s", next.Name)
	}
}

func TestSyncColors(t *testing.T) {
	SetTheme(MatrixTheme)
	if Cyan != lipgloss.Color("#00FF41") {
		t.Fatalf("expected matrix cyan, got %s", Cyan)
	}
	if BgDark != lipgloss.Color("#000000") {
		t.Fatalf("expected matrix bg, got %s", BgDark)
	}

	SetTheme(PaperTheme)
	if Cyan != lipgloss.Color("#0891B2") {
		t.Fatalf("expected paper cyan, got %s", Cyan)
	}
	if BgDark != lipgloss.Color("#FAFAFA") {
		t.Fatalf("expected paper bg, got %s", BgDark)
	}
}

func TestAllThemesDefined(t *testing.T) {
	for _, th := range AllThemes {
		if th.Name == "" {
			t.Fatal("theme has no name")
		}
	}
}
