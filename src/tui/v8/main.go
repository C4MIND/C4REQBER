package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"c4tui/config"
	"c4tui/internal"
	"c4tui/screens"
	"c4tui/splash"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
)

// app is the top-level model that orchestrates splash → main TUI transition.
type app struct {
	phase  string // "splash" | "tui"
	splash splash.Model
	tui    model
	cfg    config.Config
	width  int
	height int
}

func newApp(cfg config.Config) app {
	return app{
		phase:  "splash",
		splash: splash.New(),
		tui:    newModelWithConfig(cfg),
		cfg:    cfg,
	}
}

func (a app) Init() tea.Cmd {
	return a.splash.Init()
}

func (a app) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		if msg.String() == "ctrl+c" {
			// Graceful shutdown: cancel backend jobs, flush store, then quit
			if a.tui.CancelCtx != nil {
				a.tui.CancelCtx()
			}
			if a.tui.Store != nil {
				_ = a.tui.Store.Flush()
			}
			return a, tea.Quit
		}
	case tea.WindowSizeMsg:
		a.width = msg.Width
		a.height = msg.Height
	}

	if a.phase == "splash" {
		newSplash, cmd := a.splash.Update(msg)
		if sm, ok := newSplash.(splash.Model); ok {
			a.splash = sm
		}

		// Check if splash is done
		if a.splash.LoadingDone() {
			a.phase = "tui"
			// Replay the cached window size so the TUI model knows its dimensions
			// (the original WindowSizeMsg was consumed by the splash model).
			w, h := a.width, a.height
			if w == 0 || h == 0 {
				w, h = 80, 24
			}
			newTUI, tuiCmd := a.tui.Update(tea.WindowSizeMsg{Width: w, Height: h})
			if tui, ok := newTUI.(model); ok {
				a.tui = tui
			}
			cmds := []tea.Cmd{tuiCmd, a.tui.Init()}
			// Check first-run onboarding
			if screens.IsFirstRun() {
				a.tui.Screen = screens.ScreenOnboarding
				a.tui.Overlay = screens.NewOnboarding()
				newOverlay, overlayCmd := a.tui.Overlay.Update(tea.WindowSizeMsg{Width: w, Height: h})
				if overlay, ok := newOverlay.(screens.Model); ok {
					a.tui.Overlay = overlay
				}
				cmds = append(cmds, overlayCmd)
			}
			return a, tea.Batch(cmds...)
		}
		return a, cmd
	}

	// Main TUI phase
	newTUI, cmd := a.tui.Update(msg)
	if tui, ok := newTUI.(model); ok {
		a.tui = tui
	}
	return a, cmd
}

func (a app) View() string {
	if a.phase == "splash" {
		return a.splash.View()
	}
	return a.tui.View()
}

func main() {
	apiURL := flag.String("api", "", "Backend API base URL (overrides C4_API_URL)")
	lang := flag.String("lang", "", "UI language: en, ru, zh, ja, de, ar, hi (overrides default)")
	theme := flag.String("theme", "", "UI theme: dark, matrix, paper (overrides default)")
	flag.Parse()

	cfg := config.FromEnv()
	if *apiURL != "" {
		cfg.API.BaseURL = *apiURL
	}
	if err := cfg.Validate(); err != nil {
		fmt.Fprintf(os.Stderr, "Config error: %v\n", err)
		os.Exit(1)
	}

	application := newApp(cfg)

	// Apply CLI overrides before startup
	if *lang != "" {
		l := internal.ParseLanguage(*lang)
		application.tui.Language = l
		internal.ActiveLanguage = l
		application.tui.Header.Flag = internal.LanguageFlags[l]
	}
	if *theme != "" {
		switch strings.ToLower(*theme) {
		case "matrix":
			styles.SetTheme(styles.MatrixTheme)
		case "paper":
			styles.SetTheme(styles.PaperTheme)
		case "dark":
			styles.SetTheme(styles.DarkTheme)
		}
		application.tui.Pipeline.SetThemeColors()
	}

	p := tea.NewProgram(
		application,
		tea.WithAltScreen(),
		tea.WithMouseCellMotion(),
	)
	m, err := p.Run()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	// Flush any pending session data before exit.
	if a, ok := m.(app); ok && a.tui.Store != nil {
		if err := a.tui.Store.Flush(); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: failed to flush session: %v\n", err)
		}
	}
}
