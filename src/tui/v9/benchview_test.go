package tui

import (
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

// BenchmarkView_FullFeed benchmarks the 60fps View() function with
// a realistic feed (50 cards, mixed kinds). Tells us if there are
// hot allocations in the rendering path.
//
// 312µs/op at 50 cards (~1.9% of a 16.67ms frame budget at 60fps).
// Largest single allocation: bubblezone.(*scanner).emit (34%) which
// is third-party. Our own code is dominated by strings.Builder
// growth in rebuildFeedContent (18%) and the lipgloss.Style allocs
// in renderCard (per-kind title/body styles).
func BenchmarkView_FullFeed(b *testing.B) {
	m := NewAppFresh("http://test")
	m.width, m.height = 160, 40
	for i := 0; i < 10; i++ {
		m.appendCard(cards.Card{Kind: cards.KindPhase, Title: "phase", Status: "done", Time: time.Now()})
	}
	for i := 0; i < 20; i++ {
		m.appendCard(cards.Card{Kind: cards.KindPaper, Title: "paper", Body: "body", Time: time.Now()})
	}
	for i := 0; i < 15; i++ {
		m.appendCard(cards.Card{Kind: cards.KindHypothesis, Title: "hyp", Body: "body", Time: time.Now()})
	}
	for i := 0; i < 5; i++ {
		m.appendCard(cards.Card{Kind: cards.KindSimulation, Title: "sim", Time: time.Now(),
			Sim: cards.SimFields{Engine: "newton", EngineStatus: "success", Verdict: "supports_hypothesis"}})
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = m.View()
	}
}
