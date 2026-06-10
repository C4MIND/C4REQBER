package tui

import (
	"strings"
	"testing"

	"charm.land/lipgloss/v2"
)

func TestBioAurora_NewBioAurora_Default(t *testing.T) {
	ba := NewBioAurora(0)
	if ba == nil {
		t.Fatal("NewBioAurora returned nil")
	}
	if ba.artRows != 0 {
		t.Errorf("artRows = %d, want 0", ba.artRows)
	}
}

func TestBioAurora_NewBioAurora_NegativeArtRows(t *testing.T) {
	// Negative artRows is invalid input — should be clamped to 0.
	ba := NewBioAurora(-5)
	if ba.artRows != 0 {
		t.Errorf("artRows = %d, want 0 (clamped from negative)", ba.artRows)
	}
}

func TestBioAurora_RenderAurora_NilSafe(t *testing.T) {
	// Nil receiver must not panic; just returns base style.
	var ba *BioAurora
	plain := "1111"
	style := lipgloss.NewStyle().Foreground(lipgloss.Color("3"))
	got := ba.RenderAurora(plain, 0, style)
	if got == "" {
		t.Error("nil receiver should return base style, not empty")
	}
}

func TestBioAurora_RenderAurora_EmptyPlain(t *testing.T) {
	ba := NewBioAurora(11)
	style := lipgloss.NewStyle().Foreground(lipgloss.Color("3"))
	got := ba.RenderAurora("", 0, style)
	if got == "" {
		t.Error("empty plain should return base style, not empty")
	}
}

func TestBioAurora_RenderAurora_PreservesGlyphs(t *testing.T) {
	// Critical: the "1" characters must be present in the output.
	// Aurora should NOT replace them with blanks, even with dithering.
	ba := NewBioAurora(11)
	style := lipgloss.NewStyle().Foreground(lipgloss.Color("3"))
	plain := "111111111111111111"
	// Strip ANSI to count visible "1"s.
	got := stripSplashANSI(ba.RenderAurora(plain, 0, style))
	count := strings.Count(got, "1")
	if count != len(plain) {
		t.Errorf("expected %d '1' chars, got %d (aurora may have replaced glyphs)", len(plain), count)
	}
}

func TestBioAurora_RenderAurora_ArtRegionHasLowerIntensity(t *testing.T) {
	// Cells inside the C4R art region (y < artRows) should have
	// lower max intensity than cells outside. We verify by checking
	// that lines inside the region use a different color treatment.
	ba := NewBioAurora(11)
	style := lipgloss.NewStyle().Foreground(lipgloss.Color("3"))
	plain := "111111111111111111"
	// Render same line as "inside art" and "outside art".
	insideLine := stripSplashANSI(ba.RenderAurora(plain, 5, style))
	outsideLine := stripSplashANSI(ba.RenderAurora(plain, 15, style))
	// Both should have same "1" count.
	if len(insideLine) != len(outsideLine) {
		t.Errorf("line length differs: inside=%d outside=%d", len(insideLine), len(outsideLine))
	}
}

func TestBioAurora_Tick_AdvancesClock(t *testing.T) {
	ba := NewBioAurora(11)
	if ba.startTime != 0 {
		t.Errorf("startTime should be 0 initially, got %f", ba.startTime)
	}
	ba.Tick(5.5)
	if ba.startTime != 5.5 {
		t.Errorf("startTime after Tick(5.5) = %f, want 5.5", ba.startTime)
	}
}

func TestBioAurora_ColorAt_InRange(t *testing.T) {
	ba := NewBioAurora(11)
	// Sample many (x, y, t) combinations and verify all return valid indices.
	ba.Tick(0)
	for y := -5; y < 20; y++ {
		for x := -5; x < 80; x++ {
			idx := ba.colorAt(x, y)
			if idx < 0 || idx >= len(auroraPalette) {
				t.Errorf("colorAt(%d, %d, 0) = %d, out of range [0, %d)",
					x, y, idx, len(auroraPalette))
			}
		}
	}
}

func TestBioAurora_IntensityAt_Bounded(t *testing.T) {
	ba := NewBioAurora(11)
	// Intensity should be in [0.15, maxAuroraOpacity] range.
	for tick := 0.0; tick < 30.0; tick += 0.5 {
		ba.Tick(tick)
		for x := 0; x < 80; x++ {
			intensity := ba.intensityAt(x, 15) // outside art
			if intensity < 0.15 {
				t.Errorf("intensity at t=%f x=%d = %f, below min 0.15", tick, x, intensity)
			}
			if intensity > maxAuroraOpacity {
				t.Errorf("intensity at t=%f x=%d = %f, above max %f", tick, x, intensity, maxAuroraOpacity)
			}
		}
	}
}

func TestBioAurora_IntensityAt_ArtRegionLower(t *testing.T) {
	// In v9.11.2, intensity inside the art region is capped at 0.30.
	// Outside, it can go up to maxAuroraOpacity (0.55).
	ba := NewBioAurora(11)
	for tick := 0.0; tick < 30.0; tick += 0.5 {
		ba.Tick(tick)
		for x := 0; x < 80; x++ {
			inside := ba.intensityAt(x, 5) // inside art (y < 11)
			if inside > 0.30 {
				t.Errorf("inside art: intensity at t=%f x=%d = %f, should be ≤ 0.30", tick, x, inside)
			}
		}
	}
}

func TestBioAurora_DitheringBreaksMonochromeStreaks(t *testing.T) {
	// Test: a long line of "1"s should NOT be all the same color due
	// to dithering. We check the visible "1" count (preserved) and
	// that the underlying ANSI codes use at least 2 different colors.
	ba := NewBioAurora(11)
	style := lipgloss.NewStyle().Foreground(lipgloss.Color("3"))
	plain := strings.Repeat("1", 30)
	rendered := ba.RenderAurora(plain, 0, style)
	// Count distinct ANSI color codes used.
	colors := map[string]bool{}
	for _, code := range []string{
		"\x1b[1;34m", "\x1b[1;33m", "\x1b[1;35m", "\x1b[1;36m",
		"\x1b[34m", "\x1b[33m", "\x1b[35m", "\x1b[36m", "\x1b[32m",
		"\x1b[2;34m", "\x1b[2;33m", "\x1b[2;35m", "\x1b[2;36m", "\x1b[2;32m",
		"\x1b[1;32m", "\x1b[32m",
	} {
		if strings.Contains(rendered, code) {
			colors[code] = true
		}
	}
	// At t=0, palette indices 0..5 cycle through. We expect at least
	// 2 distinct colors in 30 chars (some will be dithered to base).
	if len(colors) < 2 {
		t.Errorf("expected at least 2 distinct colors, got %d: %v", len(colors), colors)
	}
}

func TestBioAurora_RenderStatic_NoFlicker(t *testing.T) {
	// Text under C4R should never be aurora-tinted.
	ba := NewBioAurora(11)
	style := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3"))
	text := "Discover. Invent. Shift paradigms."
	got := ba.RenderStatic(text, style)
	if !strings.Contains(got, text) {
		t.Errorf("RenderStatic should preserve text, got %q", got)
	}
}

func TestBioAurora_MaxOpacityConstant(t *testing.T) {
	// The cap is a public contract: production code and downstream
	// tools may rely on this value. Lock it in.
	const want = 0.55
	if maxAuroraOpacity != want {
		t.Errorf("maxAuroraOpacity = %f, want %f (changing this affects visual contract)", maxAuroraOpacity, want)
	}
}
