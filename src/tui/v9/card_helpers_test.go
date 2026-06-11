package tui

import (
	"strings"
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestTruncate(t *testing.T) {
	cases := map[string]struct {
		s    string
		max  int
		want string
	}{
		"short":    {"hello", 10, "hello"},
		"exact":    {"hello", 5, "hello"},
		"long":     {"hello world", 5, "hell…"},
		"one":      {"hello", 1, "…"},
		"zero":     {"hello", 0, ""},
		"cyrillic": {"привет", 4, "при…"},
		"wide":     {"日本語", 2, "日…"},
	}
	for name, c := range cases {
		if got := truncate(c.s, c.max); got != c.want {
			t.Errorf("%s: truncate(%q,%d) = %q, want %q", name, c.s, c.max, got, c.want)
		}
	}
}

func TestCardToMarkdownHypothesis(t *testing.T) {
	c := cards.Card{
		Kind:  cards.KindHypothesis,
		Title: "CRISPR off-target hypothesis",
		Body:  "guides with GC content <40% have higher off-target rates",
		Time:  time.Date(2026, 6, 11, 14, 32, 0, 0, time.UTC),
		Meta:  []cards.MetaKV{{Key: "source", Value: "openmm"}, {Key: "novelty", Value: "0.87"}},
	}
	md := cardToMarkdown(c)
	for _, want := range []string{
		"# CRISPR off-target hypothesis",
		"guides with GC content <40%",
		"source: openmm",
		"novelty: 0.87",
		"2026-06-11",
	} {
		if !strings.Contains(md, want) {
			t.Errorf("markdown missing %q\n--- got ---\n%s", want, md)
		}
	}
}

func TestCardToMarkdownSimulation(t *testing.T) {
	c := cards.Card{
		ID:    cards.NextID(),
		Kind:  cards.KindSimulation,
		Title: "openmm protein folding",
		Body:  "ΔG = -7.3 kcal/mol",
		Time:  time.Now(),
		Sim: cards.SimFields{
			Engine:       "openmm",
			EngineStatus: "available",
			Domain:       "biology",
			Pattern:      "protein_folding",
			Verdict:      "supports_hypothesis",
			CostUSD:      0.0001,
			PatternsTried: []cards.PatternTry{
				{Engine: "openmm", Status: "available"},
				{Engine: "jaxsim", Status: "skipped", Reason: "no MD"},
			},
		},
	}
	md := cardToMarkdown(c)
	for _, want := range []string{
		"openmm",
		"supports_hypothesis",
		"protein_folding",
		"0.0001",
		"Fallback chain",
		"openmm (available)",
		"jaxsim (skipped)",
	} {
		if !strings.Contains(md, want) {
			t.Errorf("simulation markdown missing %q", want)
		}
	}
}
