// Package api — typed SSE event decoder (B-07 client side).
// Replaces the stringly-typed extractResultFromSSEData with a real
// typed switch that knows the canonical event types from §7.4 of the
// unified plan: phase_progress, sim_started, sim_finished, sim_skipped,
// cost_update, paper_discovered, complete, failed.
package api

import (
	"encoding/json"
	"fmt"
)

// SSEEventType is the canonical type field of an SSE event.
type SSEEventType string

const (
	EventPhaseProgress    SSEEventType = "phase_progress"
	EventPhaseChange      SSEEventType = "phase_change"
	EventPaperDiscovered  SSEEventType = "paper_discovered"
	EventTokenStream      SSEEventType = "token_stream"
	EventCostUpdate       SSEEventType = "cost_update"
	EventWarning          SSEEventType = "warning"
	EventLog              SSEEventType = "log"
	EventSimStarted       SSEEventType = "sim_started"
	EventSimFinished      SSEEventType = "sim_finished"
	EventSimSkipped       SSEEventType = "sim_skipped"
	EventSimBudgetExceeded SSEEventType = "sim_budget_exceeded"
	EventComplete         SSEEventType = "complete"
	EventPartial          SSEEventType = "partial"
	EventFailed           SSEEventType = "failed"
	EventCancelled        SSEEventType = "cancelled"
	// Legacy v8.12 events still emitted by the current backend:
	EventLegacyPhase      SSEEventType = "phase"
	EventLegacyComplete   SSEEventType = "complete_v8"
)

// TypedEvent is the decoded form of an SSEEvent. The Type field is the
// canonical name; Type-specific fields are populated accordingly.
type TypedEvent struct {
	Type SSEEventType `json:"type"`
	Ts   string       `json:"ts,omitempty"`
	JobID string      `json:"job_id,omitempty"`

	// Phase / progress fields
	Phase        string  `json:"phase,omitempty"`
	Substep      string  `json:"substep,omitempty"`
	Progress     float64 `json:"progress,omitempty"`
	ETASeconds   int     `json:"eta_seconds,omitempty"`
	PhaseDetail  string  `json:"detail,omitempty"`

	// Sim fields (for sim_* events)
	Engine         string      `json:"engine,omitempty"`
	Pattern        string      `json:"pattern,omitempty"`
	EngineStatus   string      `json:"engine_status,omitempty"`
	Verdict        string      `json:"verdict,omitempty"`
	ElapsedMS      int         `json:"elapsed_ms,omitempty"`
	CostUSD        float64     `json:"cost_usd,omitempty"`
	BackendHost    string      `json:"backend_host,omitempty"`
	HypothesisID   string      `json:"hypothesis_id,omitempty"`
	Reason         string      `json:"reason,omitempty"`
	InstallHint    string      `json:"install_hint,omitempty"`
	FallbackUsed   string      `json:"fallback_used,omitempty"`
	PatternsTried  []string    `json:"patterns_tried,omitempty"`
	Evidence       interface{} `json:"evidence,omitempty"`

	// Generic
	Status string                 `json:"status,omitempty"`
	Result map[string]interface{} `json:"result,omitempty"`
	Errors []string               `json:"errors,omitempty"`
	LogTail []string             `json:"log_tail,omitempty"`
}

// DecodeTypedEvent parses the Data field of an SSEEvent into a TypedEvent.
// Returns a zero TypedEvent and an error if the data is not valid JSON.
func DecodeTypedEvent(data string) (TypedEvent, error) {
	var e TypedEvent
	if data == "" {
		return e, fmt.Errorf("empty SSE data")
	}
	if err := json.Unmarshal([]byte(data), &e); err != nil {
		return e, fmt.Errorf("decode SSE data: %w", err)
	}
	// Map legacy v8.12 "phase" → phase_progress when fields look right
	if e.Type == "" {
		// No type field — infer from fields. A terminal status wins over
		// phase/progress: the legacy v8.12 "complete" event also carries a
		// final phase ("G: Quality") and progress=1.0, so the status check
		// must come first or completion gets misread as phase progress.
		switch {
		case e.Status == "failed":
			e.Type = EventFailed
		case e.Status == "cancelled":
			e.Type = EventCancelled
		case e.Status == "partial":
			e.Type = EventPartial
		case e.Status == "complete", e.Status == "success":
			e.Type = EventComplete
		case e.Phase != "" || e.Progress > 0:
			e.Type = EventPhaseProgress
		default:
			e.Type = EventLog
		}
	}
	// Normalize explicit type=partial from JobStore
	if e.Type == EventPartial && e.Status == "" {
		e.Status = "partial"
	}
	return e, nil
}

// LegacyExtract is the backwards-compat shim for v8.12 events that don't
// have a 'type' field. Returns the (status, phase, progress, result,
// completed) tuple that the existing update.go expects. New code should
// use DecodeTypedEvent.
func LegacyExtract(data string) (status, phase string, progress float64, result map[string]interface{}, completed bool) {
	e, err := DecodeTypedEvent(data)
	if err != nil {
		return
	}
	status = e.Status
	phase = e.Phase
	progress = e.Progress
	result = e.Result
	// Detect completion by status value, not by inferred type
	completed = status == "complete" || status == "failed" || status == "partial"
	return
}
