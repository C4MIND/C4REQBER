// Package main is the entry point for c4tui-v9 (TUI Cockpit).
// Supports: --demo flag (runs scripted demo without backend)
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	tea "charm.land/bubbletea/v2"
	zone "github.com/lrstanley/bubblezone/v2"

	tui "github.com/figuramax/c4reqber-tui-v9"
	"github.com/figuramax/c4reqber-tui-v9/demo"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

func main() {
	demoMode := false
	topic := "design a CRISPR guide RNA with minimal off-targets in T-cells"
	for _, arg := range os.Args[1:] {
		if arg == "--demo" {
			demoMode = true
		}
	}

	zone.NewGlobal()
	defer zone.Close()

	apiURL := os.Getenv("C4_API_URL")
	if apiURL == "" {
		apiURL = "http://127.0.0.1:8000"
	}

	if demoMode {
		runDemo(topic)
		return
	}

	app := tui.NewApp(apiURL)
	p := tea.NewProgram(app, tea.WithFPS(60))
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "c4tui-v9:", err)
		os.Exit(1)
	}
}

func runDemo(topic string) {
	fmt.Println("TUI v9 DEMO MODE — no backend required")
	fmt.Println("Topic:", topic)
	fmt.Println()
	script := demo.Default(topic)
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	_ = i18n.T("app.title")
	if err := script.Run(ctx, func(e demo.CardEvent) {
		fmt.Printf("  → [%s] %s: %s\n", e.Delay.Round(time.Millisecond), e.Kind, e.Title)
	}); err != nil {
		fmt.Fprintln(os.Stderr, "demo cancelled:", err)
	}
	fmt.Println()
	fmt.Println("Demo complete. Real mode: omit --demo flag.")
}
