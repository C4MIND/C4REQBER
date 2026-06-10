package tui

import (
	"math/rand"

	"charm.land/lipgloss/v2"
	"github.com/charmbracelet/harmonica"
)

// Particle for burst effect on discovery complete.
type particle struct {
	x, y     float64
	vx, vy   float64
	life     float64
	maxLife  float64
	colorIdx int
}

const burstGravity = 0.15

// Burst runs a 2.5s particle explosion. Each Tick() advances physics.
// Particles emit from a center point, fly outward, fall under gravity, fade.
type Burst struct {
	active   bool
	tick     int
	parts    []particle
	cx, cy   int
	centerX  float64
	centerY  float64
	width    int
	height   int
}

var burstColors = []string{"203", "207", "227", "51", "39", "213"}

func NewBurst() *Burst {
	return &Burst{}
}

func (b *Burst) Trigger(width, height, cx, cy int) {
	b.active = true
	b.tick = 0
	b.width = width
	b.height = height
	b.cx = cx
	b.cy = cy
	b.centerX = float64(cx)
	b.centerY = float64(cy)
	b.parts = make([]particle, 50)
	for i := range b.parts {
		angle := rand.Float64() * 6.283
		speed := 1.5 + rand.Float64()*3.5
		life := 1.8 + rand.Float64()*1.2
		b.parts[i] = particle{
			x:        b.centerX,
			y:        b.centerY,
			vx:       float64(speed) * cosApprox(angle),
			vy:       float64(speed) * sinApprox(angle),
			life:     life,
			maxLife:  life,
			colorIdx: rand.Intn(len(burstColors)),
		}
	}
}

func (b *Burst) Tick() {
	if !b.active {
		return
	}
	b.tick++
	for i := range b.parts {
		p := &b.parts[i]
		p.x += p.vx
		p.y += p.vy
		p.vy += burstGravity
		p.life -= 0.05
	}
	alive := 0
	for _, p := range b.parts {
		if p.life > 0 && p.y < float64(b.height) {
			alive++
		}
	}
	if alive == 0 {
		b.active = false
	}
}

func (b *Burst) Render() string {
	if !b.active {
		return ""
	}
	grid := make([][]rune, b.height)
	for i := range grid {
		grid[i] = make([]rune, b.width)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}
	for _, p := range b.parts {
		if p.life <= 0 {
			continue
		}
		x, y := int(p.x), int(p.y)
		if x < 0 || x >= b.width || y < 0 || y >= b.height {
			continue
		}
		syms := []rune{'·', '•', '○', '◦', '●'}
		grid[y][x] = syms[min(p.colorIdx, len(syms)-1)]
	}
	var out []string
	for _, row := range grid {
		var line string
		for _, ch := range row {
			if ch == ' ' {
				line += " "
				continue
			}
			fade := 0
			if p := b.parts[0]; p.life < p.maxLife/2 {
				fade = 1
			}
			color := burstColors[min(fade, len(burstColors)-1)]
			line += lipgloss.NewStyle().Foreground(lipgloss.Color(color)).Render(string(ch))
		}
		out = append(out, line)
	}
	return joinLines(out)
}

func (b *Burst) Active() bool { return b.active }

// SlideIn drives smooth card-spawn animation via Harmonica spring.
type SlideIn struct {
	spring    harmonica.Spring
	pos, vel  float64
	active    bool
	age       int
	startTick int
}

func NewSlideIn() *SlideIn {
	return &SlideIn{
		spring: harmonica.NewSpring(harmonica.FPS(60), 7.0, 0.7),
	}
}

func (s *SlideIn) Trigger(now int) {
	s.active = true
	s.age = 0
	s.pos = 30 // start 30 cells to the right
	s.vel = 0
	s.startTick = now
}

func (s *SlideIn) Tick() {
	if !s.active {
		return
	}
	s.age++
	s.pos, s.vel = s.spring.Update(s.pos, s.vel, 0)
	if abs(s.pos) < 0.5 {
		s.pos = 0
		s.active = false
	}
}

func (s *SlideIn) Offset() float64 { return s.pos }
func (s *SlideIn) Active() bool   { return s.active }

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Cheap cos/sin using Taylor (avoid importing math for hot path).
func cosApprox(theta float64) float64 {
	theta = theta - floor(theta/6.2832)*6.2832
	return 1 - theta*theta/2 + theta*theta*theta*theta/24
}

func sinApprox(theta float64) float64 {
	theta = theta - floor(theta/6.2832)*6.2832
	return theta - theta*theta*theta/6 + theta*theta*theta*theta*theta/120
}

func floor(x float64) float64 {
	return float64(int64(x))
}
