package main

import (
	"os"
	"testing"

	"c4tui/config"
	tea "github.com/charmbracelet/bubbletea"
)

func TestDebugView(t *testing.T) {
	cfg := config.FromEnv()
	cfg.API.BaseURL = "http://localhost:8000"
	m := newModelWithConfig(cfg)
	m.Width = 130
	m.Height = 42
	newM, _ := m.Update(tea.WindowSizeMsg{Width: m.Width, Height: m.Height})
	m = newM.(model)
	m.Header.Discoveries = 42
	m.Header.Clock = "12:00:00"
	m.Header.Online = true
	m.Header.LLMStatus = "ollama  lmstudio  mlx"
	m.Mascot.Stats.Energy = 75
	m.Mascot.Stats.Curiosity = 60
	m.Mascot.Stats.Bond = 30
	m.Mascot.Stats.Discoveries = 5
	m.Mascot.Musing = "The cube remembers every discovery..."
	m.InputBar.Mode = "discover"
	m.InputBar.TextArea.SetValue("Neural-symbolic integration")
	m.Pipeline.Running = true
	m.Pipeline.CurPhase = 3
	m.Pipeline.Statuses = []string{"✓", "✓", "✓", "●", "○", "○", "○"}
	m.Pipeline.Progress = []float64{1.0, 1.0, 1.0, 0.45, 0, 0, 0}
	m.Pipeline.Infos = []string{"100%", "100%", "100%", "45%", "", "", ""}
	m.Result.Topic = "Neural-symbolic integration"
	m.Result.Papers = 12
	m.Result.Hypotheses = 4
	m.Result.Quality = "A"
	m.Result.SetContent()
	out := m.View()
	os.WriteFile("/tmp/tui_v3.txt", []byte(out), 0644)
	t.Log("Saved to /tmp/tui_v3.txt")
}
