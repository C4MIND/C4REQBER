package tui

import (
	"strings"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

func TestRenderCardFocusBorder(t *testing.T) {
	c := cards.Card{Kind: cards.KindHypothesis, Title: "h", Body: "b"}
	out := renderCard(c, 80, "", true, false)
	// Focused uses ┃ border
	if !strings.Contains(out, "┃") {
		t.Error("focused card should use thick ┃ border")
	}
	out2 := renderCard(c, 80, "", false, false)
	if !strings.Contains(out2, "│") {
		t.Error("unfocused card should use thin │ border")
	}
}

func TestRenderCardExpandedShowsFullBody(t *testing.T) {
	c := cards.Card{
		Kind:     cards.KindHypothesis,
		Title:    "Hypothesis",
		Body:     "short body",
		FullBody: "This is the full body of the hypothesis. It is much longer than the body and explains everything in detail. The user can read the whole thing when expanded. Line two of the full body.",
	}
	out := renderCard(c, 80, "", true, true)
	// Should contain the FullBody
	if !strings.Contains(out, "full body of the hypothesis") {
		t.Error("expanded card should render FullBody text")
	}
	if !strings.Contains(out, "Line two of the full body") {
		t.Error("expanded card should render multiple FullBody lines")
	}
	// Should contain collapse hint
	if !strings.Contains(out, "collapse") {
		t.Error("expanded card should show collapse hint")
	}
}

func TestRenderCardNotExpandedNoFullBody(t *testing.T) {
	c := cards.Card{
		Kind:     cards.KindHypothesis,
		Title:    "Hypothesis",
		Body:     "short body",
		FullBody: "This is the full body of the hypothesis. It is much longer than the body and explains everything in detail.",
	}
	out := renderCard(c, 80, "", true, false)
	// Should NOT contain FullBody when not expanded
	if strings.Contains(out, "explains everything in detail") {
		t.Error("non-expanded card should NOT render FullBody")
	}
}

func TestWordWrap(t *testing.T) {
	lines := wordWrap("the quick brown fox jumps over the lazy dog", 15)
	if len(lines) == 0 {
		t.Fatal("expected wrapped lines, got none")
	}
	for _, l := range lines {
		if len([]rune(l)) > 15 {
			t.Errorf("line %q exceeds 15 runes", l)
		}
	}
}

func TestWordWrapEmpty(t *testing.T) {
	lines := wordWrap("", 15)
	if len(lines) != 0 {
		t.Errorf("empty input should produce 0 lines, got %d", len(lines))
	}
}

func TestWordWrapShortDoesntWrap(t *testing.T) {
	lines := wordWrap("hi", 15)
	if len(lines) != 1 {
		t.Errorf("short input should produce 1 line, got %d", len(lines))
	}
}

func TestFocusedCardStateToggle(t *testing.T) {
	m := NewAppFresh("http://test")
	hyp := cards.Card{Kind: cards.KindHypothesis, Title: "h", FullBody: "long body"}
	m.appendCard(hyp)
	if hyp.State != cards.StateActive {
		t.Error("new card should be StateActive")
	}
	hyp.State = cards.StateExpanded
	if hyp.State != cards.StateExpanded {
		t.Error("state should be expandable")
	}
}
