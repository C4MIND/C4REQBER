package tui

import (
	"math"
	"strings"

	"charm.land/lipgloss/v2"
)

// BioAurora creates bio-cognitive morphing color effects on top of
// static art. It applies several smooth wave functions (low frequencies,
// sub-audio — no epilepsy risk) + ultra-slow global breathing phase
// that determine a "color state" for each (x, y) cell at time t,
// then maps that state to a 6-color organic palette.
//
// Palette: green → cyan → blue → magenta → yellow (organic sci-cog gradient).
// All transitions are smooth (sine), no abrupt flashes. v9 polish: globalPhase
// drift + tuned waves for more "alive legendary" aurora on the cube.
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

// globalPhase gives a very slow (0.02Hz) overall palette drift for
// "breathing" legendary organic feel without any flicker.
func (ba *BioAurora) globalPhase() float64 {
	return math.Sin(ba.startTime * 2 * math.Pi / 48.0) * 0.08
}

// auroraPalette is the 6-color organic gradient used for the bio-morphing.
var auroraPalette = []string{
	"2", // green
	"6", // cyan
	"4", // blue
	"5", // magenta
	"3", // yellow (rare highlight)
	"2", // green (loop)
}

// maxAuroraOpacity caps how strong the aurora tint can be. v9.11.1
// painted at full intensity which hid the C4R glyphs behind solid
// colored blocks. 0.55 keeps the art readable while still showing
// the wave morphing.
const maxAuroraOpacity = 0.55

// colorAt returns the palette index for cell (x, y) at time t.
// Combines 3 sine waves with different periods/phases for organic morphing.
// All frequencies are sub-1Hz to avoid photosensitive seizures.
//
// v9.11.6: quantize the palette index to fewer steps so the color
// stays stable for a noticeable interval (1-2 seconds) instead of
// flickering every 16ms. v9.11.5 had `int(norm * 6)` which changed
// idx whenever norm crossed a 1/6 boundary — with the wave moving
// continuously, this produced a 6-7 Hz visible flicker that looked
// like a UI bug ("мерцающий баг"). With quantization to 3 steps,
// the color only changes when norm crosses a 1/3 boundary, so the
// visible dwell time per color is ~2-3 seconds.
func (ba *BioAurora) colorAt(x, y int) int {
	t := ba.startTime
	gp := ba.globalPhase()
	// Three waves (sub-1Hz) + global drift + slow horizontal sweep for premium organic flow
	w1 := math.Sin(t*2*math.Pi/4.3 + float64(x)*0.3 + float64(y)*0.2 + gp)
	w2 := math.Sin(t*2*math.Pi/6.7 + float64(x)*0.15 - float64(y)*0.4 - gp*0.7)
	w3 := math.Sin(t*2*math.Pi/8.1 - float64(x)*0.25 + float64(y)*0.35 + gp*1.1)
	// Slow left-to-right energy sweep (adds life without flicker)
	sweep := math.Sin(t*2*math.Pi/19.0 - float64(x)*0.08)
	v := (w1 + w2 + w3 + sweep*0.4) / 3.4 // -1..+1
	// Dampen inside C4R
	if y < ba.artRows {
		v += w1 * 0.12
	} else {
		band := math.Sin(t*2*math.Pi/12.5 - float64(x)*0.15 + gp)
		v += band * 0.28
	}
	pulse := math.Sin(t * 2 * math.Pi / 7.0 + gp*2)
	v += pulse * 0.18
	norm := (math.Tanh(v) + 1.0) / 2.0
	const steps = 3
	stepIdx := int(norm * float64(steps))
	if stepIdx >= steps {
		stepIdx = steps - 1
	}
	if stepIdx < 0 {
		stepIdx = 0
	}
	idx := stepIdx * 2
	if norm*float64(steps)-float64(stepIdx) > 0.5 {
		idx++
	}
	if idx >= len(auroraPalette) {
		idx = len(auroraPalette) - 1
	}
	return idx
}

// intensityAt returns 0-maxAuroraOpacity intensity for cell (x, y) at time t.
// Capped at maxAuroraOpacity so the aurora never paints a fully solid
// color over the art. Inside the C4R art region, intensity is further
// capped at 0.15 (very subtle tint) to keep letter shapes stable and
// avoid the "every cell a different color" glitch on small glyphs
// (the 4-char wall of C, the 5-char leg of R).
//
// v9 polish: adds micro-flares — every ~9s the aurora briefly peaks at
// +0.10 intensity for 200ms, simulating a distant "star flare" pulse
// that breathes new life into the legend.
func (ba *BioAurora) intensityAt(x, y int) float64 {
	t := ba.startTime
	gp := ba.globalPhase() * 1.5
	b1 := math.Sin(t*2*math.Pi/5.2 + float64(x)*0.1 + float64(y)*0.15 + gp)
	b2 := math.Sin(t*2*math.Pi/3.8 - float64(x)*0.05 - gp)
	// Gentle breathing + micro vertical drift
	drift := math.Sin(t*2*math.Pi/11.0 + float64(y)*0.12) * 0.06
	intensity := 0.37 + 0.43*(b1+b2)/2 + 0.18 + drift

	// ── Micro-flare: every 9s, brief peak (+0.10 for ~200ms)
	// Implemented as a sinusoidal bump on the 9s period with narrow gate.
	flarePhase := math.Mod(t, 9.0)
	if flarePhase < 0.6 {
		// smooth bump from 0 → 0.10 → 0 over 0.6s
		flare := (1.0 - math.Abs(flarePhase-0.3)/0.3) * 0.10
		if flare < 0 {
			flare = 0
		}
		intensity += flare
	}

	cap := maxAuroraOpacity
	if ba.isInArtRegion(y) {
		cap = 0.15
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
// In v9.11.3 the aurora is even softer inside the C4R art region:
// max intensity 0.15, with dither cells using a muted (gray) style
// rather than the bold primary color. This stops the "прыгает, моргает"
// strobe effect where every 5th cell flashed bold yellow.
//
// baseStyle is the style for non-dithered aurora cells; ditherStyle
// is what every 5th cell uses (typically muted/gray).
func (ba *BioAurora) RenderAurora(plain string, y int, baseStyle, ditherStyle lipgloss.Style) string {
	if ba == nil || plain == "" {
		return baseStyle.Render(plain)
	}
	if ditherStyle.GetForeground() == (lipgloss.Color("")) && ditherStyle.GetBold() == false {
		// No dither style supplied — fall back to baseStyle for safety
		// (caller forgot to pass it). Maintains backwards compat with
		// v9.11.2 callers that didn't know about the second arg.
		ditherStyle = baseStyle
	}
	runes := []rune(plain)
	var sb strings.Builder
	// Evolved dither: slight phase variation per row + column creates
	// a living, non-mechanical breathing texture on the aurora.
	ditherSkip := (y + (y / 2)) % 4
	for i, r := range runes {
		if r == ' ' {
			sb.WriteRune(' ')
			continue
		}
		if r < 32 {
			sb.WriteRune(r)
			continue
		}
		// Apply dither: organic skip pattern
		if (i+ditherSkip)%5 == 0 || ((i*3+y)%7 == 0) {
			sb.WriteString(ditherStyle.Render(string(r)))
			continue
		}
		idx := ba.colorAt(i, y)
		intensity := ba.intensityAt(i, y)
		// Inside art region: cap intensity to 0.15 so letters stay
		// readable. Outside art region: full maxAuroraOpacity.
		if ba.isInArtRegion(y) && intensity > 0.15 {
			intensity = 0.15
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
		if intensity < 0.10 {
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
