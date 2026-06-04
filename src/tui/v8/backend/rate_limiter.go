package backend

import (
	"fmt"
	"sync"
	"time"
)

// RateLimitError is returned when a rate limit is exceeded.
type RateLimitError struct {
	MaxCalls int
	Period   time.Duration
	RetryIn  time.Duration
}

func (e *RateLimitError) Error() string {
	return fmt.Sprintf("rate limit exceeded (%d/%v), retry in %.1fs", e.MaxCalls, e.Period, e.RetryIn.Seconds())
}

// RateLimiter implements a sliding-window rate limiter.
type RateLimiter struct {
	maxCalls int
	period   time.Duration
	calls    []time.Time
	mu       sync.Mutex
}

// NewRateLimiter creates a limiter with maxCalls allowed per period.
func NewRateLimiter(maxCalls int, period time.Duration) *RateLimiter {
	return &RateLimiter{
		maxCalls: maxCalls,
		period:   period,
		calls:    make([]time.Time, 0, maxCalls),
	}
}

// Acquire blocks until a slot is available or returns RateLimitError.
func (rl *RateLimiter) Acquire() error {
	return rl.AcquireN(1)
}

// AcquireN reserves n slots atomically, or returns RateLimitError if not enough room.
func (rl *RateLimiter) AcquireN(n int) error {
	if n <= 0 {
		return nil
	}
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	cutoff := now.Add(-rl.period)
	// Drop old calls outside the window
	start := 0
	allOld := true
	for i, t := range rl.calls {
		if !t.Before(cutoff) {
			start = i
			allOld = false
			break
		}
	}
	if allOld {
		rl.calls = rl.calls[:0]
	} else {
		rl.calls = rl.calls[start:]
	}

	if len(rl.calls)+n > rl.maxCalls {
		wait := time.Duration(0)
		if len(rl.calls) > 0 {
			wait = rl.calls[0].Sub(cutoff)
		}
		return &RateLimitError{
			MaxCalls: rl.maxCalls,
			Period:   rl.period,
			RetryIn:  wait,
		}
	}
	for i := 0; i < n; i++ {
		rl.calls = append(rl.calls, now)
	}
	return nil
}

// Release returns n tokens to the bucket (removes the most recent n call records).
func (rl *RateLimiter) Release(n int) {
	if n <= 0 {
		return
	}
	rl.mu.Lock()
	defer rl.mu.Unlock()
	if n >= len(rl.calls) {
		rl.calls = rl.calls[:0]
	} else {
		rl.calls = rl.calls[:len(rl.calls)-n]
	}
}

// Reset clears the call history.
func (rl *RateLimiter) Reset() {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	rl.calls = rl.calls[:0]
}
