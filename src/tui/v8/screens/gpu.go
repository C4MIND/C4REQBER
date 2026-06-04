package screens

import (
	"context"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// GPUMonitor shows nvidia-smi style stats.
type GPUMonitor struct {
	width  int
	height int
	gpus   []gpuInfo
	done   bool
}

type gpuInfo struct {
	name     string
	memUsed  string
	memTotal string
	util     string
	temp     string
}

// NewGPUMonitor tries to read GPU stats from nvidia-smi.
func NewGPUMonitor() GPUMonitor {
	g := GPUMonitor{}
	g.readNvidia()
	return g
}

func (g *GPUMonitor) readNvidia() {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	out, err := exec.CommandContext(ctx, "nvidia-smi",
		"--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
		"--format=csv,noheader,nounits").Output()
	if err != nil {
		return
	}
	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.Split(line, ", ")
		if len(parts) >= 5 {
			g.gpus = append(g.gpus, gpuInfo{
				name:     strings.TrimSpace(parts[0]),
				memUsed:  strings.TrimSpace(parts[1]),
				memTotal: strings.TrimSpace(parts[2]),
				util:     strings.TrimSpace(parts[3]),
				temp:     strings.TrimSpace(parts[4]),
			})
		}
	}
}

func (g GPUMonitor) Title() string { return "GPU Monitor" }
func (g GPUMonitor) Done() bool    { return g.done }

func (g GPUMonitor) Init() tea.Cmd { return nil }

func (g GPUMonitor) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		g.width = msg.Width
		g.height = msg.Height
		return g, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			g.done = true
			return g, nil
		}
	}
	return g, nil
}

func (g GPUMonitor) View() string {
	if g.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("GPU Monitor")
	dim := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	green := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Success)

	if len(g.gpus) == 0 {
		content := lipgloss.JoinVertical(lipgloss.Center,
			title, "", dim.Render("No NVIDIA GPUs detected."),
			dim.Render("nvidia-smi not available or returned no data."),
		)
		return g.centerBox(content)
	}

	var cards []string
	for _, gpu := range g.gpus {
		util, _ := strconv.Atoi(gpu.util)
		bar := renderBar(util, 30)
		utilStr := green.Render(fmt.Sprintf("%s%%", gpu.util))
		if util > 80 {
			utilStr = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Red).Render(fmt.Sprintf("%s%%", gpu.util))
		}
		card := lipgloss.JoinVertical(lipgloss.Left,
			fmt.Sprintf("  %s  %s°C", gpu.name, gpu.temp),
			fmt.Sprintf("  Memory: %s / %s MiB", gpu.memUsed, gpu.memTotal),
			fmt.Sprintf("  Util:   %s %s", bar, utilStr),
		)
		cards = append(cards, lipgloss.NewStyle().
			Width(min(60, g.width-8)).
			Padding(1).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(styles.ActiveTheme().Border).
			Render(card))
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		lipgloss.JoinVertical(lipgloss.Left, cards...),
		"",
		dim.Render("Press Esc or Q to close"),
	)

	return g.centerBox(content)
}

func (g GPUMonitor) centerBox(content string) string {
	box := lipgloss.NewStyle().
		Width(min(70, g.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)
	return lipgloss.Place(
		g.width, g.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}

func renderBar(pct, width int) string {
	filled := (pct * width) / 100
	if filled < 0 {
		filled = 0
	}
	if filled > width {
		filled = width
	}
	empty := width - filled
	return lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan).Render(strings.Repeat("█", filled)) +
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Border).Render(strings.Repeat("░", empty))
}
