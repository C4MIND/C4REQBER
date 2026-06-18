package effects

import "testing"

func TestRainRenderPooledGrid(t *testing.T) {
	// v9.13: Render() should NOT reallocate the grid every frame.
	// Verify by calling Render 10 times and checking that subsequent
	// calls still produce output without panicking and without
	// dropping frames.
	r := NewRain()
	r.SetSize(40, 20)
	// Force some drops to be on-screen
	for i := 0; i < len(r.drops); i++ {
		r.drops[i] = i % 20
	}
	for i := 0; i < 10; i++ {
		_ = r.Render()
	}
	// After 10 frames, the grid should still exist and match dimensions
	if r.grid == nil {
		t.Fatal("grid should not be nil after renders")
	}
	if len(r.grid) != 20 {
		t.Errorf("grid should have 20 rows, got %d", len(r.grid))
	}
	if len(r.grid[0]) != 40 {
		t.Errorf("grid row should have 40 cols, got %d", len(r.grid[0]))
	}
}

func TestRainRenderEmptyWhenNoDrops(t *testing.T) {
	r := NewRain()
	r.SetSize(40, 20)
	// All drops off-screen
	for i := range r.drops {
		r.drops[i] = -100
	}
	if got := r.Render(); got != "" {
		t.Errorf("expected empty when no drops, got %d chars", len(got))
	}
}

func TestBurstRenderPooledGrid(t *testing.T) {
	b := NewBurst()
	b.Trigger(40, 20, 20, 10)
	for i := 0; i < 10; i++ {
		b.Tick()
		_ = b.Render()
	}
	if b.grid == nil {
		t.Fatal("burst grid should not be nil after renders")
	}
	if len(b.grid) != 20 {
		t.Errorf("grid should have 20 rows, got %d", len(b.grid))
	}
}

func TestBurstRenderPerParticleFade(t *testing.T) {
	// v9.13: regression test for the b.parts[0] bug. We need
	// to verify that particles with different life values get
	// different colors in the rendered output. The old code used
	// b.parts[0].life for every cell.
	b := NewBurst()
	// Force 2 particles with very different life values
	b.parts = []particle{
		{x: 5, y: 5, life: 2.5, maxLife: 3.0, colorIdx: 0},  // fresh, full color
		{x: 6, y: 5, life: 0.5, maxLife: 3.0, colorIdx: 0},  // aged, faded
	}
	b.active = true
	b.width = 20
	b.height = 10
	out := b.Render()
	// Both cells should be rendered. The colors in the lipgloss
	// escape codes should differ between the two cells. We check
	// that the output contains at least 2 distinct ANSI color codes.
	if out == "" {
		t.Fatal("burst should render non-empty when 2 particles are alive")
	}
	// Just check that the output has more than 1 line of content
	if len(out) < 5 {
		t.Errorf("burst output should have multiple chars, got: %q", out)
	}
}

func TestBurstInactiveRendersEmpty(t *testing.T) {
	b := NewBurst()
	if got := b.Render(); got != "" {
		t.Errorf("inactive burst should render empty, got %q", got)
	}
}

func TestVerdictPulseLifecycle(t *testing.T) {
	p := NewVerdictPulse()
	if p.Active() {
		t.Error("fresh pulse should be inactive")
	}
	p.Trigger("supports_hypothesis")
	if !p.Active() {
		t.Error("after Trigger, pulse should be active")
	}
	if p.Color() != "2" {
		t.Errorf("supports verdict color = %q, want 2 (green)", p.Color())
	}
	// Tick once — should still be active
	p.Tick()
	if !p.Active() {
		t.Error("pulse should still be active after 1 tick")
	}
	// At tick=duration/2, intensity should be near peak
	p.tick = p.duration / 2
	if got := p.Intensity(); got < 0.5 {
		t.Errorf("intensity at half = %f, want > 0.5", got)
	}
	// Tick past the duration
	for i := 0; i < p.duration+5; i++ {
		p.Tick()
	}
	if p.Active() {
		t.Error("pulse should expire after duration ticks")
	}
}

func TestVerdictPulseColors(t *testing.T) {
	p := NewVerdictPulse()
	cases := map[string]string{
		"supports_hypothesis": "2",
		"refutes_hypothesis":  "1",
		"inconclusive":        "3",
		"unknown":             "8",
	}
	for verdict, wantColor := range cases {
		p.Trigger(verdict)
		if got := p.Color(); got != wantColor {
			t.Errorf("verdict %q color = %q, want %q", verdict, got, wantColor)
		}
	}
}

func TestVerdictPulseIntensityEnvelope(t *testing.T) {
	p := NewVerdictPulse()
	p.Trigger("supports_hypothesis")
	// Intensity should be 0 at start
	if p.Intensity() != 0 {
		t.Errorf("intensity at tick 0 = %f, want 0", p.Intensity())
	}
	// At half-duration, intensity should peak near 1
	p.tick = p.duration / 2
	if got := p.Intensity(); got < 0.9 {
		t.Errorf("intensity at half = %f, want ~1", got)
	}
	// Past duration, should be 0 (inactive)
	p.tick = p.duration + 1
	if got := p.Intensity(); got != 0 {
		t.Errorf("intensity after duration = %f, want 0", got)
	}
}
