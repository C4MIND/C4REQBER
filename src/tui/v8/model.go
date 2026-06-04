package main

import (
	"context"
	"time"

	"c4tui/backend"
	"c4tui/config"
	"c4tui/internal"
	"c4tui/screens"
	"c4tui/widgets"
	tea "github.com/charmbracelet/bubbletea"
)

// model is the Bubble Tea state container.
type model struct {
	Width  int
	Height int
	Cfg    config.Config

	Header   widgets.Header
	InputBar widgets.InputBar
	Pipeline widgets.Pipeline
	Result   widgets.Result
	C4Grid   widgets.C4Grid
	Mascot   widgets.CubeMascot
	Chat     widgets.Chat
	Help     widgets.Help
	Toast    widgets.Toast
	Backend  *backend.Bridge

	Store        *internal.Store
	Screen       screens.Screen
	Overlay      screens.Model
	Discoveries  int
	JobID        string
	PipelineCtx  context.Context
	CancelCtx    context.CancelFunc
	LastResult   map[string]any
	Language     internal.Language
	PipelineMode string
	lastTopic    string
	lastTyping   time.Time

	// SSE streaming state
	SSEEvents <-chan backend.SSEEvent
	SSEErrCh  <-chan error
	SSEActive bool

	pollTimer *time.Timer
}

// newModel creates the initial model with default configuration.
func newModel() model {
	cfg := config.FromEnv()
	return newModelWithConfig(cfg)
}

// newModelWithConfig creates the initial model with a custom configuration.
func newModelWithConfig(cfg config.Config) model {
	b := backend.NewBridgeWithCredentials(cfg.API.BaseURL, cfg.API.APIKey, cfg.API.DevBypassToken)
	h := widgets.NewHeader(cfg)
	h.HealthCheck = func() bool {
		ctx, cancel := context.WithTimeout(context.Background(), cfg.API.Timeout)
		defer cancel()
		ok, _ := b.Health(ctx)
		return ok
	}
	m := model{
		Width:    0,
		Height:   0,
		Cfg:      cfg,
		Header:   h,
		InputBar: widgets.NewInputBar(cfg),
		Pipeline: widgets.NewPipeline(cfg),
		Result:   widgets.NewResult(cfg),
		C4Grid:   widgets.NewC4Grid(cfg),
		Mascot:   widgets.NewMascot(cfg),
		Chat:     widgets.NewChat(cfg),
		Help:     widgets.NewHelp(cfg),
		Toast:    widgets.NewToast(),
		Backend:  b,
		Language: internal.LangEN,
	}
	m.Store = internal.NewStore()
	m.Discoveries = m.Store.DiscoveriesCount
	m.Header.Discoveries = m.Discoveries
	m.Header.Flag = internal.LanguageFlags[m.Language]
	// Load history into input bar
	recent := m.Store.Recent(20)
	history := make([]string, 0, len(recent))
	for i := len(recent) - 1; i >= 0; i-- {
		if recent[i].Topic != "" {
			history = append(history, recent[i].Topic)
		}
	}
	m.InputBar.SetHistory(history)
	return m
}

// Init returns the initial command.
func (m model) Init() tea.Cmd {
	return tea.Batch(
		m.Header.Init(),
		m.Mascot.Init(),
		m.C4Grid.Init(),
		m.helpTipTick(),
		tea.EnterAltScreen,
		listenForSignals(),
	)
}
