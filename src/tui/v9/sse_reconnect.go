package tui

import (
	"context"
	"sync"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

// ReconnectPolicy controls SSE auto-reconnect with exponential backoff.
type ReconnectPolicy struct {
	MaxAttempts  int           // total attempts before giving up (0 = infinite)
	InitialDelay time.Duration // first retry delay (default 500ms)
	MaxDelay     time.Duration // cap on backoff (default 30s)
	Multiplier   float64       // backoff multiplier (default 2.0)
}

// DefaultReconnectPolicy is used unless overridden via env C4_SSE_RECONNECT.
func DefaultReconnectPolicy() ReconnectPolicy {
	return ReconnectPolicy{
		MaxAttempts:  0, // infinite
		InitialDelay: 500 * time.Millisecond,
		MaxDelay:     30 * time.Second,
		Multiplier:   2.0,
	}
}

// sseState tracks reconnect state for one job.
type sseState struct {
	mu          sync.Mutex
	attempts    int
	cancelled   bool
	policy      ReconnectPolicy
	streamErrCb func(err error, attempt int) // for UI feedback
}

// NewSSEState returns a fresh state for tracking a stream.
func NewSSEState(policy ReconnectPolicy, onErr func(error, int)) *sseState {
	return &sseState{policy: policy, streamErrCb: onErr}
}

// NextDelay returns the delay for the next reconnect attempt (0 if cancelled or exhausted).
func (s *sseState) NextDelay() time.Duration {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.cancelled {
		return 0
	}
	if s.policy.MaxAttempts > 0 && s.attempts >= s.policy.MaxAttempts {
		return 0
	}
	s.attempts++
	delay := s.policy.InitialDelay
	for i := 1; i < s.attempts; i++ {
		delay = time.Duration(float64(delay) * s.policy.Multiplier)
		if delay > s.policy.MaxDelay {
			delay = s.policy.MaxDelay
			break
		}
	}
	return delay
}

// Cancel marks the state as cancelled (no more reconnects).
func (s *sseState) Cancel() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.cancelled = true
}

// Cancelled returns whether the state has been cancelled.
func (s *sseState) Cancelled() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.cancelled
}

// Attempts returns the current attempt count.
func (s *sseState) Attempts() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.attempts
}

// SSEStreamResult is the message returned by sseStreamWithReconnect.
type SSEStreamResult struct {
	JobID    string
	Event    api.SSEEvent
	Err      error
	Attempt  int
	Reopened bool // true if this event came from a reconnect
}


func sseStreamWithReconnect(ctx context.Context, c *api.Client, jobID string, state *sseState) <-chan SSEStreamResult {
	out := make(chan SSEStreamResult, 16)
	go func() {
		defer close(out)
		for {
			if state.Cancelled() {
				return
			}
			attempt := state.Attempts()
			events, cancelFn, err := c.Stream(ctx, jobID)
			if err != nil {
				state.mu.Lock()
				_ = err // ensure used
				state.mu.Unlock()
				if state.streamErrCb != nil {
					state.streamErrCb(err, attempt)
				}
				delay := state.NextDelay()
				if delay == 0 {
					out <- SSEStreamResult{JobID: jobID, Err: err, Attempt: attempt}
					return
				}
				time.Sleep(delay)
				continue
			}
			// Stream opened — drain events
			opened := attempt > 0
			streamDone := false
			for ev := range events {
				if state.Cancelled() {
					cancelFn()
					return
				}
				out <- SSEStreamResult{JobID: jobID, Event: ev, Attempt: attempt, Reopened: opened}
			}
			cancelFn()
			// If we got here without an explicit "complete" event, reconnect
			// (this is the reconnect path: server closed connection early)
			_ = streamDone
			if state.Cancelled() {
				return
			}
			delay := state.NextDelay()
			if delay == 0 {
				return
			}
			time.Sleep(delay)
		}
	}()
	return out
}
