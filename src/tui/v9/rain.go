package tui

import (
	"math/rand"

	"charm.land/lipgloss/v2"
)

// MatrixRain: katakana chars falling in feed background when idle.
// Subtly fades behind cards; stops on any user input.
type Rain struct {
	width, height int
	drops         []int
	speed         int
	tick          int
	chars         []rune
}

func NewRain() *Rain {
	return &Rain{
		speed: 1,
		chars: []rune("ｱｳｴｵｶｷｸｹｺｻｼｽｾ￠￡￢￣￤￨￩￪￫￬￭￮￯￰￱￲￳￴￵￶￷￸￹￺￻￼�￾ｱｲｳｴｵabcdefghijklmnopqrstuvwxyz0123456789@#$%&*+-/=<>?^_~"),
	}
}

func (r *Rain) SetSize(w, h int) {
	r.width = w
	r.height = h
	if r.drops == nil || len(r.drops) < w {
		r.drops = make([]int, w)
		for i := range r.drops {
			// start drops at y in [-h*2, -1] (always strictly negative → all off-screen)
			r.drops[i] = -1 - rand.Intn(h*2)
		}
	}
}

func (r *Rain) Tick() {
	r.tick++
	if r.tick%2 != 0 { // 30fps visual
		return
	}
	for i := range r.drops {
		r.drops[i] += r.speed
		if r.drops[i] > r.height+5 {
			r.drops[i] = -rand.Intn(r.height)
		}
	}
}

func (r *Rain) Render() string {
	if r.width == 0 || r.height == 0 {
		return ""
	}
	grid := make([][]rune, r.height)
	for i := range grid {
		grid[i] = make([]rune, r.width)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}
	anyOnScreen := false
	for x := 0; x < r.width && x < len(r.drops); x++ {
		y := r.drops[x]
		if y < 0 || y >= r.height {
			continue
		}
		anyOnScreen = true
		grid[y][x] = r.chars[rand.Intn(len(r.chars))]
		if y > 0 && y-1 < r.height {
			grid[y-1][x] = r.chars[rand.Intn(len(r.chars))]
		}
	}
	if !anyOnScreen {
		return "" // all drops off-screen, no point rendering
	}
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("22")) // very dim green
	bright := lipgloss.NewStyle().Foreground(lipgloss.Color("42"))   // brighter head
	var out []string
	for y, row := range grid {
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
