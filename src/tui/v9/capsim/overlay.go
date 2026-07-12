// Package capsim — capabilities overlay (Ctrl+Shift+C).
// Renders the TUI fullscreen view of all simulation/verification engines
// for the current machine, with per-engine status icons and install hints.
package capsim

import (
	"fmt"
	"strings"

	"charm.land/lipgloss/v2"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
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
	title := "⏚ " + i18n.T("sim.overlay.title")
	if report.Platform.System != "" {
		title = "⏚ " + fmt.Sprintf(i18n.T("sim.overlay.title_platform"), report.Platform.System, report.Platform.Arch)
	}
	titleStyled := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6")).Render(title)
	b.WriteString(titleStyled)
	b.WriteString("\n")
	hwLine := fmt.Sprintf("GPU: %s · %.1f GB · %d CPUs · %.0f GB RAM",
		report.Hardware.GPUName, report.Hardware.GPUMemoryGB, report.Hardware.CPUCount, report.Hardware.RAMGB)
	b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(hwLine))
	b.WriteString("\n\n")

	groups := report.GroupByDomain()
	if len(groups) == 0 {
		b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Render("  " + i18n.T("sim.overlay.no_report")))
		b.WriteString("\n")
	} else {
		for _, g := range groups {
			domainHeader := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("  " + string(g.Domain))
			b.WriteString(domainHeader)
			b.WriteString("\n")
			for _, eid := range g.Engines {
				eng := report.ByID(eid)
				if eng == nil {
					continue
				}
				row := formatEngineRow(*eng, width)
				b.WriteString(row)
				b.WriteString("\n")
				if eng.Status == StatusUnavailable && eng.InstallHint != "" {
					hint := "      ⓘ " + eng.InstallHint
					b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(hint))
					b.WriteString("\n")
				}
			}
			b.WriteString("\n")
		}
	}

	if len(report.Verifiers) > 0 {
		b.WriteString(lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("4")).Render("  " + i18n.T("sim.overlay.section.verification")))
		b.WriteString("\n")
		for _, v := range report.Verifiers {
			icon := "○"
			if v.Available {
				icon = "●"
			}
			name := v.Name
			if name == "" {
				name = v.ID
			}
			ver := v.Version
			if ver != "" {
				ver = " (" + ver + ")"
			}
			row := fmt.Sprintf("  %s %s%s", icon, name, ver)
			b.WriteString(row)
			b.WriteString("\n")
		}
		b.WriteString("\n")
	}

	probeLine := fmt.Sprintf("  "+i18n.T("sim.overlay.footer"),
		report.ProbeTimestamp.Format("15:04:05"), report.ProbeLatencyMS)
	b.WriteString(lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(probeLine))

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
		tier = " " + i18n.T("sim.overlay.tier.fast")
	case "slow":
		tier = " " + i18n.T("sim.overlay.tier.slow")
	case "linux_only":
		tier = " " + i18n.T("sim.overlay.tier.linux")
	case "cloud":
		tier = " " + i18n.T("sim.overlay.tier.cloud")
	}
	row := indent + iconStyled + " " + name + tier
	if e.Status == StatusUnavailable {
		row = indent + iconStyled + " " + name + lipgloss.NewStyle().Foreground(lipgloss.Color("1")).Render(" "+i18n.T("sim.overlay.unavailable"))
	}
	return row
}

// ShortSummary returns a 1-line summary for the status bar.
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
	line := fmt.Sprintf("⏚ %d/%d %s", ok, len(r.Engines), i18n.T("sim.summary.engines"))
	if len(r.Verifiers) > 0 {
		vok := 0
		for _, v := range r.Verifiers {
			if v.Available {
				vok++
			}
		}
		line += fmt.Sprintf(" · %d/%d %s", vok, len(r.Verifiers), i18n.T("sim.summary.verifiers"))
	}
	return line
}
