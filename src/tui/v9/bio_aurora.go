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
//
// v9.11.2 changes:
//   - Max opacity reduced from 1.0 → 0.55 so aurora never paints over
//     the C4R art, only tints it
//   - Per-rune dithering pattern prevents long monochrome streaks that
//     looked like a broken display
//   - Horizontal energy band y-range restricted to avoid covering C4R
//     text (Y rows where C4R lives are skipped)
//   - Color jumps damped: norm rescaled with tanh for soft saturation
type BioAurora struct {
	startTime float64 // seconds since splash started
	artRows   int     // number of rows occupied by art (skip these)
}

// NewBioAurora creates a fresh bio-aurora.
// artRows is the number of rows occupied by C4R art (used to skip
// the most-intense color modulation in that region so the letters
// stay readable).
func NewBioAurora(artRows int) *BioAurora {
	if artRows < 0 {
		artRows = 0
	}
	return &BioAurora{startTime: 0, artRows: artRows}
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

// maxAuroraOpacity caps how strong the aurora tint can be. v9.11.1
// painted at full intensity which hid the C4R glyphs behind solid
// colored blocks. 0.55 keeps the art readable while still showing
// the wave morphing.
const maxAuroraOpacity = 0.55

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
	// Dampen the horizontal energy band: in v9.11.1 this created long
	// monochrome streaks across the entire row. We now restrict its
	// Y range to rows OUTSIDE the C4R art region, and reduce amplitude.
	if y < ba.artRows {
		// Inside C4R art: use a tiny per-cell dither, no big band.
		// This keeps letters readable but adds subtle color flicker.
		v += w1 * 0.15
	} else {
		// Outside C4R: full horizontal energy band can roam freely.
		band := math.Sin(t*2*math.Pi/12.5 - float64(x)*0.15)
		v += band * 0.3
	}
	// Vertical pulse: top brighter, bottom dimmer (or vice versa)
	pulse := math.Sin(t*2*math.Pi/7.0)
	v += pulse * 0.2
	// Soft saturation: tanh compresses the extremes so colour transitions
	// feel smoother and avoid the "snap from green to yellow" jumps that
	// the integer palette index would otherwise produce.
	norm := (math.Tanh(v) + 1.0) / 2.0 // 0..1, smooth
	idx := int(norm * float64(len(auroraPalette)))
	if idx >= len(auroraPalette) {
		idx = len(auroraPalette) - 1
	}
	if idx < 0 {
		idx = 0
	}
	return idx
}

// intensityAt returns 0-maxAuroraOpacity intensity for cell (x, y) at time t.
// Capped at maxAuroraOpacity so the aurora never paints a fully solid
// color over the art. Inside the C4R art region, intensity is further
// capped at 0.30 to keep letters readable.
func (ba *BioAurora) intensityAt(x, y int) float64 {
	t := ba.startTime
	b1 := math.Sin(t*2*math.Pi/5.2 + float64(x)*0.1 + float64(y)*0.15)
	b2 := math.Sin(t*2*math.Pi/3.8 - float64(x)*0.05)
	// 0.2..1.0 range, then capped at maxAuroraOpacity
	intensity := 0.4 + 0.4*(b1+b2)/2 + 0.2
	cap := maxAuroraOpacity
	if ba.isInArtRegion(y) {
		cap = 0.30 // softer inside C4R art
	}
	if intensity > cap {
		intensity = cap
	}
	if intensity < 0.15 {
		intensity = 0.15
	}
	return intensity
}

// isInArtRegion reports whether (x, y) is inside the C4R art region.
// Cells in the art region get a dampened aurora (low opacity, dither)
// so the letters stay readable.
func (ba *BioAurora) isInArtRegion(y int) bool {
	return ba.artRows > 0 && y < ba.artRows
}

// RenderAurora applies the bio-aurora color modulation to a line of art.
// Each rune is re-colored using the palette at (x, y) where x is rune
// position. Spaces and empty runes are left untouched.
//
// In v9.11.2 the aurora is much softer: max opacity 0.55, with a
// per-rune dither pattern that prevents long monochrome streaks.
// Cells inside the art region get a subtler treatment (max 0.30) to
// keep the C4R letters readable.
func (ba *BioAurora) RenderAurora(plain string, y int, baseStyle lipgloss.Style) string {
	if ba == nil || plain == "" {
		return baseStyle.Render(plain)
	}
	runes := []rune(plain)
	var sb strings.Builder
	// Per-row dither: skip every Nth rune's color swap based on y, so
	// even if the wave says "all green for the next 20 cells", only
	// ~60% actually paint, breaking up the long streaks.
	ditherSkip := y % 3
	for i, r := range runes {
		if r == ' ' {
			sb.WriteRune(' ')
			continue
		}
		if r < 32 {
			sb.WriteRune(r)
			continue
		}
		// Apply dither: skip a fraction of cells entirely.
		if (i+ditherSkip)%5 == 0 {
			// Use base style (no aurora tint) for these cells.
			sb.WriteString(baseStyle.Render(string(r)))
			continue
		}
		idx := ba.colorAt(i, y)
		intensity := ba.intensityAt(i, y)
		// Inside art region: cap intensity to 0.30 so letters stay
		// readable. Outside art region: full maxAuroraOpacity.
		if ba.isInArtRegion(y) && intensity > 0.30 {
			intensity = 0.30
		}
		style := lipgloss.NewStyle().Foreground(lipgloss.Color(auroraPalette[idx]))
		// Use bold sparingly — only in the brightest cells, and only
		// outside the art region (bold inside art would make glyphs
		// wider and overlap each other).
		if intensity > maxAuroraOpacity*0.85 && !ba.isInArtRegion(y) {
			style = style.Bold(true)
		}
		// Apply intensity as foreground alpha approximation: dimmer
		// cells use a muted palette colour. Lipgloss v2 doesn't expose
		// per-cell alpha, so we use Faint() for low intensity, normal
		// otherwise.
		if intensity < 0.25 {
			style = style.Faint(true)
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
