// Package probe runs a headless e2e probe against a live c4reqber backend.
// Usage: c4tui-v9 probe <query>
//
// Outputs a JSON report of the full discovery flow:
//   - auth (CSRF + register + login)
//   - submit (one-click)
//   - poll loop (status, phase, progress, result)
//   - papers (knowledge search)
//   - timing
//
// Designed for CI smoke tests and live integration verification.
package probe

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

// DefaultCredentials is the known-working probe user (created in session 1).
// v9 TUI uses these for live backend integration verification.
const (
	DefaultEmail    = "kilo@test.com"
	DefaultPassword = "test12345"
)

// Report is the JSON output of a probe run.
type Report struct {
	StartedAt   string         `json:"started_at"`
	DurationSec float64        `json:"duration_sec"`
	Backend     string         `json:"backend"`
	Auth        AuthResult     `json:"auth"`
	Submit      SubmitResult   `json:"submit"`
	PollHistory []PollSnapshot `json:"poll_history"`
	Papers      []PaperRow     `json:"papers"`
	Hypothesis  map[string]any `json:"hypothesis,omitempty"`
	Errors      []string       `json:"errors,omitempty"`
}

type AuthResult struct {
	CSRFHarvested bool   `json:"csrf_harvested"`
	RegisterOK    bool   `json:"register_ok"`
	LoginOK       bool   `json:"login_ok"`
	TokenLen      int    `json:"token_len"`
	Email         string `json:"email"`
}

type SubmitResult struct {
	JobID    string `json:"job_id"`
	OK       bool   `json:"ok"`
	Duration string `json:"duration"`
}

type PollSnapshot struct {
	Time     string  `json:"time"`
	Status   string  `json:"status"`
	Phase    string  `json:"phase"`
	Progress float64 `json:"progress"`
}

type PaperRow struct {
	Title         string `json:"title"`
	Year          any    `json:"year"`
	Venue         string `json:"venue"`
	DOI           string `json:"doi"`
	Source        string `json:"source"`
	CitationCount any    `json:"citation_count"`
}

// Run executes the full probe. Result is written to stdout as JSON.
func Run(apiURL, query string) error {
	start := time.Now()
	rep := Report{
		StartedAt:   start.UTC().Format(time.RFC3339),
		Backend:     apiURL,
		Auth:        AuthResult{Email: DefaultEmail},
		PollHistory: []PollSnapshot{},
		Papers:      []PaperRow{},
		Errors:      []string{},
	}
	defer func() {
		rep.DurationSec = time.Since(start).Seconds()
		out, _ := json.MarshalIndent(rep, "", "  ")
		fmt.Fprintln(os.Stdout, string(out))
	}()

	c := api.New(apiURL)
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()

	// 1. Health + CSRF
	if err := c.Health(ctx); err != nil {
		rep.Errors = append(rep.Errors, "health: "+err.Error())
		return nil
	}
	rep.Auth.CSRFHarvested = c.CSRF() != ""

	// 2. Register (idempotent — 200/409/422 are all OK)
	rep.Auth.RegisterOK = c.Register(ctx, DefaultEmail, DefaultPassword, "Probe v9") == nil

	// 3. Login
	if err := c.Login(ctx, DefaultEmail, DefaultPassword); err != nil {
		rep.Errors = append(rep.Errors, "login: "+err.Error())
		return nil
	}
	rep.Auth.LoginOK = c.Token() != ""
	rep.Auth.TokenLen = len(c.Token())

	// 4. Submit one-click
	subStart := time.Now()
	jobID, err := c.OneClick(ctx, query, "science")
	rep.Submit.Duration = time.Since(subStart).String()
	if err != nil {
		rep.Errors = append(rep.Errors, "submit: "+err.Error())
		return nil
	}
	rep.Submit.JobID = jobID
	rep.Submit.OK = true

	// 5. Poll loop (every 2s, max 30 polls = 60s)
	for i := 0; i < 30; i++ {
		js, err := c.JobStatus(ctx, jobID)
		if err != nil {
			rep.Errors = append(rep.Errors, fmt.Sprintf("poll[%d]: %s", i, err.Error()))
			time.Sleep(2 * time.Second)
			continue
		}
		rep.PollHistory = append(rep.PollHistory, PollSnapshot{
			Time:     time.Now().UTC().Format(time.RFC3339),
			Status:   js.Status,
			Phase:    js.Phase,
			Progress: js.Progress,
		})
		if js.Completed {
			if js.Result != nil {
				if hyp, ok := js.Result["hypothesis"].(map[string]any); ok {
					rep.Hypothesis = hyp
				}
			}
			break
		}
		time.Sleep(2 * time.Second)
	}

	// 6. Knowledge search (parallel discovery source)
	papers, err := c.KnowledgeSearch(ctx, query, 5)
	if err != nil {
		rep.Errors = append(rep.Errors, "knowledge: "+err.Error())
		return nil
	}
	for _, p := range papers {
		row := PaperRow{
			Title:         fieldString(p, "title"),
			Year:          p["year"],
			Venue:         fieldString(p, "venue"),
			DOI:           fieldString(p, "doi"),
			Source:        fieldString(p, "source"),
			CitationCount: p["citation_count"],
		}
		rep.Papers = append(rep.Papers, row)
	}

	return nil
}

func fieldString(m map[string]any, key string) string {
	if m == nil {
		return ""
	}
	v, ok := m[key]
	if !ok || v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return fmt.Sprintf("%v", v)
}
