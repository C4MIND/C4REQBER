package demo

import (
	"context"
	"testing"
	"time"
)

func TestDefaultScript(t *testing.T) {
	s := Default("test topic")
	if s.Topic != "test topic" {
		t.Error("topic not set")
	}
	if len(s.Events) == 0 {
		t.Error("no events")
	}
	// 1 submit + 7 phase + 1 hypothesis + 2 papers = 11
	if len(s.Events) != 11 {
		t.Errorf("expected 11 events, got %d", len(s.Events))
	}
	// Check sequence: submit → phases → hypothesis → papers
	if s.Events[0].Kind != "submit" {
		t.Error("first event should be submit")
	}
	if s.Events[len(s.Events)-1].Kind != "paper" {
		t.Error("last event should be paper")
	}
}

func TestScriptTotalTime(t *testing.T) {
	s := Default("test")
	var total time.Duration
	for _, e := range s.Events {
		total += e.Delay
	}
	if total != s.TotalTime {
		t.Errorf("total delay %s != declared %s", total, s.TotalTime)
	}
}

func TestScriptRun(t *testing.T) {
	s := &Script{
		Topic:     "fast",
		TotalTime: 50 * time.Millisecond,
		Events: []CardEvent{
			{Delay: 10 * time.Millisecond, Kind: "phase", Title: "Phase 1"},
			{Delay: 20 * time.Millisecond, Kind: "phase", Title: "Phase 2"},
			{Delay: 20 * time.Millisecond, Kind: "phase", Title: "Phase 3"},
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	count := 0
	err := s.Run(ctx, func(e CardEvent) { count++ })
	if err != nil {
		t.Fatalf("run failed: %v", err)
	}
	if count != 3 {
		t.Errorf("got %d events, want 3", count)
	}
}

func TestAsAPIResult(t *testing.T) {
	s := Default("test")
	r := s.AsAPIResult()
	if r["status"] != "complete" {
		t.Error("status wrong")
	}
	res, _ := r["result"].(map[string]any)
	if res == nil {
		t.Fatal("no result")
	}
	hyp, _ := res["hypothesis"].(map[string]any)
	if hyp == nil {
		t.Fatal("no hypothesis")
	}
	if hyp["text"] == nil {
		t.Error("hypothesis text missing")
	}
	papers, ok := res["papers"].([]any)
	if !ok || len(papers) != 2 {
		t.Errorf("expected 2 papers, got %d", len(papers))
	}
}

func TestScriptRunCancel(t *testing.T) {
	s := &Script{
		Topic:     "test",
		TotalTime: 5 * time.Second,
		Events: []CardEvent{
			{Delay: 100 * time.Millisecond, Kind: "phase"},
			{Delay: 5 * time.Second, Kind: "phase"},
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	err := s.Run(ctx, func(e CardEvent) {})
	if err == nil {
		t.Error("expected context error")
	}
}
