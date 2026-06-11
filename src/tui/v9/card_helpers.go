package tui

import (
	"fmt"
	"os/exec"
	"runtime"
	"strings"

	"github.com/figuramax/c4reqber-tui-v9/cards"
)

// cardToMarkdown renders a Card as a markdown document.
// Used by the `c` (copy) action so the user gets clean text in clipboard.
// CardSimulation gets a structured header (engine + verdict) per the plan.
func cardToMarkdown(c cards.Card) string {
	var b strings.Builder
	fmt.Fprintf(&b, "# %s\n\n", c.Title)
	if c.Body != "" {
		fmt.Fprintf(&b, "%s\n\n", c.Body)
	}
	if c.Kind == cards.KindSimulation {
		fmt.Fprintf(&b, "*Engine:* %s · *Status:* %s · *Pattern:* %s · *Domain:* %s\n",
			c.Sim.Engine, c.Sim.EngineStatus, c.Sim.Pattern, c.Sim.Domain)
		if c.Sim.Verdict != "" {
			fmt.Fprintf(&b, "*Verdict:* %s\n", c.Sim.Verdict)
		}
		if c.Sim.CostUSD > 0 {
			fmt.Fprintf(&b, "*Cost:* $%.4f\n", c.Sim.CostUSD)
		}
		if len(c.Sim.PatternsTried) > 0 {
			fmt.Fprintf(&b, "\n*Fallback chain:*\n")
			for _, t := range c.Sim.PatternsTried {
				fmt.Fprintf(&b, "- %s (%s)\n", t.Engine, t.Status)
			}
		}
	}
	if len(c.Meta) > 0 {
		fmt.Fprintf(&b, "\n*Metadata:*\n")
		for _, m := range c.Meta {
			fmt.Fprintf(&b, "- %s: %s\n", m.Key, m.Value)
		}
	}
	fmt.Fprintf(&b, "\n*Time:* %s\n", c.Time.Format("2006-01-02 15:04:05"))
	return b.String()
}

// truncate shortens s to max runes with an ellipsis if it was longer.
func truncate(s string, maxRunes int) string {
	if maxRunes <= 0 {
		return ""
	}
	runes := []rune(s)
	if len(runes) <= maxRunes {
		return s
	}
	if maxRunes <= 1 {
		return "…"
	}
	return string(runes[:maxRunes-1]) + "…"
}

// openURL opens a URL in the OS default browser.
// macOS:   open
// Linux:   xdg-open
// Windows: rundll32 url.dll,FileProtocolHandler
// Returns nil on platforms that have no known opener.
func openURL(u string) error {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", u)
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", u)
	default:
		cmd = exec.Command("xdg-open", u)
	}
	return cmd.Start()
}
