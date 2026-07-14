// Package tui — debug overlay (§15).
// Toggled with Ctrl+Shift+D (ActDebug) or ':debug' in the command palette.
// Shows the live state of the TUI for debugging: connection state,
// tick rate, last SSE event, feed stats, sim stats, memory estimate.
// Pure function — takes a snapshot struct so it's testable.

package tui

import (
	"fmt"
	"strings"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
)

// DebugSnapshot is the data needed to render the debug overlay.
// Produced by (m *model).debugSnapshot() and passed to RenderDebugOverlay
// for pure-function rendering.
type DebugSnapshot struct {
	Width         int
	Height        int
	Tick          int
	TickRate      int           // target 60 fps, actual measured
	Connection    string        // "live" / "polling" / "offline" / "unknown"
	LastSSEType   string        // last SSE event type
	LastSSETS     time.Time     // timestamp of last SSE event
	FeedLen       int
	ZoneIDs       int
	Bookmarks     int
	SimCountRun   int
	SimCountTotal int           // total CardSimulation in feed
	SimCost       float64
	SimCapabilitySummary string  // "⏚ X/Y engines" or empty
	Follow        bool
	Focused       int          // -1 = none
	MemoryEst     string        // "feed × ~200 bytes"
	Toast         string
}

// CollectDebugSnapshot builds a snapshot from the live model.
func (m *model) CollectDebugSnapshot() DebugSnapshot {
	connStr := ConnLabel(m.connState)
	lastType := ""
	lastTS := time.Time{}
	if m.lastPhase != "" {
		lastType = "phase (legacy v8.12)"
	}
	bookmarks := 0
	simsTotal := 0
	for _, c := range m.feed {
		if c.Bookmark {
			bookmarks++
		}
		if c.Kind == CardSimulation {
			simsTotal++
		}
	}
	return DebugSnapshot{
		Width:                m.width,
		Height:               m.height,
		Tick:                 m.tick,
		TickRate:             60, // Bubble Tea runs at ~60fps by default
		Connection:           connStr,
		LastSSEType:          lastType,
		LastSSETS:            lastTS,
		FeedLen:              len(m.feed),
		ZoneIDs:              len(m.zoneIDs),
		Bookmarks:            bookmarks,
		SimCountRun:          m.simCountThisRun,
		SimCountTotal:        simsTotal,
		SimCost:              m.simSpendThisSession,
		SimCapabilitySummary: capsim.ShortSummary(m.capsimReport),
		Follow:               m.follow,
		Focused:              m.focusedCardIdx,
		MemoryEst:            fmt.Sprintf("~%d KB", (len(m.feed)*200)/1024),
		Toast:                m.toast,
	}
}

// RenderDebugOverlay produces the fullscreen debug view.
func RenderDebugOverlay(snap DebugSnapshot) string {
	var b strings.Builder

	b.WriteString("🔧 Debug Overlay (Ctrl+Shift+D to close)\n\n")

	b.WriteString("Viewport\n")
	b.WriteString(fmt.Sprintf("  size:     %d × %d\n", snap.Width, snap.Height))
	b.WriteString(fmt.Sprintf("  tick:     %d  (target rate %d fps)\n", snap.Tick, snap.TickRate))
	b.WriteString("\n")

	b.WriteString("Connection\n")
	b.WriteString(fmt.Sprintf("  state:    %s\n", snap.Connection))
	if snap.LastSSEType != "" {
		b.WriteString(fmt.Sprintf("  last:     %s @ %s\n", snap.LastSSEType, snap.LastSSETS.Format("15:04:05")))
	} else {
		b.WriteString("  last:     (none this session)\n")
	}
	b.WriteString("\n")

	b.WriteString("Feed\n")
	b.WriteString(fmt.Sprintf("  cards:    %d  (bookmarks: %d)\n", snap.FeedLen, snap.Bookmarks))
	b.WriteString(fmt.Sprintf("  zones:    %d\n", snap.ZoneIDs))
	follow := "▶ following"
	if !snap.Follow {
		follow = "⏸ paused"
	}
	b.WriteString(fmt.Sprintf("  mode:     %s\n", follow))
	if snap.Focused >= 0 {
		b.WriteString(fmt.Sprintf("  focused:  card #%d\n", snap.Focused+1))
	} else {
		b.WriteString("  focused:  (last card)\n")
	}
	b.WriteString("\n")

	b.WriteString("Sims\n")
	b.WriteString(fmt.Sprintf("  this run: %d\n", snap.SimCountRun))
	b.WriteString(fmt.Sprintf("  total:    %d CardSimulation in feed\n", snap.SimCountTotal))
	b.WriteString(fmt.Sprintf("  cost:     $%.4f (this session)\n", snap.SimCost))
	if snap.SimCapabilitySummary != "" {
		b.WriteString(fmt.Sprintf("  caps:     %s\n", snap.SimCapabilitySummary))
	}
	b.WriteString("\n")

	b.WriteString("Memory\n")
	b.WriteString(fmt.Sprintf("  est:      %s (feed × ~200 bytes/card)\n", snap.MemoryEst))
	b.WriteString("\n")

	if snap.Toast != "" {
		b.WriteString(fmt.Sprintf("Toast: %s\n", snap.Toast))
	}

	return b.String()
}
