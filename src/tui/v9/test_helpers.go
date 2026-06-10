package tui

import (
	"image/color"

	tea "charm.land/bubbletea/v2"
	"github.com/figuramax/c4reqber-tui-v9/api"
)

// Test helper message constructors. Wrappers around bubbletea Msg types
// so tests don't need to import all bubbletea internals.

func teaWindowSizeMsg(w, h int) tea.WindowSizeMsg {
	return tea.WindowSizeMsg{Width: w, Height: h}
}

func teaKeyMsg(s string) tea.KeyPressMsg {
	return tea.KeyPressMsg{Text: s, Code: []rune(s)[0]}
}

func teaBackgroundColorMsg(isDark bool) tea.BackgroundColorMsg {
	if isDark {
		// Build a fake dark color (R=G=B=20)
		return tea.BackgroundColorMsg{Color: color.RGBA{R: 0x14, G: 0x14, B: 0x14}}
	}
	return tea.BackgroundColorMsg{Color: color.RGBA{R: 0xff, G: 0xff, B: 0xff}}
}

func teaMouseClickMsg(x, y int, left bool) tea.MouseClickMsg {
	btn := tea.MouseRight
	if left {
		btn = tea.MouseLeft
	}
	return tea.MouseClickMsg{X: x, Y: y, Button: btn}
}

func apiSSEEventMsg(ev api.SSEEvent) sseEventMsg {
	return sseEventMsg{event: ev, cancel: func() {}}
}
