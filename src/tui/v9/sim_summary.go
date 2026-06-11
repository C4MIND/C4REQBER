// Package tui — sim helpers.
// Functions that synthesize CardSimulation entries from backend data
// that the user should see in the feed as a first-class discovery artifact.

package tui

import (
	"fmt"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/cards"
)

// capSummaryCard builds a synthetic CardSimulation that summarizes the
// capabilities report — useful for the user to see in their feed that
// "this machine has 22/32 sims available" right after pressing Ctrl+Shift+C.
//
// One CardSimulation per domain with EngineStatus="available" → renders as
// "summary card" via the (Engine="capsim:domain") sentinel. The user sees
// what they have without needing to leave the feed for the overlay.
func capSummaryCard(r *capsim.Report) cards.Card {
	ok := 0
	for _, e := range r.Engines {
		if e.Status == capsim.StatusAvailable || e.Status == capsim.StatusSlow {
			ok++
		}
	}
	groups := r.GroupByDomain()
	body := fmt.Sprintf("%d/%d engines available across %d domains",
		ok, len(r.Engines), len(groups))
	c := cards.Card{
		ID:    cards.NextID(),
		Kind:  cards.KindSimulation,
		Title: "Capabilities probed",
		Body:  body,
		Time:  time.Now(),
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
				Caption: fmt.Sprintf("%d engines probed", len(r.Engines)),
			},
		},
	}
	// Populate the per-domain fallback chain so the user sees
	// "domain X had Y sims" at a glance.
	for _, g := range groups {
		c.Sim.PatternsTried = append(c.Sim.PatternsTried, cards.PatternTry{
			Engine: string(g.Domain),
			Status: fmt.Sprintf("%d engines", len(g.Engines)),
		})
	}
	return c
}

// capUnavailableCard emits a per-engine CardSimulation with status=unavailable
// for every engine that the user can install. Adds one card per missing engine.
// This is the key affordance the plan calls out (D-03): "engine unavailability
// is a first-class state". The user always knows what's missing.
//
// Capped at maxPerReport to avoid flooding the feed on a 32-engine machine.
func capUnavailableCards(r *capsim.Report, maxPerReport int) []cards.Card {
	if maxPerReport <= 0 {
		maxPerReport = 6 // default
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
			reason = "not on this platform"
		}
		out = append(out, cards.Card{
			ID:    cards.NextID(),
			Kind:  cards.KindSimulation,
			Title: "engine " + e.ID + " unavailable",
			Body:  e.Name + " · " + reason,
			Time:  time.Now().Add(time.Duration(i) * time.Millisecond),
			Meta:  []cards.MetaKV{{Key: "domain", Value: string(e.Domain)}, {Key: "tier", Value: e.Tier}},
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
