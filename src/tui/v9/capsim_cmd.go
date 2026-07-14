package tui

import (
	"context"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
)

// capsimMsg is delivered when capabilities have been fetched (or failed).
type capsimMsg struct {
	report *capsim.Report
	err    error
}

// capsimCmd fetches the capabilities report. Async — runs off the UI thread.
// Used by Ctrl+Shift+C and by `:capabilities refresh`.
func capsimCmd(client *capsim.Client, forceRefresh bool) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 6*time.Second)
		defer cancel()
		r, err := client.Get(ctx, forceRefresh)
		if err != nil {
			// Fall back to a safe empty report so the overlay still renders
			// (showing the "backend unreachable" hint) instead of crashing.
			return capsimMsg{report: capsim.Fallback(), err: err}
		}
		return capsimMsg{report: r, err: nil}
	}
}
