package backend

import (
	"context"
	"fmt"
	"time"

	tea "github.com/charmbracelet/bubbletea"
)

// ---------------------------------------------------------------------------
// Message types
// ---------------------------------------------------------------------------

// DiscoverMsg is sent when a discovery job is started.
type DiscoverMsg struct {
	JobID string
	Err   error
}

// FlashMsg is sent when a flash job is started.
type FlashMsg struct {
	JobID string
	Err   error
}

// SearchMsg carries search results.
type SearchMsg struct {
	Resp *SearchResponse
	Err  error
}

// VerifyMsg carries verification results.
type VerifyMsg struct {
	Resp *VerifyResponse
	Err  error
}

// PhaseMsg is sent by SSE / polling with pipeline phase updates.
type PhaseMsg struct {
	Phase    string
	Status   string
	Progress float64
	Detail   string
}

// JobCompleteMsg is sent when a job finishes.
type JobCompleteMsg struct {
	JobID  string
	Result map[string]any
	Errors []string
}

// JobFailedMsg is sent when a job fails.
type JobFailedMsg struct {
	JobID  string
	Errors []string
}

// C4NavigateMsg carries C4 path results.
type C4NavigateMsg struct {
	Resp *C4NavigateResponse
	Err  error
}

// TurboMsg is sent when a turbo job is started.
type TurboMsg struct {
	JobID string
	Err   error
}

// TurboFactoryMsg is sent when batch jobs are started.
type TurboFactoryMsg struct {
	JobIDs []string
	Err    error
}

// SSEStartedMsg is sent when an SSE stream is successfully opened.
type SSEStartedMsg struct {
	Events <-chan SSEEvent
	ErrCh  <-chan error
}

// SSEEventMsg wraps a single SSE event delivered to the TUI.
type SSEEventMsg struct {
	Event SSEEvent
}

// SSEErrorMsg signals an SSE stream error without failing the pipeline.
type SSEErrorMsg struct {
	Err error
}

// ---------------------------------------------------------------------------
// Command constructors
// ---------------------------------------------------------------------------

// DiscoverCmd starts a discovery pipeline.
func DiscoverCmd(ctx context.Context, b *Bridge, problem, domain string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return DiscoverMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 2*time.Minute)
		defer cancel()
		resp, err := b.Discover(ctx, problem, domain)
		if err != nil {
			return DiscoverMsg{Err: err}
		}
		return DiscoverMsg{JobID: resp.JobID}
	}
}

// FlashCmd starts a flash discovery pipeline.
func FlashCmd(ctx context.Context, b *Bridge, problem, domain string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return FlashMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
		defer cancel()
		resp, err := b.Flash(ctx, problem, domain)
		if err != nil {
			return FlashMsg{Err: err}
		}
		return FlashMsg{JobID: resp.JobID}
	}
}

// SearchCmd runs a knowledge search.
func SearchCmd(ctx context.Context, b *Bridge, query string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return SearchMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
		defer cancel()
		resp, err := b.Search(ctx, query)
		if err != nil {
			return SearchMsg{Err: err}
		}
		return SearchMsg{Resp: resp}
	}
}

// VerifyCmd runs formal verification.
func VerifyCmd(ctx context.Context, b *Bridge, code, method string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return VerifyMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
		defer cancel()
		resp, err := b.Verify(ctx, code, method)
		if err != nil {
			return VerifyMsg{Err: err}
		}
		return VerifyMsg{Resp: resp}
	}
}

// C4NavigateCmd computes a C4 cognitive path.
func C4NavigateCmd(ctx context.Context, b *Bridge, problem string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return C4NavigateMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
		defer cancel()
		resp, err := b.C4Navigate(ctx, problem)
		if err != nil {
			return C4NavigateMsg{Err: err}
		}
		return C4NavigateMsg{Resp: resp}
	}
}

// TurboCmd starts deep agentic discovery.
func TurboCmd(ctx context.Context, b *Bridge, problem, domain string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return TurboMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 5*time.Minute)
		defer cancel()
		resp, err := b.Turbo(ctx, problem, domain)
		if err != nil {
			return TurboMsg{Err: err}
		}
		return TurboMsg{JobID: resp.JobID}
	}
}

