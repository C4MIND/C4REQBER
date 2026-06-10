package tui

import (
	"context"
	"encoding/json"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

// submitCmd fires a discovery request.
func submitCmd(c *api.Client, query, domain, tier string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		_ = c.Health(ctx)
		_ = c.Register(ctx, "kilo-v9@test.com", "test12345", "Kilo v9")
		_ = c.Login(ctx, "kilo-v9@test.com", "test12345")
		id, err := c.OneClickWithTier(ctx, query, domain, tier)
		return apiSubmitMsg{jobID: id, err: err}
	}
}

// pollCmd polls /v8/discover/status/{job_id}. Used as fallback when SSE fails.
func pollCmd(c *api.Client, jobID string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		js, err := c.JobStatus(ctx, jobID)
		if err != nil {
			return apiPollMsg{err: err}
		}
		return apiPollMsg{
			status:    js.Status,
			phase:     js.Phase,
			progress:  js.Progress,
			result:    js.Result,
			completed: js.Completed,
		}
	}
}

// sseCmd opens an SSE stream for the given jobID and returns a tea.Cmd that
// produces sseEventMsg values for each event from the server.
// Caller invokes sseCancelCmd with the same jobID to stop streaming.
func sseCmd(c *api.Client, jobID string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithCancel(context.Background())
		events, _, err := c.Stream(ctx, jobID)
		if err != nil {
			cancel()
			return sseErrorMsg{err: err}
		}
		// Drain first event synchronously to keep state machine deterministic
		select {
		case ev, ok := <-events:
			if !ok {
				cancel()
				return sseErrorMsg{err: nil} // closed
			}
			return sseEventMsg{event: ev, cancel: cancel}
		case <-time.After(8 * time.Second):
			cancel()
			return sseErrorMsg{err: nil} // timeout
		}
	}
}

// sseContinueCmd continues streaming — invoked when previous sseEventMsg arrived.
func sseContinueCmd(events <-chan api.SSEEvent, cancel func()) tea.Cmd {
	return func() tea.Msg {
		select {
		case ev, ok := <-events:
			if !ok {
				return sseClosedMsg{}
			}
			return sseEventMsg{event: ev, cancel: cancel}
		case <-time.After(8 * time.Second):
			return sseClosedMsg{} // periodic keepalive / no events
		}
	}
}

// papersCmd for /v8/knowledge/search.
func papersCmd(c *api.Client, query string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		papers, err := c.KnowledgeSearch(ctx, query, 3)
		if err != nil {
			return apiPapersMsg{err: err}
		}
		return apiPapersMsg{papers: papers}
	}
}

// flashCmd runs /v8/discover/flash (sync, ~5-10s).
func flashCmd(c *api.Client, query string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		_ = c.Health(ctx)
		_ = c.Register(ctx, "kilo-v9@test.com", "test12345", "Kilo v9")
		_ = c.Login(ctx, "kilo-v9@test.com", "test12345")
		result, err := c.Flash(ctx, query, "science")
		return flashResultMsg{result: result, err: err}
	}
}

// multiCmd runs /v8/discover/multi (sync, multi-hypothesis).
func multiCmd(c *api.Client, query string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
		defer cancel()
		_ = c.Health(ctx)
		_ = c.Register(ctx, "kilo-v9@test.com", "test12345", "Kilo v9")
		_ = c.Login(ctx, "kilo-v9@test.com", "test12345")
		result, err := c.Multi(ctx, query, "science", 3)
		return multiResultMsg{result: result, err: err}
	}
}

// extractResultFromSSEData parses the data field of an SSE event and returns
// a partial JobStatus (status, phase, progress, result, completed).
func extractResultFromSSEData(data string) (status, phase string, progress float64, result map[string]any, completed bool) {
	if data == "" {
		return
	}
	var m map[string]any
	if err := json.Unmarshal([]byte(data), &m); err != nil {
		// non-JSON data — just keep as raw
		return
	}
	status = fieldString(m, "status")
	phase = fieldString(m, "phase")
	progress = 0
	if v, ok := m["progress"].(float64); ok {
		progress = v
	}
	if r, ok := m["result"].(map[string]any); ok {
		result = r
	}
	completed = status == "complete" || status == "failed" || status == "partial"
	return
}
