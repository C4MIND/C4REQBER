package tui

import (
	"strings"
	"testing"

	"charm.land/lipgloss/v2"
	zone "github.com/lrstanley/bubblezone/v2"
)

func init() {
	zone.NewGlobal()
}

// stripANSI removes ANSI escape codes for snapshot testing.
var ansiRe = strings.NewReplacer(
	"\x1b[0m", "", "\x1b[1m", "", "\x1b[2m", "", "\x1b[4m", "",
	"\x1b[30m", "", "\x1b[31m", "", "\x1b[32m", "", "\x1b[33m", "",
	"\x1b[34m", "", "\x1b[35m", "", "\x1b[36m", "", "\x1b[37m", "",
	"\x1b[90m", "", "\x1b[91m", "", "\x1b[92m", "", "\x1b[93m", "",
	"\x1b[94m", "", "\x1b[95m", "", "\x1b[96m", "", "\x1b[97m", "",
	"\x1b[?25l", "", "\x1b[?25h", "", "\x1b[?1049h", "", "\x1b[?1049l", "",
	"\x1b[K", "", "\x1b[H", "", "\x1b[2J", "",
)

func stripANSI(s string) string {
	// Generic ESC[...m stripping
	var out strings.Builder
	i := 0
	for i < len(s) {
		if s[i] == 0x1b && i+1 < len(s) && s[i+1] == '[' {
			j := i + 2
			for j < len(s) {
				if (s[j] >= 0x40 && s[j] <= 0x7e) {
					j++
					break
				}
				j++
			}
			i = j
			continue
		}
		out.WriteByte(s[i])
		i++
	}
	return out.String()
}

func TestSnapshotEmptyState(t *testing.T) {
	SetLang(LangEN)
	m := NewApp("http://127.0.0.1:8000")
	m.width = 120
	m.height = 40
	m.layout()
	view := stripANSI(m.View().Content)
	if !strings.Contains(view, "C4REQBER v9") {
		t.Errorf("missing header in:\n%s", view)
	}
	if !strings.Contains(view, "READY") {
		t.Errorf("missing footer in:\n%s", view)
	}
	if !strings.Contains(view, "Ready for your first discovery") {
		t.Errorf("missing empty title in:\n%s", view)
	}
}

func TestSnapshotWithCard(t *testing.T) {
	m := NewApp("http://127.0.0.1:8000")
	m.width = 120
	m.height = 40
	m.layout()
	m.appendCard(Card{
		Kind: CardPhase, Title: "Phase A: Framing",
		Body: "CRISPR off-target in T-cells", Status: "running", Progress: 0.5,
	})
	view := stripANSI(m.View().Content)
	if !strings.Contains(view, "Phase A") {
		t.Errorf("missing phase card title in:\n%s", view)
	}
}

func TestSnapshotErrorCard(t *testing.T) {
	m := NewApp("http://127.0.0.1:8000")
	m.width = 120
	m.height = 40
	m.layout()
	m.appendCard(Card{Kind: CardError, Title: "Submit failed", Body: "connection refused"})
	view := stripANSI(m.View().Content)
	if !strings.Contains(view, "Submit failed") {
		t.Errorf("missing error card")
	}
}

func TestSnapshotRussian(t *testing.T) {
	SetLang(LangRU)
	defer SetLang(LangEN)
	m := NewApp("http://127.0.0.1:8000")
	m.width = 120
	m.height = 40
	m.layout()
	view := stripANSI(m.View().Content)
	if !strings.Contains(view, "ГОТОВ") {
		t.Errorf("missing Russian READY in:\n%s", view)
	}
}

func TestProgressBar(t *testing.T) {
	tests := []struct {
		p    float64
		want string
	}{
		{0.0, "[░░░░░░░░░░░░░░░░░░░░]"},
		{1.0, "[████████████████████]"},
		{0.5, "[██████████░░░░░░░░░░]"},
	}
	for _, tt := range tests {
		got := progressBar(tt.p, 20)
		if got != tt.want {
			t.Errorf("progressBar(%v) = %q, want %q", tt.p, got, tt.want)
		}
	}
}

func TestStringField(t *testing.T) {
	m := map[string]any{
		"title": "Hello",
		"year":  2020,
		"missing": nil,
	}
	if stringField(m, "title") != "Hello" {
		t.Error("title")
	}
	if stringField(m, "year") != "2020" {
		t.Error("year")
	}
	if stringField(m, "missing") != "" {
		t.Error("missing")
	}
	if stringField(nil, "anything") != "" {
		t.Error("nil map")
	}
}

var _ = lipgloss.Color("") // keep import
