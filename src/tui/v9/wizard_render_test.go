package tui

import (
	"strings"
	"testing"
)

func TestWizardStepAdvances(t *testing.T) {
	w := NewWizardState()
	if w.Step() != 0 {
		t.Errorf("initial step = %d, want 0", w.Step())
	}
	w.Next()
	if w.Step() != 1 {
		t.Errorf("after Next, step = %d, want 1", w.Step())
	}
	w.Next()
	if w.Step() != 2 {
		t.Errorf("after 2x Next, step = %d, want 2", w.Step())
	}
	w.Next()
	if w.Step() != 3 {
		t.Errorf("after 3x Next, step = %d, want 3", w.Step())
	}
	// Should cap at 3
	w.Next()
	if w.Step() != 3 {
		t.Errorf("Next after cap should stay at 3, got %d", w.Step())
	}
}

func TestWizardShowHide(t *testing.T) {
	w := NewWizardState()
	if w.Active() {
		t.Error("wizard should not be active by default")
	}
	w.Show()
	if !w.Active() {
		t.Error("Show should activate wizard")
	}
	if w.Step() != 0 {
		t.Errorf("Show should reset step to 0, got %d", w.Step())
	}
	w.Hide()
	if w.Active() {
		t.Error("Hide should deactivate wizard")
	}
}

func TestWizardRenderStep0(t *testing.T) {
	out := RenderWizard(80, 24, 0)
	if !strings.Contains(out, "Welcome") {
		t.Errorf("step 0 should contain 'Welcome', got: %s", truncate(out, 200))
	}
	if !strings.Contains(out, "next") {
		t.Errorf("step 0 should contain 'next' hint")
	}
}

func TestWizardRenderStep1(t *testing.T) {
	out := RenderWizard(80, 24, 1)
	if !strings.Contains(out, "demo") && !strings.Contains(out, "Demo") {
		t.Errorf("step 1 should mention demo, got: %s", truncate(out, 200))
	}
}

func TestWizardRenderStep2(t *testing.T) {
	out := RenderWizard(80, 24, 2)
	if !strings.Contains(out, "Tab") {
		t.Errorf("step 2 should mention Tab key, got: %s", truncate(out, 200))
	}
}

func TestWizardRenderDefault(t *testing.T) {
	out := RenderWizard(80, 24, 5) // out-of-range step
	if !strings.Contains(out, "Ready") {
		t.Errorf("default step should show Ready, got: %s", truncate(out, 200))
	}
}

func TestWizardRenderSmallDimensions(t *testing.T) {
	// Very small width/height — should fall back to defaults gracefully
	out := RenderWizard(20, 5, 0)
	if out == "" {
		t.Error("wizard should render even at small dimensions")
	}
}
