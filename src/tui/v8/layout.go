package main

// layout holds computed panel dimensions for a single frame.
type layout struct {
	// Overall
	width  int
	height int

	// Top
	headerH int
	sepH    int // 0 or 1 for horizontal rule

	// Bottom
	chatH   int
	helpH   int
	statusH int

	// Body
	bodyH int

	// Columns
	leftW  int
	midW   int
	rightW int

	// Left column (C4 + Mascot)
	c4H      int
	mascotH  int
	showCube bool

	// Middle column (Input + Pipeline)
	inputH int
	pipeH  int

	// Responsive flags
	narrow     bool // width < 90
	veryNarrow bool // width < 70
	short      bool // height < 24
}

// computeLayout calculates optimal panel dimensions based on terminal size.
// It is the single source of truth for both View() and Update().
func (m model) computeLayout() layout {
	l := layout{
		width:   m.Width,
		height:  m.Height,
		headerH: 2,
		statusH: 1,
		sepH:    1, // horizontal rule between header and body
	}

	// Emergency fallback for impossibly small terminals
	if m.Height < 10 {
		l.bodyH = max(1, m.Height-l.headerH-l.statusH-l.sepH)
		l.leftW = m.Width
		l.midW = m.Width
		l.rightW = m.Width
		l.c4H = l.bodyH
		l.inputH = l.bodyH
		l.pipeH = 0
		l.showCube = false
		l.chatH = 0
		l.helpH = 0
		return l
	}

	// Responsive breakpoints
	l.narrow = m.Width < 90
	l.veryNarrow = m.Width < 70
	l.short = m.Height < 24

	// Chat height — adaptive
	if m.Chat.Expanded {
		l.chatH = m.Cfg.Layout.ChatExpandedHeight
		if l.chatH > m.Height/3 {
			l.chatH = m.Height / 3
		}
		if l.chatH < 4 {
			l.chatH = 4
		}
	} else {
		l.chatH = m.Cfg.Layout.ChatCollapsedHeight
		if l.chatH < 1 {
			l.chatH = 1
		}
	}

	// Help height — collapsed tip is always 1 line; expanded is adaptive
	if m.Help.Visible {
		l.helpH = m.Cfg.Layout.HelpHeight
		if l.helpH > m.Height/3 {
			l.helpH = m.Height / 3
		}
		if l.helpH < 4 {
			l.helpH = 4
		}
	} else {
		l.helpH = 1 // collapsed tip line
	}

	// Auto-collapse help/chat when screen is very short
	if l.short {
		if l.helpH > 1 {
			l.helpH = 1 // keep tip line even when short
		}
		if l.chatH > 1 {
			l.chatH = 1
		}
	}

	// Body height
	l.bodyH = m.Height - l.headerH - l.sepH - l.chatH - l.helpH - l.statusH
	if l.bodyH < 3 {
		// Emergency: hide help/chat to make room for body
		l.chatH = 0
		l.helpH = 0
		l.bodyH = m.Height - l.headerH - l.sepH - l.statusH
		if l.bodyH < 1 {
			l.bodyH = 1
		}
	}

	// Column widths
	const minColW = 20
	if l.veryNarrow {
		// Single column: everything stacks
		l.leftW = m.Width
		l.midW = m.Width
		l.rightW = m.Width
	} else if l.narrow {
		// Two-column layout: left = C4+Mascot, right = Input+Pipeline+Result
		l.leftW = m.Width * 35 / 100
		if l.leftW < minColW {
			l.leftW = minColW
		}
		l.rightW = m.Width - l.leftW
		if l.rightW < minColW {
			l.rightW = minColW
			l.leftW = m.Width - l.rightW
		}
		l.midW = l.rightW // middle shares right column in 2-col mode
	} else {
		// Three-column layout — give Result more space
		l.leftW = m.Width * 28 / 100
		l.midW = m.Width * 32 / 100
		l.rightW = m.Width - l.leftW - l.midW
		if l.rightW < minColW {
			l.rightW = minColW
			l.leftW = (m.Width - l.rightW) * 45 / 100
			l.midW = m.Width - l.leftW - l.rightW
		}
	}

	// Left column split: C4Grid + Mascot
	l.showCube = true
	if l.short || l.veryNarrow {
		l.showCube = false // hide decorative mascot on tiny screens
	}
	if l.showCube {
		l.c4H, l.mascotH = splitHeight(l.bodyH, 6, 10, 6, 5)
		if l.mascotH == 0 {
			l.showCube = false
		}
	} else {
		l.c4H = l.bodyH
		l.mascotH = 0
	}

	// Middle column split: InputBar + Pipeline
	l.inputH, l.pipeH = splitHeight(l.bodyH, 30, 100, 5, 4)

	// Adaptive: shrink pipeline when idle to give more space to Result
	if !m.Pipeline.Running && m.Pipeline.StartTime.IsZero() {
		l.pipeH = 5
		if l.pipeH > l.bodyH-4 {
			l.pipeH = l.bodyH - 4
			if l.pipeH < 0 {
				l.pipeH = 0
			}
		}
		l.inputH = l.bodyH - l.pipeH
	}

	return l
}

// splitHeight divides total height proportionally while respecting minimums.
// If total is too small for both minimums, priority goes to 'a' and b becomes 0.
func splitHeight(total, ratioNum, ratioDen, minA, minB int) (a, b int) {
	a = total * ratioNum / ratioDen
	b = total - a
	if total >= minA+minB {
		if a < minA {
			a = minA
		}
		if b < minB {
			b = minB
		}
		if a+b > total {
			// Give priority to a, shrink b
			b = total - a
			if b < minB {
				b = minB
				a = total - b
			}
		}
	} else {
		// Not enough room — priority to a, b hidden
		a = total
		b = 0
	}
	return
}

// (header separator is now cached in view.go via cachedHeaderSeparator)
