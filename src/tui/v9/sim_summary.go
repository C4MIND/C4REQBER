// Package tui — sim helpers.
// Functions that synthesize CardSimulation entries from backend data
// that the user should see in the feed as a first-class discovery artifact.

package tui

import (
	"fmt"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// capSummaryCard builds a synthetic CardSimulation that summarizes the
// capabilities report — useful for the user to see in their feed that
// "this machine has N/M sims available" right after pressing Ctrl+Shift+C.
func capSummaryCard(r *capsim.Report) cards.Card {
	ok := 0
	for _, e := range r.Engines {
		if e.Status == capsim.StatusAvailable || e.Status == capsim.StatusSlow {
			ok++
		}
	}
	groups := r.GroupByDomain()
	body := fmt.Sprintf(i18n.T("sim.card.cap_body"), ok, len(r.Engines), len(groups))
	c := cards.Card{
		ID:     cards.NextID(),
		Kind:   cards.KindSimulation,
		Title:  i18n.T("sim.card.cap_title"),
		Body:   body,
		Time:   time.Now(),
		Status: "done",
		Sim: cards.SimFields{
			Engine:       "capsim",
			EngineStatus: "available",
			Domain:       "general",
			Pattern:      "capability_probe",
			Verdict:      "inconclusive",
			ElapsedMS:    int(r.ProbeLatencyMS),
			BackendHost:  r.Platform.System + "/" + r.Platform.Arch,
			Evidence: cards.SimEvidence{
				Type:    "table",
				Caption: fmt.Sprintf(i18n.T("sim.card.cap_evidence"), len(r.Engines)),
			},
		},
	}
	for _, g := range groups {
		c.Sim.PatternsTried = append(c.Sim.PatternsTried, cards.PatternTry{
			Engine: string(g.Domain),
			Status: fmt.Sprintf(i18n.T("sim.card.domain_engines"), len(g.Engines)),
		})
	}
	return c
}

// capUnavailableCards emits a per-engine CardSimulation with status=unavailable
// for every engine that the user can install.
func capUnavailableCards(r *capsim.Report, maxPerReport int) []cards.Card {
	if maxPerReport <= 0 {
		maxPerReport = 6
	}
	var out []cards.Card
	for i, e := range r.Engines {
		if e.Status != capsim.StatusUnavailable {
			continue
		}
		if len(out) >= maxPerReport {
			break
		}
		reason := e.MissingReason
		if reason == "" {
			reason = i18n.T("sim.card.reason_default")
		}
		out = append(out, cards.Card{
			ID:     cards.NextID(),
			Kind:   cards.KindSimulation,
			Title:  fmt.Sprintf(i18n.T("sim.card.engine_unavailable"), e.ID),
			Body:   e.Name + " · " + reason,
			Time:   time.Now().Add(time.Duration(i) * time.Millisecond),
			Meta:   []cards.MetaKV{{Key: "domain", Value: string(e.Domain)}, {Key: "tier", Value: e.Tier}},
			Status: "error",
			Sim: cards.SimFields{
				Engine:        e.ID,
				EngineTier:    e.Tier,
				EngineStatus:  "unavailable",
				Domain:        string(e.Domain),
				Pattern:       "capability_check",
				Verdict:       "inconclusive",
				InstallHint:   e.InstallHint,
				PatternsTried: []cards.PatternTry{{Engine: e.ID, Status: "unavailable", Reason: reason}},
			},
		})
	}
	return out
}
