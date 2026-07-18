package tui

import (
	"fmt"
	"time"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// DreamState — ambient idle mode shown after N seconds of no activity.
// Shows rotating ASCII art + thinking quotes. Disappears on any keypress.
type DreamState struct {
	active      bool
	startedAt   time.Time
	idleSeconds int
	currentArt  int
	lastArtTick time.Time
	frame       int
	paused      bool
}

// 5 ambient dream arts (ASCII) — small enough to fit in 60×20 viewport.
var dreamArts = []string{
	// Wave
	`∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪
∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪
∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪∪
~~~~~~~~~~~~~~~~~~~~~~~~~~`,
	// Stargazing
	`·    .  ·    .    . ·  ✦
    .        ·  ·    .  ·
 .    .  ·     .  ·    .
  .    .  . ·    .  ·  ·
.   .  ✦  ·  .    .  · .
    .    .  ·   .  ✦  ·  `,
	// Spinning cube
	`   ╱╲
  ╱  ╲
 ╱ 27 ╲
╲states╱
 ╲    ╱
  ╲  ╱
   ╲╱`,
	// Equation
	`Z₃³ × 6 operators
= 27 states
  6 forward
  6 inverse
  3 identity
  ─────────
  27 unique cells`,
	// Particles
	`   ·  ·     ·  ·
 ·     ·  ✦    ·   ·
  ·  ·   ·   ·  ·
 ·   ·    · ·   ·  ·
  ·  ·  ·   ·   ·
·    ·    ·  ✦   ·  `,
}

// Dream quotes — 12 short musings about science, discovery, idle thought.
var dreamQuotes = []string{
	"What if a solution lives in a state we haven't explored yet?",
	"Z₃³. 27 cells. The undirected graph has diameter 3. Directed forward is 6.",
	"The cube breathes even when you don't.",
	"Some discoveries need silence to surface.",
	"6 operators. 27 states. Infinite paths through them.",
	"Wait 5 minutes. The next breakthrough often arrives uninvited.",
	"Verification ≠ proof. Proof ≠ understanding.",
	"An idle mind is the universe's favorite research tool.",
	"Quality × novelty × cost = discovery index.",
	"Time is the only non-renewable resource in any pipeline.",
	"Three constraints make a problem. Two make a wish.",
	"Difference between discovery and invention: one finds, the other makes.",
}

// NewDreamState creates a new dream state.
func NewDreamState() *DreamState {
	return &DreamState{
		active:      false,
		idleSeconds: 300, // 5 minutes
		currentArt:  0,
		frame:       0,
	}
}

// Reset clears the idle timer.
func (d *DreamState) Reset() {
	d.active = false
	d.startedAt = time.Time{}
}

// Touch is called on any user activity — resets the idle counter.
func (d *DreamState) Touch() {
	if d.active {
		d.Reset()
	}
}

// Tick advances dream animation. Activates after idleSeconds of no touches.
// Returns true if state changed.
func (d *DreamState) Tick() bool {
	now := time.Now()
	if d.startedAt.IsZero() {
		d.startedAt = now
	}
	idle := now.Sub(d.startedAt)
	wasActive := d.active
	// idleSeconds <= 0 means dream mode is disabled (C4_DREAM_IDLE=0 per
	// config docs). Previously this evaluated to idle > 0, permanently
	// activating dream mode — which buried the live UI during recordings.
	d.active = d.idleSeconds > 0 && idle > time.Duration(d.idleSeconds)*time.Second
	if !d.active {
		return wasActive // maybe transitioned to inactive
	}
	// Rotate art every 10s, advance frame every 0.5s
	if now.Sub(d.lastArtTick) > 10*time.Second {
		d.currentArt = (d.currentArt + 1) % len(dreamArts)
		d.lastArtTick = now
	}
	if int(idle.Seconds()*2) != d.frame {
		d.frame = int(idle.Seconds() * 2)
		return true
	}
	return false
}

// Render produces the dream overlay (returns empty if not active).
func (d *DreamState) Render(width, height int) string {
	if !d.active {
		return ""
	}
	style := lipgloss.NewStyle().
		Width(width).
		Height(height).
		Align(lipgloss.Center, lipgloss.Center).
		Foreground(lipgloss.Color("5"))
	art := dreamArts[d.currentArt]
	quote := dreamQuotes[d.frame%len(dreamQuotes)]
	title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3")).Render("✨ DREAM MODE")
	hint := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(
		i18n.T("dream.hint"))
	idle := time.Since(d.startedAt).Round(time.Second)
	idleStr := lipgloss.NewStyle().Foreground(lipgloss.Color("6")).Render(
		fmt.Sprintf("%s %s", i18n.T("dream.idle"), idle))
	body := fmt.Sprintf("%s\n\n%s\n\n%s\n\n%s\n\n%s", title, art, quote, idleStr, hint)
	return style.Render(body)
}

// Active returns whether dream mode is currently shown.
func (d *DreamState) Active() bool {
	return d.active
}

// Pause/Resume — useful for tests.
func (d *DreamState) Pause()       { d.paused = true }
func (d *DreamState) Resume()      { d.paused = false }
func (d *DreamState) Paused() bool { return d.paused }

// ActivateForTest forces dream mode on (used by tests).
func (d *DreamState) ActivateForTest() {
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-time.Hour) // long enough ago
	d.active = true
}

// QuoteForTest exposes dreamQuotes for tests.
func QuoteForTest(i int) string {
	return dreamQuotes[i%len(dreamQuotes)]
}

// ArtForTest exposes dreamArts for tests.
func ArtForTest(i int) string {
	return dreamArts[i%len(dreamArts)]
}
