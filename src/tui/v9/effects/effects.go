// Package effects provides game-feel animation primitives for TUI v9:
// matrix rain, particle burst, slide-in, typewriter, sparkles.
package effects

import (
	"math/rand"

	"charm.land/lipgloss/v2"
	"github.com/charmbracelet/harmonica"
)

const (
	rainChars = "ｱｳｴｵｶｷｸｹｺｻｼｽｾ￠￡￢￣￤￨￩￪￫￬￭￮￯￰￱￲￳￴￵￶￷￸￹￺￻�ｱｲｳｴｵabcdefghijklmnopqrstuvwxyz0123456789@#$%&*+-/=<>?^_~"
	rainDim   = "22"
	rainHead  = "42"

	burstGravity = 0.15
	burstColors  = "203 207 227 51 39 213"
)

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func floor(x float64) float64 {
	return float64(int64(x))
}

func cosApprox(theta float64) float64 {
	theta = theta - floor(theta/6.2832)*6.2832
	return 1 - theta*theta/2 + theta*theta*theta*theta/24
}

func sinApprox(theta float64) float64 {
	theta = theta - floor(theta/6.2832)*6.2832
	return theta - theta*theta*theta/6 + theta*theta*theta*theta*theta/120
}

func joinLines(lines []string) string {
	if len(lines) == 0 {
		return ""
	}
	s := lines[0]
	for i := 1; i < len(lines); i++ {
		s += "\n" + lines[i]
	}
	return s
}

// ════════════════════════════════════════════════════════════════
// Matrix Rain
// ════════════════════════════════════════════════════════════════

type Rain struct {
	width, height int
	drops         []int
	speed         int
	tick          int
	chars         []rune
	grid          [][]rune // v9.13: pooled render buffer to avoid 60fps realloc
}

func NewRain() *Rain {
	return &Rain{
		speed: 1,
		chars: []rune(rainChars),
	}
}

func (r *Rain) SetSize(w, h int) {
	r.width = w
	r.height = h
	if r.drops == nil || len(r.drops) < w {
		r.drops = make([]int, w)
		for i := range r.drops {
			r.drops[i] = -1 - rand.Intn(h*2)
		}
	}
}

func (r *Rain) Tick() {
	r.tick++
	if r.tick%2 != 0 {
		return
	}
	for i := range r.drops {
		r.drops[i] += r.speed
		if r.drops[i] > r.height+5 {
			r.drops[i] = -1 - rand.Intn(r.height)
		}
	}
}

func (r *Rain) Render() string {
	if r.width == 0 || r.height == 0 {
		return ""
	}
	// First pass: figure out which columns have any drop on screen.
	// If none, return empty string immediately to avoid allocating
	// a height*width grid every frame.
	anyOnScreen := false
	for x := 0; x < r.width && x < len(r.drops); x++ {
		y := r.drops[x]
		if y >= 0 && y < r.height {
			anyOnScreen = true
			break
		}
	}
	if !anyOnScreen {
		return ""
	}
	// v9.13: per-frame alloc audit. We reuse a pooled grid if its
	// dimensions match; otherwise realloc once. The grid is then
	// filled with the per-cell character (or ' ').
	if r.grid == nil || len(r.grid) != r.height || (len(r.grid) > 0 && len(r.grid[0]) != r.width) {
		r.grid = make([][]rune, r.height)
		for i := range r.grid {
			r.grid[i] = make([]rune, r.width)
		}
	}
	// Reset grid to spaces without re-allocating
	for y := 0; y < r.height; y++ {
		for x := 0; x < r.width; x++ {
			r.grid[y][x] = ' '
		}
	}
	anyOnScreen = false
	for x := 0; x < r.width && x < len(r.drops); x++ {
		y := r.drops[x]
		if y < 0 || y >= r.height {
			continue
		}
		anyOnScreen = true
		r.grid[y][x] = r.chars[rand.Intn(len(r.chars))]
		if y > 0 && y-1 < r.height {
			r.grid[y-1][x] = r.chars[rand.Intn(len(r.chars))]
		}
	}
	if !anyOnScreen {
		return ""
	}
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(rainDim))
	bright := lipgloss.NewStyle().Foreground(lipgloss.Color(rainHead))
	var out []string
	for y, row := range r.grid {
		var line string
		for x, ch := range row {
			if ch == ' ' {
				line += " "
				continue
			}
			if y == r.drops[x] {
				line += bright.Render(string(ch))
			} else {
				line += dimStyle.Render(string(ch))
			}
		}
		out = append(out, line)
	}
	return joinLines(out)
}

