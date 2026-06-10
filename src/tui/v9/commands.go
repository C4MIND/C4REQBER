package tui

import (
	"context"
	"time"

	tea "charm.land/bubbletea/v2"
)

// submitCmd fires a discovery request and sends apiSubmitMsg back.
func submitCmd(apiURL, query, _ string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		c := newAPIClient(apiURL)
		_ = c.ensureCSRF(ctx)
		_ = c.register(ctx, "kilo-v9@test.com", "test12345", "Kilo v9")
		_ = c.login(ctx, "kilo-v9@test.com", "test12345")
		id, err := c.submit(ctx, query, "science")
		return apiSubmitMsg{jobID: id, err: err}
	}
}

func pollCmd(apiURL, jobID string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		c := newAPIClient(apiURL)
		msg, err := c.poll(ctx, jobID)
		if err != nil {
			return apiPollMsg{err: err}
		}
		return msg
	}
}

func papersCmd(apiURL, query string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		c := newAPIClient(apiURL)
		papers, err := c.papers(ctx, query, 3)
		if err != nil {
			return apiPapersMsg{err: err}
		}
		return apiPapersMsg{papers: papers}
	}
}

var _ = time.Second
