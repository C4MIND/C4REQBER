// Package main is the entry point for c4tui-v9 (TUI Cockpit).
// Supports: --demo flag (scripted demo without backend)
//           --version (print version)
//           --config (print resolved config from env)
package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"strings"
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
var version = "v9.11.7"

// gitRef returns the git commit short hash, or empty if not available.
func gitRef() string {
	out, err := exec.Command("git", "rev-parse", "--short", "HEAD").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

func main() {
	demoMode := false
	demoStory := ""
	showConfig := false
	showVersion := false
	showStats := false
	showHistory := false
	pruneDays := 0
	exportPath := ""
	topic := "design a CRISPR guide RNA with minimal off-targets in T-cells"
	for i, arg := range os.Args[1:] {
		switch {
		case arg == "--demo":
			demoMode = true
		case strings.HasPrefix(arg, "--story="):
			demoStory = strings.TrimPrefix(arg, "--story=")
		case arg == "--version" || arg == "-v":
			showVersion = true
		case arg == "--config":
			showConfig = true
		case arg == "--stats":
			showStats = true
		case arg == "--history":
			showHistory = true
		case arg == "--export-stats":
			if i+1 < len(os.Args)-1 {
				exportPath = os.Args[i+2]
			}
		case strings.HasPrefix(arg, "--prune-history="):
			fmt.Sscanf(arg, "--prune-history=%d", &pruneDays)
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
	if showHistory {
		runHistory()
		return
	}
	if pruneDays > 0 {
		runPrune(pruneDays)
		return
	}
	if exportPath != "" {
		runExportStats(exportPath)
		return
	}

	if demoMode {
		runDemo(topic, demoStory)
		return
	}

	i18n.SetLang(cfg.Lang)
	app := tui.NewApp(cfg.APIURL)
	cfg.ApplyToModel(app)

	if cfg.SaveHistory {
		defer saveHistory(cfg)
	}

	// Run splash first, then the app
	if os.Getenv("C4_NO_SPLASH") == "" && os.Getenv("C4_SPLASH") != "0" {
		runSplash(version, gitRef())
	}

	p := tea.NewProgram(app, tea.WithFPS(60), KeyDedupFilter())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "c4tui-v9:", err)
		os.Exit(1)
	}
}

func runDemo(topic, story string) {
	fmt.Println("TUI v9 DEMO MODE — no backend required")
	fmt.Println("Topic:", topic)
	if story != "" {
		fmt.Println("Story:", story)
	}
	fmt.Println()
	var script *demo.Script
	if story != "" {
		script = demo.Story(story, topic)
	} else {
		script = demo.Default(topic)
	}
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
	fmt.Println("Stories: --demo --story=crispr|sleep|lang")
}

// runSplash displays the splash screen for ~3s then returns.
func runSplash(version, gitRef string) {
	m := tui.NewSplash(version, gitRef)
	p := tea.NewProgram(m, tea.WithFPS(30))
	if _, err := p.Run(); err != nil {
		// Non-fatal: splash is decorative
		return
	}
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

func runHistory() {
	files, err := tui.LoadAllHistoryFiles()
	if err != nil {
		fmt.Fprintf(os.Stderr, "load history: %v\n", err)
		os.Exit(1)
	}
	if len(files) == 0 {
		fmt.Println("No history files.")
		return
	}
	fmt.Printf("c4tui-v9 %s — per-run history (%d runs)\n\n", version, len(files))
	for i, f := range files {
		snap := f.Snapshot
		fmt.Printf("[%d] %s\n", i+1, f.SessionEnd.Format("2006-01-02 15:04:05"))
		fmt.Printf("    config:    %s\n", f.Config)
		fmt.Printf("    discoveries: %d (ok=%d fail=%d abort=%d)\n",
			snap.Discoveries, snap.DiscoveriesOK, snap.DiscoveriesFail, snap.DiscoveriesAbort)
		fmt.Printf("    cost:      $%.3f  api: %d (err: %d)  longest: %.1fs\n",
			snap.TotalCost, snap.TotalAPICalls, snap.APIErrors, snap.LongestRunSec)
		fmt.Println()
	}
}

func runPrune(days int) {
	files, err := tui.LoadAllHistoryFiles()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	cutoff := time.Now().AddDate(0, 0, -days)
	removed := 0
	for _, f := range files {
		if f.SessionEnd.Before(cutoff) {
			home, _ := os.UserHomeDir()
			path := fmt.Sprintf("%s/.config/c4reqber/tui-v9-history-%s.json",
				home, f.SessionEnd.Format("2006-01-02-15-04-05"))
			if err := os.Remove(path); err == nil {
				removed++
			}
		}
	}
	fmt.Printf("Pruned %d history file(s) older than %d days.\n", removed, days)
}

func runExportStats(path string) {
	files, err := tui.LoadAllHistoryFiles()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	stats := tui.Aggregate(files)
	if err := os.WriteFile(path, []byte(stats.FormatStats()), 0644); err != nil {
		fmt.Fprintf(os.Stderr, "export: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Exported stats to %s\n", path)
}

// Silence unused import in case drop a path.
var _ telemetry.Snapshot
var _ = time.Now
