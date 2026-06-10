package tui

import (
	"fmt"
	"math/rand"
	"strings"

	"charm.land/lipgloss/v2"
)

// Particle is a floating ASCII sparkle that drifts around the art.
type Particle struct {
	x, y   int
	frame  int
	glyph  string
	style  string
	active bool
}

// ParticleField manages drifting ASCII particles around the cube/C4R.
type ParticleField struct {
	particles []Particle
	rng       *rand.Rand
	maxX, maxY int
}

// NewParticleField creates a new field of ~30 particles within bounds.
func NewParticleField(width, height int) *ParticleField {
	pf := &ParticleField{
		rng:   rand.New(rand.NewSource(0xCAFE)),
		maxX:  width,
		maxY:  height,
	}
	glyphs := []string{"·", ":", "∴", "∴", "·", "·"}
	styles := []string{"5", "6", "8", "3"}
	// Seed 30 particles in upper 2/3 of screen (where art lives)
	for i := 0; i < 30; i++ {
		pf.particles = append(pf.particles, Particle{
			x:      pf.rng.Intn(width),
			y:      pf.rng.Intn(height / 3 * 2),
			frame:  pf.rng.Intn(60),
			glyph:  glyphs[pf.rng.Intn(len(glyphs))],
			style:  styles[pf.rng.Intn(len(styles))],
			active: true,
		})
	}
	return pf
}

// Tick advances particle animation (drift down 1, wrap around).
func (pf *ParticleField) Tick() {
	if pf == nil {
		return
	}
	for i := range pf.particles {
		p := &pf.particles[i]
		p.frame++
		if p.frame%6 == 0 {
			p.y++
			if p.y >= pf.maxY {
				p.y = 0
				p.x = pf.rng.Intn(pf.maxX)
			}
		}
		if p.frame%9 == 0 {
			p.x += pf.rng.Intn(3) - 1 // drift ±1
			if p.x < 0 {
				p.x = 0
			}
			if p.x >= pf.maxX {
				p.x = pf.maxX - 1
			}
		}
	}
}

// ComposeOverlays adds particles to rows that are mostly blank.
// NEVER overwrites non-blank content (i.e. art or text).
func (pf *ParticleField) ComposeOverlays(buffer []string, width int) []string {
	if pf == nil || len(buffer) == 0 {
		return buffer
	}
	out := make([]string, len(buffer))
	copy(out, buffer)
	for _, p := range pf.particles {
		if p.y < 0 || p.y >= len(out) {
			continue
		}
		// Skip if row has visible content (art/text). 0-2 visible chars = safe.
		plain := stripSplashANSI(out[p.y])
		nonSpace := 0
		for _, r := range plain {
			if r != ' ' && r != 0 {
				nonSpace++
				if nonSpace > 2 {
					break
				}
			}
		}
		if nonSpace > 2 {
			continue
		}
		if p.x < 0 || p.x >= width {
			continue
		}
		// Build a clean row with the particle at p.x
		row := make([]rune, width)
		for i := range row {
			row[i] = ' '
		}
		glyphRunes := []rune(p.glyph)
		if len(glyphRunes) > 0 && p.x < width {
			row[p.x] = glyphRunes[0]
		}
		style := lipgloss.NewStyle().Foreground(lipgloss.Color(p.style))
		out[p.y] = style.Render(string(row))
	}
	return out
}

// BloomFrame returns the cube lines with progressive bloom-in
// (frame 0 = no bloom, frame bloomFrames = full cube).
func BloomFrame(artLines []string, frame, total int) []string {
	if total <= 0 {
		return artLines
	}
	t := float64(frame) / float64(total)
	if t >= 1.0 {
		return artLines
	}
	if t < 0 {
		t = 0
	}
	// Bloom-in: cube expands from center outward
	// For each line, reveal chars symmetrically from center
	out := make([]string, len(artLines))
	for i, line := range artLines {
		plain := stripSplashANSI(line)
		plainLen := len([]rune(plain))
		if plainLen == 0 {
			out[i] = line
			continue
		}
		// Distance from center of this line's middle row
		center := plainLen / 2
		// Vertical expansion: how many lines from top should be revealed
		totalLines := len(artLines)
		centerLine := totalLines / 2
		dist := i - centerLine
		if dist < 0 {
			dist = -dist
		}
		// Reveal threshold: at t=0, only center line. At t=1, all lines.
		revealLinesUpTo := int(t * float64(totalLines+1))
		if dist > revealLinesUpTo {
			// Line not yet revealed
			out[i] = strings.Repeat(" ", plainLen)
			continue
		}
		// Within revealed lines, also bloom chars from center outward
		// Character bloom: per-line, reveal radius grows with t
		maxRadius := int(t * float64(plainLen+1))
		newRunes := make([]rune, plainLen)
		for j := 0; j < plainLen; j++ {
			dc := j - center
			if dc < 0 {
				dc = -dc
			}
			if dc <= maxRadius {
				newRunes[j] = []rune(plain)[j]
			} else {
				newRunes[j] = ' '
			}
		}
		out[i] = string(newRunes)
	}
	return out
}

// ShimmerText applies a faint color shimmer to a string.
// frame is the animation frame (0-360 degrees).
func ShimmerText(s string, frame int) string {
	// Apply a faint gradient that moves over time
	colors := []string{"3", "6", "5", "6", "3"} // primary, cyan, magenta, cyan, primary
	idx := (frame / 3) % len(colors)
	style := lipgloss.NewStyle().Foreground(lipgloss.Color(colors[idx]))
	return style.Render(s)
}

// BootingProgress returns a 12-char ASCII progress bar for the crystal phase.
// progress is 0-1.
func BootingProgress(progress float64) string {
	if progress < 0 {
		progress = 0
	}
	if progress > 1 {
		progress = 1
	}
	width := 12
	filled := int(progress * float64(width))
	if filled > width {
		filled = width
	}
	bar := "[" + strings.Repeat("█", filled) + strings.Repeat("░", width-filled) + "]"
	pct := fmt.Sprintf(" %3d%%", int(progress*100))
	return bar + pct
}
