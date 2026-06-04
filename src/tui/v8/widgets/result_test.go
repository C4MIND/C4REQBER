package widgets

import (
	"testing"

	"github.com/charmbracelet/bubbles/viewport"
)

func TestResult_SetContent(t *testing.T) {
	r := Result{
		Viewport:   viewport.New(40, 10),
		Topic:      "Test Topic",
		Papers:     2,
		Hypotheses: 1,
		Quality:    "A",
		HypothesesList: []map[string]interface{}{
			{"title": "Hypothesis 1"},
		},
		SourcesList: []map[string]interface{}{
			{"title": "Source 1"},
			{"title": "Source 2"},
		},
	}
	r.SetContent()
	if r.Viewport.View() == "" {
		t.Fatal("expected non-empty viewport content")
	}
}

func TestResult_View_Empty(t *testing.T) {
	r := Result{Viewport: viewport.New(40, 10)}
	v := r.View(42)
	if v == "" {
		t.Fatal("expected non-empty view for empty result")
	}
}
