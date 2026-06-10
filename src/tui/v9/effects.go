package tui

import (
	"math/rand"
	"strings"

	tea "charm.land/bubbletea/v2"
)

// Typewriter char-by-char reveal for hypothesis text.
// RevealSpeed = chars per tick (1 = slow, 3 = readable).
type Typewriter struct {
	target   string
	current  int
	speed    int
	active   bool
	done     bool
	lastTick int
}

func NewTypewriter() *Typewriter {
	return &Typewriter{speed: 2}
}

func (t *Typewriter) Set(text string, nowTick int) {
	t.target = text
	t.current = 0
	t.active = true
	t.done = false
	t.lastTick = nowTick
}

func (t *Typewriter) Tick(nowTick int) {
	if !t.active || t.done {
		return
	}
	delta := nowTick - t.lastTick
	if delta < 2 { // reveal every 2 ticks (~33ms at 60fps)
		return
	}
	t.lastTick = nowTick
	t.current += t.speed
	if t.current >= len(t.target) {
		t.current = len(t.target)
		t.done = true
		t.active = false
	}
}

func (t *Typewriter) View() string {
	if !t.active && !t.done {
		return ""
	}
	return t.target[:t.current]
}

func (t *Typewriter) Active() bool { return t.active }

// Sparks for cursor on keypress — small particles in input area.
type Spark struct {
	x, y    int
	vx, vy  float64
	life    float64
	symIdx  int
}

const sparkSyms = "·•◦●"

type Sparkles struct {
	active    bool
	sparks    []Spark
	width     int
	height    int
}

func NewSparkles() *Sparkles {
	return &Sparkles{}
}

func (s *Sparkles) SetSize(w, h int) {
	s.width = w
	s.height = h
}

func (s *Sparkles) Emit(cx, cy int, n int) {
	if s.width == 0 {
		return
	}
	s.active = true
	for i := 0; i < n; i++ {
		s.sparks = append(s.sparks, Spark{
			x:      cx,
			y:      cy,
			vx:     (rand.Float64() - 0.5) * 1.5,
			vy:     -(0.5 + rand.Float64()*1.0),
			life:   0.6 + rand.Float64()*0.4,
			symIdx: rand.Intn(len(sparkSyms)),
		})
	}
	if len(s.sparks) > 200 {
		s.sparks = s.sparks[len(s.sparks)-200:]
	}
}

func (s *Sparkles) Tick() {
	if !s.active {
		return
	}
	gravity := 0.05
	alive := s.sparks[:0]
	for i := range s.sparks {
		sp := &s.sparks[i]
		sp.x += int(sp.vx)
		sp.y += int(sp.vy)
		sp.vy += gravity
		sp.life -= 0.04
		if sp.life > 0 && sp.x >= 0 && sp.x < s.width && sp.y >= 0 && sp.y < s.height {
			alive = append(alive, *sp)
		}
	}
	s.sparks = alive
	if len(s.sparks) == 0 {
		s.active = false
	}
}

func (s *Sparkles) Render() string {
	if !s.active {
		return ""
	}
	lines := make([]string, s.height)
	for i := range lines {
		lines[i] = strings.Repeat(" ", s.width)
	}
	for _, sp := range s.sparks {
		if sp.x < 0 || sp.x >= s.width || sp.y < 0 || sp.y >= s.height {
			continue
		}
		sym := string(sparkSyms[sp.symIdx%len(sparkSyms)])
		row := lines[sp.y]
		lines[sp.y] = row[:sp.x] + sym + row[sp.x+1:]
	}
	return joinLines(lines)
}

func (s *Sparkles) Active() bool { return s.active }

var _ = tea.KeyPressMsg{} // keep import
