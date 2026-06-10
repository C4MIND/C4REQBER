// Package main is the entry point for c4tui-v9 (TUI Cockpit).
// Supports: --demo flag (scripted demo without backend)
//           --version (print version)
//           --config (print resolved config from env)
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
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

// version is set at build time via -ldflags "-X main.version=..."
var version = "v9.7.0"

func main() {
	demoMode := false
	showConfig := false
	showVersion := false
	showStats := false
	topic := "design a CRISPR guide RNA with minimal off-targets in T-cells"
	for _, arg := range os.Args[1:] {
		switch arg {
		case "--demo":
			demoMode = true
		case "--version", "-v":
			showVersion = true
		case "--config":
			showConfig = true
		case "--stats":
			showStats = true
		}
	}

	zone.NewGlobal()
	defer zone.Close()

	cfg := tui.LoadConfig()

	if showVersion {
		fmt.Printf("c4tui-v9 %s\n", version)
		return
	}
	if showConfig {
		fmt.Printf("c4tui-v9 %s\n", version)
		fmt.Printf("Config: %s\n", cfg.String())
		return
	}
	if showStats {
		runStats()
		return
	}

	if demoMode {
		runDemo(topic)
		return
	}

	i18n.SetLang(cfg.Lang)
	app := tui.NewApp(cfg.APIURL)
	cfg.ApplyToModel(app)

	if cfg.SaveHistory {
		defer saveHistory(cfg)
	}

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

func saveHistory(cfg tui.Config) {
	// We can't easily get the app's telemetry from main after Run() returns
	// because the model is internal. So we read it from disk if it exists
	// (it's been written by the model itself on shutdown).
	// For now, this is a no-op stub — full implementation deferred to v9.7
	// where we add a hook to pass tel back from model to main.
	_ = cfg
}

func runStats() {
	fmt.Printf("c4tui-v9 %s — telemetry stats\n", version)
	files, err := tui.LoadAllHistoryFiles()
	if err != nil {
		fmt.Fprintf(os.Stderr, "load history: %v\n", err)
		os.Exit(1)
	}
	if len(files) == 0 {
		fmt.Println("No history files found in ~/.config/c4reqber/")
		fmt.Println("(Run c4tui-v9 at least once to generate history.)")
		return
	}
	stats := tui.Aggregate(files)
	fmt.Printf("Loaded %d history file(s) from ~/.config/c4reqber/\n\n", len(files))
	fmt.Print(stats.FormatStats())
}

// Silence unused import in case drop a path.
var _ telemetry.Snapshot
var _ = time.Now
