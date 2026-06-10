package main

import (
	"fmt"
	"os"

	tea "charm.land/bubbletea/v2"
	zone "github.com/lrstanley/bubblezone/v2"

	tui "github.com/figuramax/c4reqber-tui-v9"
)

func main() {
	zone.NewGlobal()
	defer zone.Close()

	apiURL := os.Getenv("C4_API_URL")
	if apiURL == "" {
		apiURL = "http://127.0.0.1:8000"
	}

	app := tui.NewApp(apiURL)
	p := tea.NewProgram(app, tea.WithFPS(60))
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "c4tui-v9:", err)
		os.Exit(1)
	}
}
