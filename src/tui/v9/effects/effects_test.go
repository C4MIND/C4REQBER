package effects

import (
	"strings"
	"testing"
)

func TestRainInitial(t *testing.T) {
	r := NewRain()
	r.SetSize(80, 24)
	// Initial state: all drops at negative y → should be empty (anyOnScreen=false)
	if r.Render() != "" {
		t.Error("rain initial state should render empty (all drops off-screen)")
	}
}

func TestRainAdvance(t *testing.T) {
	r := NewRain()
	r.SetSize(80, 24)
	for i := 0; i < 100; i++ {
		r.Tick()
	}
	out := r.Render()
	if len(out) == 0 {
		t.Error("rain should have content after 100 ticks")
	}
	// Should have at least some non-space chars
	if !strings.ContainsAny(out, "abcdefghijklmnopqrstuvwxyz0123456789@#$%&*+-/=<>?^_~") {
		t.Error("rain should have varied chars after ticks")
	}
}

func TestBurstInactive(t *testing.T) {
	b := NewBurst()
	if b.Render() != "" {
		t.Error("inactive burst should render empty")
	}
}

func TestBurstActive(t *testing.T) {
	b := NewBurst()
	b.Trigger(80, 24, 40, 12)
	if !b.Active() {
		t.Error("burst should be active after Trigger")
	}
	out := b.Render()
	if out == "" {
		t.Error("active burst should render non-empty")
	}
	// Tick down
	for i := 0; i < 100; i++ {
		b.Tick()
	}
	// Eventually expires
}

func TestSparklesEmit(t *testing.T) {
	s := NewSparkles()
	s.SetSize(80, 24)
	if s.Render() != "" {
		t.Error("sparkles should be empty before emit")
	}
	s.Emit(40, 12, 5)
	if !s.Active() {
		t.Error("sparkles should be active after Emit")
	}
	out := s.Render()
	if out == "" {
		t.Error("sparkles should render after Emit")
	}
}

func TestSparklesExpire(t *testing.T) {
	s := NewSparkles()
	s.SetSize(80, 24)
	s.Emit(40, 12, 5)
	for i := 0; i < 50; i++ {
		s.Tick()
	}
	if s.Active() {
		t.Error("sparkles should expire after 50 ticks")
	}
}

func TestTypewriterReveal(t *testing.T) {
	tw := NewTypewriter()
	tw.Set("Hello world", 0)
	if tw.View() != "" {
		t.Error("typewriter should start empty (tick 0)")
	}
	for i := 0; i < 50; i++ {
		tw.Tick(i * 5)
	}
	got := tw.View()
	if got != "Hello world" {
		t.Errorf("typewriter final = %q, want %q", got, "Hello world")
	}
}

func TestTypewriterPartial(t *testing.T) {
	tw := NewTypewriter()
	tw.Set("ABCDE", 0)
	tw.Tick(0) // 1 char
	tw.Tick(1) // skipped (delta < 2)
	tw.Tick(2) // another
	got := tw.View()
	if len(got) > 5 || len(got) < 1 {
		t.Errorf("partial reveal unexpected: %q (len %d)", got, len(got))
	}
}

func TestSlideInTrigger(t *testing.T) {
	sl := NewSlideIn()
	if sl.Active() {
		t.Error("slidein should not start active")
	}
	sl.Trigger()
	if !sl.Active() {
		t.Error("slidein should be active after Trigger")
	}
	// Advance to settled
	for i := 0; i < 200; i++ {
		sl.Tick()
	}
	if sl.Active() {
		t.Error("slidein should settle after 200 ticks")
	}
}
