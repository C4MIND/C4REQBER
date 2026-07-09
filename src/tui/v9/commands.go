package tui

import (
	"context"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

// submitCmd fires a discovery request.
// v9.12.2: chain auth steps — Health/Register/Login errors propagate
// as apiSubmitMsg so the user sees a meaningful error instead of a
// confusing "CSRF token missing" from the downstream OneClick call.
func submitCmd(c *api.Client, query, domain, tier string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		if err := ensureAPIAuth(ctx, c); err != nil {
			return apiSubmitMsg{err: err}
		}
		id, err := c.OneClickWithTier(ctx, query, domain, tier, "human")
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
			return sseEventMsg{event: ev, events: events, cancel: cancel}
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
			return sseEventMsg{event: ev, events: events, cancel: cancel}
		case <-time.After(8 * time.Second):
			return sseClosedMsg{} // periodic keepalive / no events
		}
	}
}

// flashCmd runs /v8/discover/flash (sync, ~5-10s).
func flashCmd(c *api.Client, query string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		if err := ensureAPIAuth(ctx, c); err != nil {
			return flashResultMsg{err: err}
		}
		result, err := c.FlashAndWait(ctx, query, "science")
		return flashResultMsg{result: result, err: err}
	}
}

// extractResultFromSSEData parses the data field of an SSE event and returns
// a partial JobStatus (status, phase, progress, result, completed).
// v9.13: now uses the typed decoder (api.DecodeTypedEvent) for proper
// handling of all SSE event types — including the new sim_* events.
func extractResultFromSSEData(data string) (status, phase string, progress float64, result map[string]any, completed bool) {
	return api.LegacyExtract(data)
}
