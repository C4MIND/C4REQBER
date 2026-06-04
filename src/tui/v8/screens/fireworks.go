package screens

import (
	"math"
	"math/rand"
	"time"

	tea "github.com/charmbracelet/bubbletea"
)

// Fireworks shows a brief celebration overlay when quality > 80.
type Fireworks struct {
	width     int
	height    int
	particles []particle
	tick      int
	done      bool
}

type particle struct {
	x, y    float64
	vx, vy  float64
	life    int
	maxLife int
	color   string
	char    rune
}

var fireworkColors = []string{"#FF6B6B", "#FFD93D", "#4ECDC4", "#ec4899", "#8b5cf6", "#4ADE80", "#f97316"}
var fireworkChars = []rune{'*', '+', '·', '◆', '○', '✦'}

// NewFireworks creates a celebration overlay.
func NewFireworks() Fireworks {
	return Fireworks{}
}

func (f Fireworks) Title() string { return "Fireworks" }
func (f Fireworks) Done() bool    { return f.done }

func (f Fireworks) Init() tea.Cmd {
	return tea.Batch(
		tea.Tick(80*time.Millisecond, func(t time.Time) tea.Msg { return fwTickMsg{} }),
		tea.Tick(3*time.Second, func(t time.Time) tea.Msg { return fwDoneMsg{} }),
	)
}

func (f Fireworks) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		f.width = msg.Width
		f.height = msg.Height
		f.spawnBursts()
		return f, nil
	case fwTickMsg:
		if f.done {
			return f, nil
		}
		f.tick++
		f.updateParticles()
		if f.tick%8 == 0 {
			f.spawnBurst()
		}
		return f, tea.Tick(80*time.Millisecond, func(t time.Time) tea.Msg { return fwTickMsg{} })
	case fwDoneMsg:
		f.done = true
		return f, nil
	}
	return f, nil
}

func (f *Fireworks) spawnBursts() {
	for i := 0; i < 5; i++ {
		f.spawnBurst()
	}
}

func (f *Fireworks) spawnBurst() {
	if f.width <= 4 || f.height <= 4 {
		return
	}
	cx := float64(rand.Intn(f.width-4) + 2)
	cy := float64(rand.Intn(f.height/2) + 2)
	color := fireworkColors[rand.Intn(len(fireworkColors))]
	count := 12 + rand.Intn(12)
	for i := 0; i < count; i++ {
		angle := (2 * math.Pi * float64(i)) / float64(count)
		speed := 0.5 + rand.Float64()*1.5
		f.particles = append(f.particles, particle{
			x: cx, y: cy,
			vx:      math.Cos(angle) * speed,
			vy:      math.Sin(angle) * speed,
			life:    20 + rand.Intn(15),
			maxLife: 35,
			color:   color,
			char:    fireworkChars[rand.Intn(len(fireworkChars))],
		})
	}
}

func (f *Fireworks) updateParticles() {
	if len(f.particles) == 0 {
		return
	}
	alive := make([]particle, 0, len(f.particles))
	for _, p := range f.particles {
		p.x += p.vx
		p.y += p.vy
		p.vy += 0.05 // gravity
		p.life--
		if p.life > 0 {
			alive = append(alive, p)
		}
	}
	f.particles = alive
}

func (f Fireworks) View() string {
	if f.width == 0 {
		return ""
	}

	// Pre-allocate a flat buffer: each row is width runes + 1 newline
	// Guard against absurd terminal sizes to prevent int overflow.
	if f.width <= 0 || f.height <= 0 || f.width > 1000 || f.height > 1000 {
		return ""
	}
	buf := make([]rune, 0, f.height*(f.width+1))

	// Build rows directly
	for y := 0; y < f.height; y++ {
		row := make([]rune, f.width)
		for x := range row {
			row[x] = ' '
		}
		// Place particles
		for _, p := range f.particles {
			if int(p.y) == y && int(p.x) >= 0 && int(p.x) < f.width {
				alpha := float64(p.life) / float64(p.maxLife)
				if alpha > 0.7 {
					row[int(p.x)] = p.char
				} else if alpha > 0.3 {
					row[int(p.x)] = '·'
				}
			}
		}
		buf = append(buf, row...)
		if y < f.height-1 {
			buf = append(buf, '\n')
		}
	}

	return string(buf)
}

type fwTickMsg struct{}
type fwDoneMsg struct{}
