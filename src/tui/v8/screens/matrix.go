package screens

import (
	"math"
	"math/rand"
	"strings"
	"time"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// MatrixRain is a full-screen matrix rain easter egg.
type MatrixRain struct {
	width   int
	height  int
	columns []int
	done    bool
}

const matrixChars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*"

// NewMatrixRain creates the matrix rain overlay.
func NewMatrixRain() MatrixRain {
	return MatrixRain{columns: nil}
}

func (m MatrixRain) Title() string { return "Matrix" }
func (m MatrixRain) Done() bool    { return m.done }

func (m MatrixRain) Init() tea.Cmd {
	return tea.Tick(80*time.Millisecond, func(t time.Time) tea.Msg {
		return matrixTickMsg{t: t}
	})
}

func (m MatrixRain) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.columns = make([]int, m.width)
		if m.height > 0 && m.height < math.MaxInt/2 {
			for i := range m.columns {
				m.columns[i] = rand.Intn(m.height * 2)
			}
		}
		return m, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" || msg.String() == "ctrl+m" {
			m.done = true
			return m, nil
		}
	case matrixTickMsg:
		for i := range m.columns {
			m.columns[i]++
			if m.columns[i] > m.height+20 {
				m.columns[i] = rand.Intn(10) - 10
			}
		}
		return m, tea.Tick(80*time.Millisecond, func(t time.Time) tea.Msg {
			return matrixTickMsg{t: t}
		})
	}
	return m, nil
}

func (m MatrixRain) View() string {
	if m.width == 0 || m.height == 0 {
		return ""
	}

	green := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan)
	lightGreen := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Highlight)
	darkGreen := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Border)

	var rows []string
	for y := 0; y < m.height; y++ {
		var row strings.Builder
		for x := 0; x < m.width; x++ {
			col := m.columns[x]
			dist := y - col
			if dist == 0 {
				row.WriteString(lightGreen.Render(string(matrixChars[rand.Intn(len(matrixChars))])))
			} else if dist > 0 && dist < 12 {
				row.WriteString(green.Render(string(matrixChars[rand.Intn(len(matrixChars))])))
			} else if dist >= 12 && dist < 20 {
				row.WriteString(darkGreen.Render(string(matrixChars[rand.Intn(len(matrixChars))])))
			} else {
				row.WriteString(" ")
			}
		}
		rows = append(rows, row.String())
	}

	return strings.Join(rows, "\n")
}

type matrixTickMsg struct {
	t time.Time
}
