package backend

import (
	"testing"
	"time"
)

func TestRateLimiter_AllowsUnderLimit(t *testing.T) {
	rl := NewRateLimiter(3, time.Second)
	for i := 0; i < 3; i++ {
		if err := rl.Acquire(); err != nil {
			t.Fatalf("expected acquire %d to succeed, got %v", i+1, err)
		}
	}
}

func TestRateLimiter_BlocksOverLimit(t *testing.T) {
	rl := NewRateLimiter(2, time.Second)
	_ = rl.Acquire()
	_ = rl.Acquire()
	if err := rl.Acquire(); err == nil {
		t.Fatal("expected acquire over limit to fail")
	} else if _, ok := err.(*RateLimitError); !ok {
		t.Fatalf("expected RateLimitError, got %T", err)
	}
}

func TestRateLimiter_Reset(t *testing.T) {
	rl := NewRateLimiter(1, time.Second)
	_ = rl.Acquire()
	if err := rl.Acquire(); err == nil {
		t.Fatal("expected second acquire to fail")
	}
	rl.Reset()
	if err := rl.Acquire(); err != nil {
		t.Fatalf("expected acquire after reset to succeed, got %v", err)
	}
}

func TestRateLimiter_SlidingWindow(t *testing.T) {
	rl := NewRateLimiter(2, 100*time.Millisecond)
	_ = rl.Acquire()
	_ = rl.Acquire()
	if err := rl.Acquire(); err == nil {
		t.Fatal("expected third acquire to fail immediately")
	}
	time.Sleep(120 * time.Millisecond)
	if err := rl.Acquire(); err != nil {
		t.Fatalf("expected acquire after window to succeed, got %v", err)
	}
}

func TestRateLimiter_AcquireN(t *testing.T) {
	rl := NewRateLimiter(5, time.Second)
	if err := rl.AcquireN(3); err != nil {
		t.Fatalf("expected AcquireN(3) to succeed, got %v", err)
	}
	if err := rl.AcquireN(3); err == nil {
		t.Fatal("expected AcquireN(3) to fail (only 2 slots left)")
	}
	if err := rl.AcquireN(2); err != nil {
		t.Fatalf("expected AcquireN(2) to succeed, got %v", err)
	}
	if err := rl.Acquire(); err == nil {
		t.Fatal("expected Acquire to fail (limit exhausted)")
	}
}

func TestRateLimiter_AcquireN_Zero(t *testing.T) {
	rl := NewRateLimiter(1, time.Second)
	if err := rl.AcquireN(0); err != nil {
		t.Fatalf("expected AcquireN(0) to succeed, got %v", err)
	}
}
