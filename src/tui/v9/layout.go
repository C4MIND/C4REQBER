// Package tui — adaptive layout engine.
// Per §4 of the unified plan: 4 tiers (T0/T1/T2/T3) based on terminal size.
// Replaces the inline m.layout() math in view.go with a real Layout struct
// that holds the regions. View() reads these regions when rendering.
package tui

// Tier is the adaptive layout tier.
type Tier int

const (
	TierMinimal   Tier = 0 // 60-99 × 18-23  — tmux pane, headless
	TierCompact   Tier = 1 // 100-139 × 24-34 — 13" laptop
	TierStandard  Tier = 2 // 140-199 × 35-49 — 14-16" laptop, FHD
	TierSpacious  Tier = 3 // 200+ × 50+     — 4K, ultrawide
)

// Layout holds the computed regions for one frame.
type Layout struct {
	Tier        Tier
	Width       int
	Height      int
	Header      Region // 1 row
	Feed        Region // the middle
	Input       Region // 3 rows (T1+), 1 row (T0)
	Footer      Region // 2 rows (T2+), 1 row (T1/T0)
	StatusBar   Region // 0 rows (T0/T1), 1 row (T2+ when toggled)
	RightRail   Region // 0 cols (T0/T1/T2), 32 cols (T3)
	HasRightRail bool
	IsCompact    bool
}

// Region is a terminal-coords rectangle.
type Region struct {
	X, Y, W, H int
}

// ComputeLayout decides the tier and computes regions.
// Pure function — no model state, fully testable.
func ComputeLayout(width, height int, showStatusBar bool) Layout {
	l := Layout{Width: width, Height: height}

	// Tier from width
	switch {
	case width < 100:
		l.Tier = TierMinimal
	case width < 140:
		l.Tier = TierCompact
	case width < 200:
		l.Tier = TierStandard
	default:
		l.Tier = TierSpacious
	}
	// Height demotion
	if height < 24 && l.Tier > TierCompact {
		l.Tier = TierCompact
	}
	if height < 18 {
		l.Tier = TierMinimal
	}

	// Header (always 1 row)
	l.Header = Region{0, 0, width, 1}

	// Right rail (T3 only)
	if l.Tier == TierSpacious {
		rw := 32
		if rw > width/4 {
			rw = width / 4
		}
		l.RightRail = Region{width - rw, 1, rw, height - 1}
		l.HasRightRail = true
	}

	// Footer height
	footerH := 1
	if l.Tier >= TierStandard {
		footerH = 2
	}
	l.Footer = Region{0, height - footerH, width, footerH}

	// Status bar (between footer and input, only at T2+ and only if toggled)
	statusH := 0
	if showStatusBar && l.Tier >= TierStandard {
		statusH = 1
	}
	if statusH > 0 {
		l.StatusBar = Region{0, height - footerH - statusH, width, statusH}
	}

	// Input height
	inputH := 3
	if l.Tier == TierMinimal {
		inputH = 1
	}
	l.Input = Region{0, height - footerH - statusH - inputH, width, inputH}

	// Feed = the rest
	feedX := 0
	feedW := width
	if l.HasRightRail {
		feedW = l.RightRail.X
	}
	feedH := l.Input.Y - 1 // from below header to above input
	if feedH < 3 {
		feedH = 3
	}
	l.Feed = Region{feedX, 1, feedW, feedH}

	// IsCompact = true at T0/T1
	l.IsCompact = l.Tier <= TierCompact
	return l
}
