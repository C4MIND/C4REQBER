package tui

import (
	"image/color"
	"strings"

	tea "charm.land/bubbletea/v2"
	"github.com/figuramax/c4reqber-tui-v9/api"
)

// Test helper message constructors. Wrappers around bubbletea Msg types
// so tests don't need to import all bubbletea internals.

func teaWindowSizeMsg(w, h int) tea.WindowSizeMsg {
	return tea.WindowSizeMsg{Width: w, Height: h}
}

// teaNamedKeys maps keystroke names to their bubbletea/ultraviolet key codes
// so that the resulting KeyPressMsg.String() round-trips to the same name
// (e.g. "esc" -> KeyEscape -> "esc"). Without this, multi-rune names like
// "esc"/"tab"/"enter" would be truncated to their first rune.
var teaNamedKeys = map[string]rune{
	"esc":       tea.KeyEscape,
	"escape":    tea.KeyEscape,
	"tab":       tea.KeyTab,
	"enter":     tea.KeyEnter,
	"space":     tea.KeySpace,
	"backspace": tea.KeyBackspace,
	"delete":    tea.KeyDelete,
	"up":        tea.KeyUp,
	"down":      tea.KeyDown,
	"left":      tea.KeyLeft,
	"right":     tea.KeyRight,
	"home":      tea.KeyHome,
	"end":       tea.KeyEnd,
	"pgup":      tea.KeyPgUp,
	"pgdown":    tea.KeyPgDown,
}

// teaKeyMsg builds a bubbletea v2 KeyPressMsg from a keystroke string the same
// way bubbletea renders it back via String(): modifier prefixes (ctrl+/alt+/
// shift+) set the Mod bitmask, named special keys map to their key code, and a
// lone printable rune is carried in Text so String() returns it verbatim.
func teaKeyMsg(s string) tea.KeyPressMsg {
	var mod tea.KeyMod
	rest := s
loop:
	for {
		switch {
		case strings.HasPrefix(rest, "ctrl+"):
			mod |= tea.ModCtrl
			rest = rest[len("ctrl+"):]
		case strings.HasPrefix(rest, "alt+"):
			mod |= tea.ModAlt
			rest = rest[len("alt+"):]
		case strings.HasPrefix(rest, "shift+"):
			mod |= tea.ModShift
			rest = rest[len("shift+"):]
		default:
			break loop
		}
	}
	if code, ok := teaNamedKeys[rest]; ok {
		return tea.KeyPressMsg{Mod: mod, Code: code}
	}
	r := []rune(rest)
	if len(r) == 0 {
		return tea.KeyPressMsg{Mod: mod}
	}
	if mod == 0 {
		// Unmodified printable key: Text drives String().
		return tea.KeyPressMsg{Text: rest, Code: r[0]}
	}
	// Modified printable key: leave Text empty so String() uses the
	// "mod+key" keystroke form.
	return tea.KeyPressMsg{Mod: mod, Code: r[0]}
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
