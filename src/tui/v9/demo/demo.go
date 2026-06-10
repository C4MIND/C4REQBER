// Package demo provides a scripted fake discovery flow for first-time users.
// Used by --demo flag in the TUI main binary.
package demo

import (
	"context"
	"fmt"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

// CardEvent is one scripted card emission.
type CardEvent struct {
	Delay     time.Duration
	Kind      string
	Title     string
	Body      string
	Meta      []string
	Status    string
	Progress  float64
}

// Script is a series of fake card events.
type Script struct {
	Topic      string
	Events     []CardEvent
	TotalTime  time.Duration
}

// Default returns the stock "first-time user" demo.
func Default(topic string) *Script {
	// 5 phase cards + 1 hypothesis + 3 papers, 30s total
	return &Script{
		Topic:     topic,
		TotalTime: 30 * time.Second,
		Events: []CardEvent{
			{Delay: 0, Kind: "submit", Title: "→ " + topic, Body: "demo submission"},
			{Delay: 2 * time.Second, Kind: "phase", Title: "A: Framing", Body: "complexity 0.74", Status: "done", Progress: 0.14},
			{Delay: 2 * time.Second, Kind: "phase", Title: "B: Knowledge acquisition", Body: "12 sources fired", Status: "done", Progress: 0.28},
			{Delay: 2 * time.Second, Kind: "phase", Title: "C: Gap analysis", Body: "3 high-priority gaps", Status: "done", Progress: 0.42},
			{Delay: 3 * time.Second, Kind: "phase", Title: "D: Hypothesis generation", Body: "1 hypothesis formed", Status: "done", Progress: 0.57},
			{Delay: 3 * time.Second, Kind: "phase", Title: "E: Simulation", Body: "OpenMM · 3,200 steps", Status: "done", Progress: 0.71},
			{Delay: 4 * time.Second, Kind: "phase", Title: "F: Dissertation", Body: "4,521 chars drafted", Status: "done", Progress: 0.85},
			{Delay: 4 * time.Second, Kind: "phase", Title: "G: Quality control", Body: "all gates passed", Status: "done", Progress: 1.0},
			{Delay: 5 * time.Second, Kind: "hypothesis", Title: "Hypothesis", Body: "Use truncated 17-nt guide RNAs with NGG PAM + chemically-modified 2'-O-methyl at three terminal positions to reduce off-target binding while preserving on-target efficiency in primary human T-cells.", Meta: []string{"source: LLMProvider/v8", "confidence 0.87"}, Status: "done"},
			{Delay: 3 * time.Second, Kind: "paper", Title: "Optimized sgRNA design to maximize activity and minimize off-target", Body: "Doench JG et al. · Nature Biotech 2016", Meta: []string{"doi: 10.1038/nbt.3437", "source: openalex", "citations 1847"}, Status: "done"},
			{Delay: 2 * time.Second, Kind: "paper", Title: "Genome-scale CRISPR-Cas9 knockout screening", Body: "Shalem O et al. · Science 2014", Meta: []string{"doi: 10.1126/science.1247005", "source: openalex", "citations 2840"}, Status: "done"},
		},
	}
}

// AsAPIResult converts a demo script to an api.JobStatus-like result.
// Used to validate the rendering path with realistic data.
func (s *Script) AsAPIResult() map[string]any {
	return map[string]any{
		"status":   "complete",
		"phase":    "G: Quality",
		"progress": 1.0,
		"result": map[string]any{
			"hypothesis": map[string]any{
				"source":        "LLMProvider/v8",
				"text":          "Use truncated 17-nt guide RNAs with NGG PAM + chemically-modified 2'-O-methyl at three terminal positions to reduce off-target binding while preserving on-target efficiency in primary human T-cells.",
				"novelty_score": 0.87,
			},
			"papers": []any{
				map[string]any{
					"title":          "Optimized sgRNA design to maximize activity and minimize off-target",
					"authors":       []string{"Doench JG", "Fusi N", "Sullender M"},
					"year":          2016,
					"venue":         "Nature Biotechnology",
					"doi":           "10.1038/nbt.3437",
					"citation_count": 1847,
					"source":        "openalex",
				},
				map[string]any{
					"title":          "Genome-scale CRISPR-Cas9 knockout screening",
					"authors":       []string{"Shalem O", "Sanjana NE", "Hartenian E"},
					"year":          2014,
					"venue":         "Science",
					"doi":           "10.1126/science.1247005",
					"citation_count": 2840,
					"source":        "openalex",
				},
			},
		},
		"completed_at": float64(time.Now().Unix()),
	}
}

// Run executes the demo by emitting events into the channel.
// Used by --demo flag.
func (s *Script) Run(ctx context.Context, emit func(CardEvent)) error {
	for _, e := range s.Events {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(e.Delay):
		}
		emit(e)
	}
	_ = fmt.Sprintf("demo %s complete in %s", s.Topic, s.TotalTime)
	return nil
}

var _ = api.JobStatus{} // keep import alive for future use
