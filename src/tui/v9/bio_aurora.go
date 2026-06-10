package tui

import (
	"math"
	"strings"

	"charm.land/lipgloss/v2"
)

// BioAurora creates bio-cognitive morphing color effects on top of
// static art. It applies several smooth wave functions (low frequencies,
// sub-audio — no epilepsy risk) that determine a "color state" for each
// (x, y) cell at time t, then maps that state to a 6-color organic palette.
//
// Palette: green → cyan → blue → magenta → red (organic sci-cog gradient).
// All transitions are smooth (sine), no abrupt flashes.
type BioAurora struct {
	startTime float64 // seconds since splash started
}

// NewBioAurora creates a fresh bio-aurora.
func NewBioAurora() *BioAurora {
	return &BioAurora{startTime: 0}
}

// Tick advances the aurora animation clock.
func (ba *BioAurora) Tick(elapsedSec float64) {
	ba.startTime = elapsedSec
}

// auroraPalette is the 6-color organic gradient used for the bio-morphing.
var auroraPalette = []string{
	"2",  // green
	"6",  // cyan
	"4",  // blue
	"5",  // magenta
	"3",  // yellow (rare highlight)
	"2",  // green (loop)
}

// colorAt returns the palette index for cell (x, y) at time t.
// Combines 3 sine waves with different periods/phases for organic morphing.
// All frequencies are sub-1Hz to avoid photosensitive seizures.
func (ba *BioAurora) colorAt(x, y int) int {
	t := ba.startTime
	// Three waves with periods 4.3s, 6.7s, 8.1s (all sub-1Hz)
	w1 := math.Sin(t*2*math.Pi/4.3 + float64(x)*0.3 + float64(y)*0.2)
	w2 := math.Sin(t*2*math.Pi/6.7 + float64(x)*0.15 - float64(y)*0.4)
	w3 := math.Sin(t*2*math.Pi/8.1 - float64(x)*0.25 + float64(y)*0.35)
	// Combine: average + offsets for shifting bands
	v := (w1 + w2 + w3) / 3.0 // -1..+1
	// Add a slow horizontal "energy band" that travels left→right
	band := math.Sin(t*2*math.Pi/12.5 - float64(x)*0.15)
	v += band * 0.3
	// Add a vertical pulse: top brighter, bottom dimmer (or vice versa periodically)
	pulse := math.Sin(t*2*math.Pi/7.0)
	v += pulse * 0.2
	// Normalize to 0..1
	norm := (v + 2.0) / 4.0 // 0..1
	if norm < 0 {
		norm = 0
	}
	if norm > 1 {
		norm = 1
	}
	// Map to palette index
	idx := int(norm * float64(len(auroraPalette)))
	if idx >= len(auroraPalette) {
		idx = len(auroraPalette) - 1
	}
	return idx
}

// intensityAt returns 0-1 intensity for cell (x, y) at time t.
// Slow modulation: brighter in wave crests, dimmer in troughs.
func (ba *BioAurora) intensityAt(x, y int) float64 {
	t := ba.startTime
	// Slow brightness wave (period 5.2s, sub-1Hz)
	b1 := math.Sin(t*2*math.Pi/5.2 + float64(x)*0.1 + float64(y)*0.15)
	// Pulse synchronized with bio-aurora color shifts
	b2 := math.Sin(t*2*math.Pi/3.8 - float64(x)*0.05)
	intensity := 0.4 + 0.4*(b1+b2)/2 + 0.2
	if intensity < 0.2 {
		intensity = 0.2
	}
	if intensity > 1.0 {
		intensity = 1.0
	}
	return intensity
}

// RenderAurora applies the bio-aurora color modulation to a line of art
// (or text — but text is handled separately to keep it static).
// Each rune is re-colored using the palette at (x, y) where x is rune position.
// Spaces and empty runes are left untouched.
func (ba *BioAurora) RenderAurora(plain string, y int, baseStyle lipgloss.Style) string {
	if ba == nil || plain == "" {
		return baseStyle.Render(plain)
	}
	runes := []rune(plain)
	var sb strings.Builder
	for i, r := range runes {
		if r == ' ' {
			sb.WriteRune(' ')
			continue
		}
		// Skip very-low chars (rendered as-is)
		if r < 32 {
			sb.WriteRune(r)
			continue
		}
		idx := ba.colorAt(i, y)
		intensity := ba.intensityAt(i, y)
		// Pick color from palette
		style := lipgloss.NewStyle().Foreground(lipgloss.Color(auroraPalette[idx]))
		// For dimmed cells, use a muted shade (style with dim)
		if intensity < 0.4 {
			style = style.Faint(true)
		} else if intensity < 0.7 {
			style = style.Foreground(lipgloss.Color(auroraPalette[idx]))
		} else {
			style = style.Bold(true)
		}
		sb.WriteString(style.Render(string(r)))
	}
	return sb.String()
}

// RenderStatic returns a plain baseStyle-rendered line (no aurora).
// Used for text blocks (we don't want text to flicker).
func (ba *BioAurora) RenderStatic(text string, baseStyle lipgloss.Style) string {
	return baseStyle.Render(text)
}
