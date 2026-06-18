// Package tui — verdict chips on hypothesis cards.
// Per D-06 of the unified plan, when one or more CardSimulation entries
// have HypothesisID == c.ID for a CardHypothesis c, render a verdict chip
// strip above the body summarizing the evidence.

package tui

import (
	"fmt"
	"strings"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

// verdictChips returns the chip-row to render above the body of a
// CardHypothesis, summarizing the CardSimulation entries that reference it.
// Returns empty string if no linked sims exist.
func verdictChips(m *model, hypID cards.ID) string {
	if hypID == 0 {
		return ""
	}
	var supports, refutes, inconclusive int
	var lastEngine string
	for _, c := range m.feed {
		if c.Kind != cards.KindSimulation {
			continue
		}
		if c.Sim.HypothesisID != hypID {
			continue
		}
		lastEngine = c.Sim.Engine
		switch c.Sim.Verdict {
		case "supports_hypothesis":
			supports++
		case "refutes_hypothesis":
			refutes++
		case "inconclusive":
			inconclusive++
		}
	}
	if supports+refutes+inconclusive == 0 {
		return ""
	}
	var parts []string
	if supports > 0 {
		parts = append(parts, lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("2")).Render(
			fmt.Sprintf("◆✓ %d/%d supported", supports, supports+refutes+inconclusive)))
	}
	if refutes > 0 {
		parts = append(parts, lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("1")).Render(
			fmt.Sprintf("◆✗ %d refuted", refutes)))
	}
	if inconclusive > 0 && supports+refutes == 0 {
		parts = append(parts, lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Render(
			fmt.Sprintf("◆? %d inconclusive", inconclusive)))
	}
	row := strings.Join(parts, "  ")
	if lastEngine != "" {
		row += lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render("  · via " + lastEngine)
	}
	return row
}