// ════════════════════════════════════════════════════════════════
// Particle Burst
// ════════════════════════════════════════════════════════════════

type particle struct {
	x, y     float64
	vx, vy   float64
	life     float64
	maxLife  float64
	colorIdx int
}

type Burst struct {
	active  bool
	tick    int
	parts   []particle
	cx, cy  int
	centerX float64
	centerY float64
	width   int
	height  int
	grid     [][]rune // v9.13: pooled render buffer
}

func NewBurst() *Burst { return &Burst{} }

func (b *Burst) Trigger(width, height, cx, cy int) {
	b.active = true
	b.tick = 0
	b.width = width
	b.height = height
	b.cx = cx
	b.cy = cy
	b.centerX = float64(cx)
	b.centerY = float64(cy)
	colors := splitSpace(burstColors)
	b.parts = make([]particle, 50)
	for i := range b.parts {
		angle := rand.Float64() * 6.283
		speed := 1.5 + rand.Float64()*3.5
		life := 1.8 + rand.Float64()*1.2
		b.parts[i] = particle{
			x:        b.centerX,
			y:        b.centerY,
			vx:       speed * cosApprox(angle),
			vy:       speed * sinApprox(angle),
			life:     life,
			maxLife:  life,
			colorIdx: rand.Intn(len(colors)),
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
	colors := splitSpace(burstColors)
	syms := []rune{'·', '•', '○', '◦', '●'}
	// v9.13: pooled grid (was re-allocating every frame).
	if b.grid == nil || len(b.grid) != b.height || (len(b.grid) > 0 && len(b.grid[0]) != b.width) {
		b.grid = make([][]rune, b.height)
		for i := range b.grid {
			b.grid[i] = make([]rune, b.width)
		}
	}
	// Reset to spaces
	for y := 0; y < b.height; y++ {
		for x := 0; x < b.width; x++ {
			b.grid[y][x] = ' '
		}
	}
	// v9.13: track each cell's particle to compute per-particle fade.
	type cellInfo struct {
		ch     rune
		fade   int    // 0=full color, 1=dim
	}
	infos := make(map[[2]int]cellInfo, len(b.parts))
	for _, p := range b.parts {
		if p.life <= 0 {
			continue
		}
		x, y := int(p.x), int(p.y)
		if x < 0 || x >= b.width || y < 0 || y >= b.height {
			continue
		}
		b.grid[y][x] = syms[minInt(p.colorIdx, len(syms)-1)]
		// Compute fade for THIS particle
		fade := 0
		if p.life < p.maxLife/2 {
			fade = 1
		}
		infos[[2]int{y, x}] = cellInfo{ch: b.grid[y][x], fade: fade}
	}
	var out []string
	for y, row := range b.grid {
		var line string
		for x, ch := range row {
			if ch == ' ' {
				line += " "
				continue
			}
			info, ok := infos[[2]int{y, x}]
			if !ok {
				// Default to first color if no info
				line += lipgloss.NewStyle().Foreground(lipgloss.Color(colors[0])).Render(string(ch))
				continue
			}
			// v9.13: pick the color based on this particle's fade (was b.parts[0] before,
			// which made every cell in the frame use the same fade state — wrong)
			colorIdx := 0
			if info.fade > 0 {
				colorIdx = minInt(info.fade, len(colors)-1)
			}
			line += lipgloss.NewStyle().Foreground(lipgloss.Color(colors[colorIdx])).Render(string(ch))
		}
		out = append(out, line)
	}
	return joinLines(out)
}

func (b *Burst) Active() bool { return b.active }

// ════════════════════════════════════════════════════════════════
// SlideIn (Harmonica spring)
// ════════════════════════════════════════════════════════════════

type SlideIn struct {
	spring   harmonica.Spring
	pos, vel float64
	active   bool
	age      int
}

func NewSlideIn() *SlideIn {
	return &SlideIn{
		spring: harmonica.NewSpring(harmonica.FPS(60), 7.0, 0.7),
	}
}

func (s *SlideIn) Trigger() {
	s.active = true
	s.age = 0
	s.pos = 30
	s.vel = 0
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
func (s *SlideIn) Active() bool    { return s.active }

// ════════════════════════════════════════════════════════════════
// Typewriter
// ════════════════════════════════════════════════════════════════

type Typewriter struct {
	target   string
	current  int
	speed    int
	active   bool
	done     bool
	lastTick int
}

func NewTypewriter() *Typewriter { return &Typewriter{speed: 2} }

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
	if delta < 2 {
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

// ════════════════════════════════════════════════════════════════
// Sparkles
// ════════════════════════════════════════════════════════════════

const sparkSyms = "·•◦●"

type Spark struct {
	x, y   int
	vx, vy float64
	life   float64
	symIdx int
}

type Sparkles struct {
	active bool
	sparks []Spark
	width  int
	height int
}

func NewSparkles() *Sparkles { return &Sparkles{} }

func (s *Sparkles) SetSize(w, h int) { s.width = w; s.height = h }

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
		lines[i] = blankString(s.width)
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

func blankString(n int) string {
	if n <= 0 {
		return ""
	}
	b := make([]byte, n)
	for i := range b {
		b[i] = ' '
	}
	return string(b)
}

func splitSpace(s string) []string {
	out := []string{}
	cur := ""
	for _, c := range s {
		if c == ' ' {
			if cur != "" {
				out = append(out, cur)
				cur = ""
			}
		} else {
			cur += string(c)
		}
	}
	if cur != "" {
		out = append(out, cur)
	}
	return out
}

// ════════════════════════════════════════════════════════════════
// Verdict Pulse (v9.13, §12.5)
// ════════════════════════════════════════════════════════════════
//
// When a sim emits a verdict (supports/refutes/inconclusive), the
// corresponding CardSimulation gets a 1.5s colored border pulse so
// the user sees the result visually without reading text.

type VerdictPulse struct {
	active  bool
	tick    int
	duration int
	color    string // "2"=green, "1"=red, "3"=yellow
}

// NewVerdictPulse returns an inactive pulse.
func NewVerdictPulse() *VerdictPulse { return &VerdictPulse{duration: 90} } // 90 ticks × 16ms ≈ 1.5s

// Trigger starts a pulse for the given verdict.
func (p *VerdictPulse) Trigger(verdict string) {
	p.active = true
	p.tick = 0
	switch verdict {
	case "supports_hypothesis":
		p.color = "2"
	case "refutes_hypothesis":
		p.color = "1"
	case "inconclusive":
		p.color = "3"
	default:
		p.color = "8" // dim
	}
}

// Tick advances the pulse.
func (p *VerdictPulse) Tick() {
	if !p.active {
		return
	}
	p.tick++
	if p.tick >= p.duration {
		p.active = false
	}
}

// Active returns true if the pulse is animating.
func (p *VerdictPulse) Active() bool { return p.active }

// Color returns the current pulse color (fades as the pulse ages).
func (p *VerdictPulse) Color() string {
	if !p.active {
		return ""
	}
	// Pulse fades: full color in the first 30%, then to dim
	if p.tick < p.duration/3 {
		return p.color
	}
	return "8"
}

// Intensity returns 0..1 for the pulse strength (used by renderers
// that want to vary border thickness or glow). Triangle envelope:
// 0 → 1 → 0 over the duration. Returns 0 when not active or past end.
func (p *VerdictPulse) Intensity() float64 {
	if !p.active || p.duration == 0 {
		return 0
	}
	t := float64(p.tick)
	d := float64(p.duration)
	if t < 0 || t > d {
		return 0
	}
	// Triangle: 0 → 1 → 0
	half := d / 2
	if t < half {
		return t / half
	}
	return 1.0 - (t-half)/half
}
