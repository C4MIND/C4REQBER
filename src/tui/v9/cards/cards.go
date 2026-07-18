// Package cards defines the central card primitive for the v9 feed.
// Refactored from the original model.go embedded Card struct per
// TUI_V9_UNIFIED_PLAN_2026-06-11 §5. Adds stable monotonic IDs,
// the new CardSimulation kind, and engine-aware actions.
package cards

import (
	"sync/atomic"
	"time"
)

// ID is a monotonic card identifier, never reused within a process.
type ID uint64

// NextID atomically increments the global counter and returns the new value.
var nextID uint64

func NextID() ID {
	return ID(atomic.AddUint64(&nextID, 1))
}

// ReserveID advances the process-local allocator past a persisted ID so cards
// appended after session restore cannot collide with restored mouse-zone IDs.
func ReserveID(id ID) {
	target := uint64(id)
	for {
		current := atomic.LoadUint64(&nextID)
		if current >= target {
			return
		}
		if atomic.CompareAndSwapUint64(&nextID, current, target) {
			return
		}
	}
}

// Kind is the card type. CardSimulation is NEW in v9.13 (BE-SIM-01/02).
type Kind int

const (
	KindEmpty Kind = iota
	KindPhase
	KindHypothesis
	KindPaper
	KindCode
	KindError
	KindSimulation // NEW: simulation evidence
)

func (k Kind) String() string {
	switch k {
	case KindEmpty:
		return "empty"
	case KindPhase:
		return "phase"
	case KindHypothesis:
		return "hypothesis"
	case KindPaper:
		return "paper"
	case KindCode:
		return "code"
	case KindError:
		return "error"
	case KindSimulation:
		return "simulation"
	}
	return "unknown"
}

// State is the visual state of one card in the feed.
type State uint8

const (
	StateActive   State = iota // default, just rendered
	StateDone                  // non-current, non-focused
	StateErrored               // body is an error trace
	StateFocused               // user navigated to this card
	StateExpanded              // user pressed Enter; shows FullBody
)

// ActionKind is one action the user can take on a card via a single keypress.
type ActionKind uint8

const (
	ActCopy ActionKind = iota
	ActCopyJSON
	ActOpenDOI
	ActSaveBibTeX
	ActSaveMarkdown
	ActExpand
	ActCollapse
	ActRetry
	ActRerun
	ActYank
	ActBookmark
	ActUnbookmark
	ActViewAbstract
	ActOpenPlot       // NEW: sim card — open generated plot
	ActInstallHint    // NEW: sim card — show conda install line
	ActSelectFallback // NEW: sim card — pick a fallback engine
)

// Action is one row in a card's action strip.
type Action struct {
	Key    string // single key, e.g. "y", "o", "i", "f"
	Label  string // "yank", "open", "install hint", "fallback"
	Kind   ActionKind
	Global bool // if true, key works even when card is not focused
}

// MetaKV is a structured metadata key/value on a card. Replaces the
// previous []string which couldn't carry key/value semantics.
type MetaKV struct {
	Key   string
	Value string
}

// Card is one row in the feed. Replaces the old v9 Card struct.
// Field-by-field migration from the v9 inline Card.
type Card struct {
	ID        ID
	Kind      Kind
	Title     string
	Body      string   // short body (1-3 lines)
	FullBody  string   // long body, only shown when expanded
	Meta      []MetaKV // structured metadata
	Actions   []Action // keymap hints, engine-aware
	Time      time.Time
	Progress  float64
	Status    string
	State     State
	Bookmark  bool
	ExpiresAt time.Time
	ZoneID    string // bubblezone ID for mouse clicks

	// Sim-specific fields (D-01). All zero-values for non-simulation cards.
	Sim SimFields
}

// SimFields carries the structured simulation evidence for a CardSimulation.
// Kept in a sub-struct so non-sim cards have a zero-cost Sim{} default.
type SimFields struct {
	Engine        string // "openmm", "fenicsx", "newton", …
	EngineTier    string // "fast" | "slow" | "linux_only" | "unavailable"
	EngineStatus  string // "available" | "skipped" | "unavailable" | "delegated" | "budget_exceeded"
	Domain        string // "biology", "physics", …
	Pattern       string // "protein_folding"
	PatternsTried []PatternTry
	Evidence      SimEvidence
	Verdict       string // "supports_hypothesis" | "refutes_hypothesis" | "inconclusive" | ""
	InstallHint   string // conda install line, if engine unavailable
	CostUSD       float64
	BackendHost   string // "local" | "vastai:instance-12345"
	ElapsedMS     int
	HypothesisID  ID // back-link to the CardHypothesis this evidence is for
}

