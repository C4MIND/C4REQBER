//go:build integration

package main

import (
	"testing"

	"c4tui/backend"
)

// TestIntegration_EndToEnd simulates a full discovery flow.
func TestIntegration_EndToEnd(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24

	// Simulate C4 navigation response
	newM, _ := m.Update(backend.C4NavigateMsg{
		Resp: &backend.C4NavigateResponse{
			Start: "C4State(T=0, S=0, A=0)",
			End:   "C4State(T=2, S=2, A=2)",
			Path:  []string{"C4State(T=0, S=0, A=0)", "C4State(T=1, S=1, A=1)", "C4State(T=2, S=2, A=2)"},
			Steps: 2,
		},
	})
	m2 := newM.(model)
	if len(m2.C4Grid.Path) != 3 {
		t.Fatalf("expected C4 path length 3, got %d", len(m2.C4Grid.Path))
	}

	// Simulate discover job start
	newM, _ = m2.Update(backend.DiscoverMsg{JobID: "job_int"})
	m3 := newM.(model)
	if m3.JobID != "job_int" {
		t.Fatalf("expected job_id job_int, got %s", m3.JobID)
	}

	// Simulate phase update (pipeline must be running)
	m3.Pipeline.Start()
	newM, _ = m3.Update(backend.PhaseMsg{Phase: "B: Search", Status: "working", Progress: 0.5})
	m4 := newM.(model)
	if !m4.Pipeline.Running {
		t.Fatal("expected pipeline running after phase msg")
	}

	// Simulate job completion
	result := map[string]interface{}{
		"problem": "integration test",
		"quality": "A+",
	}
	newM, _ = m4.Update(backend.JobCompleteMsg{JobID: "job_int", Result: result})
	m5 := newM.(model)
	if m5.Pipeline.Running {
		t.Fatal("expected pipeline stopped after completion")
	}
	if m5.Result.Topic != "integration test" {
		t.Fatalf("expected result topic 'integration test', got %s", m5.Result.Topic)
	}
	if m5.Mascot.Emotion != "happy" {
		t.Fatalf("expected happy mascot, got %s", m5.Mascot.Emotion)
	}
}

// TestIntegration_SearchFlow simulates a search flow.
func TestIntegration_SearchFlow(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	m.InputBar.Mode = "search"

	resp := &backend.SearchResponse{
		Query:   "neural networks",
		Total:   5,
		Results: []backend.SearchResult{{Title: "Paper 1"}, {Title: "Paper 2"}},
	}
	newM, _ := m.Update(backend.SearchMsg{Resp: resp})
	m2 := newM.(model)
	if m2.Result.Topic != "neural networks" {
		t.Fatalf("expected result topic 'neural networks', got %s", m2.Result.Topic)
	}
	if m2.Result.Papers != 5 {
		t.Fatalf("expected 5 papers, got %d", m2.Result.Papers)
	}
}

// TestIntegration_VerifyFlow simulates a verification flow.
func TestIntegration_VerifyFlow(t *testing.T) {
	m := newModel()
	m.Width = 80
	m.Height = 24
	m.InputBar.Mode = "verify"

	resp := &backend.VerifyResponse{
		VerifyID: "v123",
		Verified: true,
		Method:   "hoare",
	}
	newM, _ := m.Update(backend.VerifyMsg{Resp: resp})
	m2 := newM.(model)
	if m2.Mascot.Emotion != "happy" {
		t.Fatalf("expected happy mascot, got %s", m2.Mascot.Emotion)
	}
}
