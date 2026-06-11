// Package tui — status bar (1-line, between footer and feed).
// Per §3.3 of the unified plan, shows:
//   - connection state (● green = SSE, ◐ yellow = polling, ○ red = offline)
//   - follow mode (▶ following / ⏸ paused)
//   - focused card N / total
//   - sims-this-run count (◆ N)
//   - capabilities summary (⏚ X/Y engines)
//
// Visible by default at T2+ tier (width >= 140, height >= 35).
// Toggle with Ctrl+B (ActStatusBar).
package tui

import (
	"fmt"
	"strings"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
)

// ConnectionState is the live state of the SSE/polling pipeline.
type ConnectionState int

const (
	ConnUnknown ConnectionState = iota // initial
	ConnLive                          // SSE stream open, events flowing
	ConnPolling                       // SSE failed, polling fallback active
	ConnOffline                       // both failed for > 30s
)

// ConnGlyph returns the user-facing icon for a connection state.
func ConnGlyph(c ConnectionState) string {
	switch c {
	case ConnLive:
		return "●"
	case ConnPolling:
		return "◐"
	case ConnOffline:
		return "○"
	}
	return "?"
}

// ConnLabel returns a human-readable state name.
func ConnLabel(c ConnectionState) string {
	switch c {
	case ConnLive:
		return "live"
	case ConnPolling:
		return "polling"
	case ConnOffline:
		return "offline"
	}
	return "?"
}

// renderStatusBar renders the 1-line status bar.
// Returns empty string if the terminal is too small (T0/T1) or the user
// toggled it off (m.showStatusBar == false).
func (m *model) renderStatusBar() string {
	if !m.showStatusBar {
		return ""
	}
	if m.width < 100 {
		// T0/T1 — too narrow; status bar would crowd the footer
		return ""
	}

	var parts []string

	// 1. Connection
	connStr := ConnGlyph(m.connState) + " " + ConnLabel(m.connState)
	connStyled := lipgloss.NewStyle().Foreground(lipgloss.Color(connColor(m.connState))).Render(connStr)
	parts = append(parts, connStyled)

	// 2. Follow mode
	followIcon := "▶"
	followLabel := "follow"
	if !m.follow {
		followIcon = "⏸"
		followLabel = "paused"
	}
	parts = append(parts, followIcon+" "+followLabel)

	// 3. Focused card N / total
	if len(m.feed) > 0 {
		idx := m.focusedCardIdx
		if idx < 0 {
			idx = len(m.feed) - 1
		}
		parts = append(parts, fmt.Sprintf("▣ %d/%d", idx+1, len(m.feed)))
	}

	// 4. Sims-this-run count
	if m.simCountThisRun > 0 {
		parts = append(parts, fmt.Sprintf("◆ %d sims", m.simCountThisRun))
	}

	// 5. Capabilities summary
	if m.capsimReport != nil {
		parts = append(parts, capsim.ShortSummary(m.capsimReport))
	}

	// Join with " · " and pad to width
	line := strings.Join(parts, "  ·  ")
	lineStyled := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(line)
	// Right-align: pad with spaces
	pad := m.width - len([]rune(lineStyled))
	if pad < 0 {
		// Truncate gracefully
		runes := []rune(lineStyled)
		lineStyled = string(runes[:m.width])
	} else {
		lineStyled = strings.Repeat(" ", pad) + lineStyled
	}
	return lineStyled
}

// connColor returns the lipgloss color code for a connection state.
func connColor(c ConnectionState) string {
	switch c {
	case ConnLive:
		return "2" // green
	case ConnPolling:
		return "3" // yellow
	case ConnOffline:
		return "1" // red
	}
	return "8" // dim
}
