// Package capsim — capabilities overlay (Ctrl+Shift+C).
// Renders the TUI fullscreen view of all simulation/verification engines
// for the current machine, with per-engine status icons and install hints.
package capsim

import (
	"fmt"
	"strings"

	"charm.land/lipgloss/v2"
)

// statusColor returns the lipgloss color name for a status icon.
func statusColor(s EngineStatus) string {
	switch s {
	case StatusAvailable:
		return "2" // green
	case StatusSlow:
		return "3" // yellow
	case StatusUnavailable:
		return "1" // red
	case StatusBudget:
		return "1" // red
	case StatusDelegated:
		return "6" // cyan
	}
	return "8" // dim
}

// statusGlyph returns the leading icon for a row.
func statusGlyph(s EngineStatus) string {
	switch s {
	case StatusAvailable:
		return "●"
	case StatusSlow:
		return "◐"
	case StatusUnavailable:
		return "○"
	case StatusBudget:
		return "⊘"
	case StatusDelegated:
		return "☁"
	}
	return "?"
}

// RenderCapabilitiesOverlay produces a full-screen capabilities view.
// width and height are terminal dimensions; report is the data from
// Client.Get (may be empty if backend was unreachable).
func RenderCapabilitiesOverlay(width, height int, report *Report) string {
	if report == nil {
		report = Fallback()
	}
	if width < 60 {
		width = 60
	}
	if height < 20 {
		height = 20
	}

	var b strings.Builder
	// Title bar
	title := "⏚ Simulation Capabilities (this Mac)"
	if report.Platform.System != "" {
		title = "⏚ Simulation Capabilities (" + report.Platform.System + " " + report.Platform.Arch + ")"
	}
	titleStyled := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6")).Render(title)
	b.WriteString(titleStyled)
	b.WriteString("\n")
	// Hardware summary
	hwLine := fmt.Sprintf("GPU: %s · %.1f GB · %d CPUs · %.0f GB RAM",
		report.Hardware.GPUName, report.Hardware.GPUMemoryGB, report.Hardware.CPUCount, report.Hardware.RAMGB)
	b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(hwLine))
	b.WriteString("\n\n")

	// Group by domain
	groups := report.GroupByDomain()
	if len(groups) == 0 {
		b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Render("  No capabilities report — backend may be unreachable."))
		b.WriteString("\n")
	} else {
		for _, g := range groups {
			// Domain header
			domainHeader := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("  " + string(g.Domain))
			b.WriteString(domainHeader)
			b.WriteString("\n")
			// One row per engine
			for _, eid := range g.Engines {
				eng := report.ByID(eid)
				if eng == nil {
					continue
				}
				row := formatEngineRow(*eng, width)
				b.WriteString(row)
				b.WriteString("\n")
				// Install hint on the next line if unavailable
				if eng.Status == StatusUnavailable && eng.InstallHint != "" {
					hint := "      ⓘ " + eng.InstallHint
					b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(hint))
					b.WriteString("\n")
				}
			}
			b.WriteString("\n")
		}
	}

	// Verifiers section
	if len(report.Verifiers) > 0 {
		b.WriteString(lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("  ── Verification ──"))
		b.WriteString("\n")
		for _, v := range report.Verifiers {
			icon := "○"
			if v.Available {
				icon = "●"
			}
			ver := v.Version
			if ver != "" {
				ver = " (" + ver + ")"
			}
			row := fmt.Sprintf("  %s %s%s", icon, v.ID, ver)
			b.WriteString(row)
			b.WriteString("\n")
		}
		b.WriteString("\n")
	}

	// Footer
	probeLine := fmt.Sprintf("  Last probe: %s (%dms) · Ctrl+R to refresh · Esc to close",
		report.ProbeTimestamp.Format("15:04:05"), report.ProbeLatencyMS)
	b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(probeLine))

	// Pad to fill the screen
	rendered := b.String()
	lines := strings.Split(rendered, "\n")
	for len(lines) < height {
		lines = append(lines, "")
	}
	if len(lines) > height {
		lines = lines[:height]
	}
	return strings.Join(lines, "\n")
}

// formatEngineRow produces one line for one engine in the overlay.
func formatEngineRow(e Engine, width int) string {
	icon := statusGlyph(e.Status)
	iconStyled := lipgloss.NewStyle().Foreground(lipgloss.Color(statusColor(e.Status))).Render(icon)
	indent := "    "
	name := fmt.Sprintf("%-16s", e.Name)
	tier := ""
	switch e.Tier {
	case "fast":
		tier = " (fast)"
	case "slow":
		tier = " (CPU)"
	case "linux_only":
		tier = " (linux only)"
	case "cloud":
		tier = " (cloud)"
	}
	row := indent + iconStyled + " " + name + tier
	if e.Status == StatusUnavailable {
		row = indent + iconStyled + " " + name + lipgloss.NewStyle().Foreground(lipgloss.Color("1")).Render(" (unavailable)")
	}
	return row
}

// ShortSummary returns a 1-line summary for the status bar (e.g. "23/32 engines OK").
func ShortSummary(r *Report) string {
	if r == nil {
		return ""
	}
	ok := 0
	for _, e := range r.Engines {
		if e.Status == StatusAvailable || e.Status == StatusSlow {
			ok++
		}
	}
	return fmt.Sprintf("⏚ %d/%d engines", ok, len(r.Engines))
}