// PatternTry records one attempt in the fallback chain.
type PatternTry struct {
	Engine    string
	Status    string // "available" | "skipped" | "failed"
	Reason    string // if skipped/failed
	ElapsedMS int
}

// SimEvidence is the structured output of a sim. The TUI renders different
// shapes depending on Type.
type SimEvidence struct {
	Type     string // "scalar" | "series" | "image" | "verdict" | "table"
	Value    any    // float64, []float64, "https://...", or a 2D [][]any
	Unit     string // "kcal/mol", "mV", "ms"
	Caption  string
	ImageURL string // for plots
}

// DefaultActionsFor returns the action set for a card kind, per §5.3 of the plan.
func DefaultActionsFor(k Kind) []Action {
	switch k {
	case KindHypothesis:
		return []Action{
			{Key: "y", Label: "yank", Kind: ActYank},
			{Key: "e", Label: "expand", Kind: ActExpand},
			{Key: "r", Label: "rerun", Kind: ActRerun},
			{Key: "s", Label: "save", Kind: ActSaveMarkdown},
			{Key: "b", Label: "bookmark", Kind: ActBookmark},
		}
	case KindPaper:
		return []Action{
			{Key: "y", Label: "yank", Kind: ActYank},
			{Key: "o", Label: "open", Kind: ActOpenDOI},
			{Key: "a", Label: "abstract", Kind: ActViewAbstract},
			{Key: "s", Label: "bibtex", Kind: ActSaveBibTeX},
			{Key: "b", Label: "bookmark", Kind: ActBookmark},
		}
	case KindCode:
		return []Action{
			{Key: "y", Label: "yank", Kind: ActYank},
			{Key: "o", Label: "open", Kind: ActOpenDOI}, // $EDITOR for code
			{Key: "e", Label: "expand", Kind: ActExpand},
		}
	case KindSimulation:
		// Per §23.6 — engine-aware actions are computed in render-time;
		// here we return the always-available ones. Engine-specific ones
		// (install hint, fallback, open plot) are appended by the renderer
		// based on Sim.EngineStatus.
		return []Action{
			{Key: "y", Label: "yank", Kind: ActYank},
			{Key: "e", Label: "expand", Kind: ActExpand},
			{Key: "b", Label: "bookmark", Kind: ActBookmark},
		}
	case KindError:
		return []Action{
			{Key: "r", Label: "retry", Kind: ActRetry},
			{Key: "e", Label: "trace", Kind: ActExpand},
			{Key: "c", Label: "copy", Kind: ActCopy},
		}
	}
	return nil
}

// ActionsFor returns the actions, augmenting with engine-aware ones for sim cards.
func ActionsFor(c Card) []Action {
	actions := c.Actions
	if len(actions) == 0 {
		actions = DefaultActionsFor(c.Kind)
	}
	if c.Kind != KindSimulation {
		return actions
	}
	// Per §23.6: action set depends on EngineStatus.
	switch c.Sim.EngineStatus {
	case "available", "success":
		if c.Sim.Evidence.Type == "image" && c.Sim.Evidence.ImageURL != "" {
			actions = append(actions, Action{Key: "o", Label: "open plot", Kind: ActOpenPlot})
		}
	case "skipped", "failed":
		actions = append(actions, Action{Key: "f", Label: "fallback", Kind: ActSelectFallback})
	case "unavailable":
		actions = append(actions, Action{Key: "i", Label: "install", Kind: ActInstallHint})
	case "budget_exceeded":
		// no extra — settings page is the resolution path
	}
	return actions
}

// VerdictIcon returns the user-facing glyph for a sim verdict.
func VerdictIcon(v string) string {
	switch v {
	case "supports_hypothesis":
		return "◆✓"
	case "refutes_hypothesis":
		return "◆✗"
	case "inconclusive":
		return "◆?"
	}
	return ""
}

// StatusIcon returns the user-facing glyph for a sim status.
func StatusIcon(s string) string {
	switch s {
	case "available", "success":
		return "●"
	case "partial", "stub", "slow":
		return "◐"
	case "unavailable", "error", "failed":
		return "○"
	case "skipped":
		return "◌"
	case "budget_exceeded":
		return "⊘"
	case "delegated", "delegated_to_cloud":
		return "☁"
	}
	return "?"
}
