package tui

import (
	"strings"
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// renderToString renders a model's View to a cleaned string.
func renderToString(t *testing.T, m *model) string {
	t.Helper()
	if m.width == 0 {
		m.width = 120
	}
	if m.height == 0 {
		m.height = 40
	}
	m.layout()
	view := stripANSI(m.View().Content)
	return view
}

func TestGoldenEmptyState_EN(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	out := renderToString(t, m)
	// Must contain key UI strings
	mustContain := []string{
		"C4REQBER v9",      // header
		"Ready for your first", // empty title
		"DeepSeek",          // header
		"READY",             // footer
		"DISCOVER",          // mode
	}
	for _, s := range mustContain {
		if !strings.Contains(out, s) {
			t.Errorf("missing %q in:\n%s", s, out)
		}
	}
}

func TestGoldenEmptyState_RU(t *testing.T) {
	defer SetLang(i18n.LangEN)
	SetLang(i18n.LangRU)
	m := NewApp("http://test")
	out := renderToString(t, m)
	if !strings.Contains(out, "Готов к первому") {
		t.Errorf("missing RU empty title in:\n%s", out)
	}
	if !strings.Contains(out, "RU") {
		t.Errorf("missing RU label in:\n%s", out)
	}
}

func TestGoldenEmptyState_ZH(t *testing.T) {
	defer SetLang(i18n.LangEN)
	SetLang(i18n.LangZH)
	m := NewApp("http://test")
	out := renderToString(t, m)
	if !strings.Contains(out, "准备进行首次") {
		t.Errorf("missing ZH empty title in:\n%s", out)
	}
}

func TestGoldenEmptyState_AR(t *testing.T) {
	defer SetLang(i18n.LangEN)
	SetLang(i18n.LangAR)
	m := NewApp("http://test")
	out := renderToString(t, m)
	// Arabic is RTL — text might be reversed in display
	if !strings.Contains(out, "AR") {
		t.Errorf("missing AR label in:\n%s", out)
	}
}

func TestGoldenWithPhaseCard(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	m.appendCard(Card{
		Kind:     CardPhase,
		Title:    "B: Knowledge acquisition",
		Body:     "12 sources fired",
		Time:     time.Now(),
		Status:   "running",
		Progress: 0.45,
	})
	// The card's content is rendered into the viewport, but viewport only shows visible area.
	// Check that the renderCard output contains the expected strings.
	cardStr := renderCard(m.feed[1], 120)
	if !strings.Contains(cardStr, "Knowledge") {
		t.Errorf("phase card body not in renderCard output:\n%s", cardStr)
	}
	if !strings.Contains(cardStr, "45%") {
		t.Errorf("progress not in renderCard output:\n%s", cardStr)
	}
}

func TestGoldenWithHypothesisCard(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	m.appendCard(Card{
		Kind:  CardHypothesis,
		Title: "Hypothesis",
		Body:  "Use truncated 17-nt guide RNAs with NGG PAM to reduce off-target binding in T-cells.",
		Meta:  []string{"confidence 0.87", "derived from: 3 papers"},
		Time:  time.Now(),
		Status: "done",
	})
	out := renderToString(t, m)
	if !strings.Contains(out, "truncated 17-nt") {
		t.Errorf("hypothesis body not in feed:\n%s", out)
	}
}

func TestGoldenWithErrorCard(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	m.appendCard(Card{
		Kind:  CardError,
		Title: "Submit failed",
		Body:  "connection refused",
		Time:  time.Now(),
		Status: "error",
	})
	out := renderToString(t, m)
	if !strings.Contains(out, "Submit failed") {
		t.Errorf("error card not in feed:\n%s", out)
	}
}

func TestGoldenWidthNarrow(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	m.width = 60
	m.height = 24
	out := renderToString(t, m)
	// Should still render even in narrow mode
	if !strings.Contains(out, "C4REQBER v9") {
		t.Error("header missing in narrow mode")
	}
}

func TestGoldenWidthVeryNarrow(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	m.width = 30
	m.height = 12
	out := renderToString(t, m)
	// Should not panic
	if !strings.Contains(out, "C4REQBER v9") {
		t.Error("header missing in very narrow mode")
	}
}

func TestGoldenAchievementCard(t *testing.T) {
	SetLang(i18n.LangEN)
	defer SetLang(i18n.LangEN)
	m := NewApp("http://test")
	m.completedDisc = 1
	m.checkAchievements()
	out := renderToString(t, m)
	if !strings.Contains(out, "First") && !strings.Contains(out, "achievement") {
		t.Errorf("achievement card not in feed:\n%s", out)
	}
}
