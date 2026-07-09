package api

import (
	"encoding/json"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/internal/oapi"
)

// Contract tests: handwritten SSE decoder must accept OpenAPI-generated payloads.
func TestOpenAPIContract_PhaseProgress(t *testing.T) {
	raw := `{"type":"phase_progress","phase":"A: Framing","progress":0.15,"status":"running","job_id":"job_abc"}`
	var gen oapi.SSEPhaseProgress
	if err := json.Unmarshal([]byte(raw), &gen); err != nil {
		t.Fatalf("generated type unmarshal: %v", err)
	}
	typed, err := DecodeTypedEvent(raw)
	if err != nil {
		t.Fatalf("DecodeTypedEvent: %v", err)
	}
	if typed.Type != EventPhaseProgress {
		t.Fatalf("type=%q want %q", typed.Type, EventPhaseProgress)
	}
	if typed.Phase != "A: Framing" {
		t.Fatalf("phase=%q", typed.Phase)
	}
}

func TestOpenAPIContract_SimFinished(t *testing.T) {
	raw := `{"type":"sim_finished","engine":"newton","pattern":"pid_tuning","verdict":"completed","engine_status":"ok"}`
	var gen oapi.SSESimFinished
	if err := json.Unmarshal([]byte(raw), &gen); err != nil {
		t.Fatalf("generated type unmarshal: %v", err)
	}
	typed, err := DecodeTypedEvent(raw)
	if err != nil {
		t.Fatalf("DecodeTypedEvent: %v", err)
	}
	if typed.Type != EventSimFinished {
		t.Fatalf("type=%q want %q", typed.Type, EventSimFinished)
	}
	if typed.Engine != "newton" {
		t.Fatalf("engine=%q", typed.Engine)
	}
}

func TestOpenAPIContract_Complete(t *testing.T) {
	raw := `{"type":"complete","status":"complete","phase":"G: Quality","progress":1.0}`
	var gen oapi.SSEComplete
	if err := json.Unmarshal([]byte(raw), &gen); err != nil {
		t.Fatalf("generated type unmarshal: %v", err)
	}
	typed, err := DecodeTypedEvent(raw)
	if err != nil {
		t.Fatalf("DecodeTypedEvent: %v", err)
	}
	if typed.Type != EventComplete {
		t.Fatalf("type=%q want %q", typed.Type, EventComplete)
	}
}