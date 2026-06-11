// Package tui — Theme: pre-built lipgloss.Style helpers for the active
// color profile. Per §11 of the unified plan, the color profile is
// stored in the model and resolved into styles on demand. v9.13 wires
// the Theme into the header, status bar, and card kind borders so
// changing the color profile actually changes the rendered output.

package tui

import (
	"charm.land/lipgloss/v2"
)

// Theme is a bundle of pre-built lipgloss.Style objects for the active
// color profile. Cached per (profile, kind) tuple by the model.
type Theme struct {
	profile ColorProfile
	colors  colorMap
}

// NewTheme creates a Theme for the given profile.
func NewTheme(p ColorProfile) *Theme {
	return &Theme{profile: p, colors: ColorsFor(p)}
}

// Profile returns the active profile.
func (t *Theme) Profile() ColorProfile { return t.profile }

// Style returns a Style for the given semantic color name.
// Returns an empty Style if the name is unknown (caller can no-op).
func (t *Theme) Style(name string) lipgloss.Style {
	c, ok := t.colors[name]
	if !ok {
		return lipgloss.NewStyle()
	}
	return lipgloss.NewStyle().Foreground(c)
}

// StyleBold returns a bold Style for the given semantic color name.
func (t *Theme) StyleBold(name string) lipgloss.Style {
	return t.Style(name).Bold(true)
}

// StyleFaint returns a faint Style for the given semantic color name.
func (t *Theme) StyleFaint(name string) lipgloss.Style {
	return t.Style(name).Faint(true)
}

// CardKindStyle returns the title color for a card kind under this theme.
// Encodes the rule that Hypothesis=success (green), Paper=info (blue),
// Code=accent (magenta), Error=error (red), Phase=primary (yellow),
// Simulation=highlight (cyan).
func (t *Theme) CardKindStyle(kind CardKind) lipgloss.Style {
	switch kind {
	case CardHypothesis:
		return t.StyleBold("success")
	case CardPaper:
		return t.StyleBold("info")
	case CardCode:
		return t.StyleBold("accent")
	case CardError:
		return t.StyleBold("error")
	case CardPhase:
		return t.StyleBold("primary")
	case CardSimulation:
		return t.StyleBold("highlight")
	default:
		return t.Style("muted")
	}
}

// ConnectionStyle returns the style for a connection state.
func (t *Theme) ConnectionStyle(state ConnectionState) lipgloss.Style {
	switch state {
	case ConnLive:
		return t.StyleBold("success")
	case ConnPolling:
		return t.StyleBold("warn")
	case ConnOffline:
		return t.StyleBold("error")
	default:
		return t.Style("muted")
	}
}