// TurboFactoryCmd starts batch discovery on multiple problems.
func TurboFactoryCmd(ctx context.Context, b *Bridge, problems []string, domain string) tea.Cmd {
	return func() tea.Msg {
		if b == nil {
			return TurboFactoryMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		ctx, cancel := context.WithTimeout(ctx, 10*time.Minute)
		defer cancel()
		resps, err := b.TurboFactory(ctx, problems, domain)
		if err != nil {
			return TurboFactoryMsg{Err: err}
		}
		ids := make([]string, len(resps))
		for i, r := range resps {
			ids[i] = r.JobID
		}
		return TurboFactoryMsg{JobIDs: ids}
	}
}

// PollJobCmd polls a job status and returns the appropriate message.
// Polling bypasses the LLM rate limiter — it's lightweight and necessary for pipeline progress.
// Transient network errors are retried up to 3 times with backoff before marking the job as failed.
func PollJobCmd(ctx context.Context, b *Bridge, jobID string) tea.Cmd {
	return func() tea.Msg {
		if b == nil || b.Client == nil {
			return JobFailedMsg{JobID: jobID, Errors: []string{"backend bridge is nil"}}
		}

		var status *JobStatusResponse
		var err error
		for attempt := 0; attempt < 3; attempt++ {
			if attempt > 0 {
				select {
				case <-ctx.Done():
					return JobFailedMsg{JobID: jobID, Errors: []string{ctx.Err().Error()}}
				case <-time.After(time.Duration(attempt) * 500 * time.Millisecond):
				}
			}
			timeoutCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
			status, err = b.Client.JobStatus(timeoutCtx, jobID)
			cancel()
			if err == nil {
				break
			}
		}
		if err != nil {
			return JobFailedMsg{JobID: jobID, Errors: []string{"poll failed after retries: " + err.Error()}}
		}
		if status.Status == "complete" {
			return JobCompleteMsg{JobID: jobID, Result: status.Result, Errors: status.Errors}
		}
		if status.Status == "failed" {
			return JobFailedMsg{JobID: jobID, Errors: status.Errors}
		}
		return PhaseMsg{
			Phase:    status.Phase,
			Status:   status.Status,
			Progress: status.Progress,
			Detail:   status.PhaseDetail,
		}
	}
}

// SSESubscribeCmd opens an SSE stream for a job.
func SSESubscribeCmd(ctx context.Context, b *Bridge, jobID string) tea.Cmd {
	return func() tea.Msg {
		if b == nil || b.Client == nil {
			return SSEErrorMsg{Err: fmt.Errorf("backend bridge is nil")}
		}
		events, errCh, err := b.Client.SubscribeSSE(ctx, jobID)
		if err != nil {
			return SSEErrorMsg{Err: err}
		}
		return SSEStartedMsg{Events: events, ErrCh: errCh}
	}
}

// SSEPollCmd blocks until the next SSE event or error and returns it.
func SSEPollCmd(events <-chan SSEEvent, errCh <-chan error) tea.Cmd {
	return func() tea.Msg {
		select {
		case event, ok := <-events:
			if !ok {
				return SSEErrorMsg{Err: fmt.Errorf("sse stream closed")}
			}
			return SSEEventMsg{Event: event}
		case err, ok := <-errCh:
			if !ok {
				return SSEErrorMsg{Err: fmt.Errorf("sse error channel closed")}
			}
			return SSEErrorMsg{Err: err}
		}
	}
}

// SSEEventToMsg converts an SSE event into the appropriate TUI message.
func SSEEventToMsg(ev SSEEvent) tea.Msg {
	switch ev.Event {
	case "phase":
		p, err := ParsePhaseEvent(ev.Data)
		if err != nil {
			return SSEErrorMsg{Err: fmt.Errorf("parse phase event: %w", err)}
		}
		return PhaseMsg{
			Phase:    p.Phase,
			Status:   p.Status,
			Progress: p.Progress,
			Detail:   p.Detail,
		}
	case "complete":
		r, err := ParseResultEvent(ev.Data)
		if err != nil {
			return SSEErrorMsg{Err: fmt.Errorf("parse complete event: %w", err)}
		}
		return JobCompleteMsg{
			JobID:  "",
			Result: r.Result,
			Errors: r.Errors,
		}
	case "failed":
		r, err := ParseResultEvent(ev.Data)
		if err != nil {
			return SSEErrorMsg{Err: fmt.Errorf("parse failed event: %w", err)}
		}
		return JobFailedMsg{
			JobID:  "",
			Errors: r.Errors,
		}
	}
	return nil
}
