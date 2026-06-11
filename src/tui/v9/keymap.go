package tui

import (
	"runtime"
	"sort"
	"strings"
)

// Platform identifies the runtime OS for key-binding adaptation.
type Platform string

const (
	PlatformDarwin  Platform = "darwin"
	PlatformLinux   Platform = "linux"
	PlatformWindows Platform = "windows"
	PlatformBSD     Platform = "bsd"
	PlatformUnknown Platform = "unknown"
)

// DetectPlatform returns the current runtime platform, normalized.
func DetectPlatform() Platform {
	switch runtime.GOOS {
	case "darwin":
		return PlatformDarwin
	case "linux":
		return PlatformLinux
	case "windows":
		return PlatformWindows
	case "freebsd", "openbsd", "netbsd", "dragonfly":
		return PlatformBSD
	default:
		return PlatformUnknown
	}
}

// Action identifies a semantic TUI action independent of its physical key.
// Each Action has one or more physical Keys (e.g. on macOS, Quit may be
// Cmd+Q; on Linux/Windows, Ctrl+C). The KeyMap resolves Action → physical
// label at runtime based on the active Platform.
type Action string

const (
	ActRun          Action = "run"           // Enter — submit discovery
	ActHelp         Action = "help"          // ? — show help overlay
	ActQuit         Action = "quit"          // Ctrl+C — exit
	ActCancel       Action = "cancel"        // Esc — cancel running
	ActCycleMode    Action = "cycle_mode"    // Tab — cycle DISCOVER/FLASH/TURBO/TURBOFACTORY
	ActLang         Action = "lang"          // L — cycle language
	ActReauth       Action = "reauth"        // Ctrl+L — re-authenticate
	ActSearch       Action = "search"        // / — search
	ActCopy         Action = "copy"          // c — copy card
	ActJump         Action = "jump"          // j — jump
	ActTier         Action = "tier"          // Ctrl+Y — cycle C1/C2/C3
	ActSettings     Action = "settings"      // Ctrl+, — settings menu
	ActCapabilities Action = "capabilities"  // Ctrl+Shift+C — sim/verifier capabilities overlay (v9.13)
	ActInstallHint  Action = "install_hint"  // i — show install hint for an unavailable sim engine
	ActSelectFallback Action = "fallback"    // f — show fallback chain for a skipped sim
	ActOpenPlot     Action = "open_plot"     // o — open a sim plot URL in browser
	ActStatusBar    Action = "status_bar"    // Ctrl+B — toggle 1-line status bar (§3.3)
	ActFocusPrev    Action = "focus_prev"    // k — focus previous card
	ActFocusNext    Action = "focus_next"    // j — focus next card
	ActFocusFirst   Action = "focus_first"   // g g — focus first card
	ActFocusLast    Action = "focus_last"    // G — focus last card (and re-enable follow)
	ActUp           Action = "up"            // ↑
	ActDown         Action = "down"          // ↓
	ActColorProfile Action = "color_profile" // Ctrl+Shift+P — color cycle
	ActProfileMac   Action = "profile"       // Shift+L on macOS (Cmd+Shift+P conflicts)
	ActNewTab       Action = "new_tab"       // Ctrl+T (Win/Linux) or Cmd+T (Mac)
	ActEscape       Action = "escape"        // Ctrl+. — universal TUI escape hatch
)

// KeyMap resolves semantic Actions to platform-appropriate display labels
// and to bubbletea key-event strings. It is built once per session from
// DetectPlatform() and is fully immutable afterwards.
type KeyMap struct {
	Platform Platform
	bindings map[Action][]keyBinding
}

// keyBinding is one physical key variant for an Action, with display
// label and matching bubbletea event strings.
type keyBinding struct {
	label string   // human-readable, e.g. "Cmd+L"
	keys  []string // bubbletea msg.String() matches, e.g. {"ctrl+l", "cmd+l"}
}

// NewKeyMap builds a keymap for the given platform.
func NewKeyMap(p Platform) *KeyMap {
	km := &KeyMap{Platform: p, bindings: defaultBindings()}
	if remap, ok := platformRemap[p]; ok {
		for action, keys := range remap {
			if existing, has := km.bindings[action]; has {
				km.bindings[action] = mergeBindings(existing, keys)
			} else {
				km.bindings[action] = keys
			}
		}
	}
	return km
}

// defaultBindings provides the cross-platform fallback for every Action.
// Platform-specific remaps may add or override labels.
func defaultBindings() map[Action][]keyBinding {
	return map[Action][]keyBinding{
		ActRun:          {{label: "Enter", keys: []string{"enter", " "}}},
		ActHelp:         {{label: "?", keys: []string{"?"}}},
		ActQuit:         {{label: "Ctrl+C", keys: []string{"ctrl+c"}}},
		ActCancel:       {{label: "Esc", keys: []string{"esc"}}},
		ActCycleMode:    {{label: "Tab", keys: []string{"tab"}}},
		ActLang:         {{label: "L", keys: []string{"l", "shift+l"}}},
		ActReauth:       {{label: "Ctrl+L", keys: []string{"ctrl+l"}}},
		ActSearch:       {{label: "/", keys: []string{"/"}}},
		ActCopy:         {{label: "c", keys: []string{"c"}}},
		ActJump:         {{label: "Ctrl+J", keys: []string{"ctrl+j"}}},
		ActTier:         {{label: "Ctrl+Y", keys: []string{"ctrl+y"}}},
		ActSettings:     {{label: "Ctrl+,", keys: []string{"ctrl+,"}}},
		ActCapabilities: {{label: "Ctrl+Shift+C", keys: []string{"ctrl+shift+c"}}},
		ActInstallHint:  {{label: "i", keys: []string{"i"}}},
		ActSelectFallback: {{label: "f", keys: []string{"f"}}},
		ActOpenPlot:     {{label: "o", keys: []string{"o"}}},
		ActStatusBar:    {{label: "Ctrl+B", keys: []string{"ctrl+b"}}},
		ActFocusPrev:    {{label: "k", keys: []string{"k"}}},
		ActFocusNext:    {{label: "j", keys: []string{"j"}}},
		ActFocusFirst:   {{label: "g g", keys: []string{"g", "g"}}},
		ActFocusLast:    {{label: "G", keys: []string{"G", "shift+g"}}},
		ActUp:           {{label: "↑", keys: []string{"up"}}},
		ActDown:         {{label: "↓", keys: []string{"down"}}},
		ActColorProfile: {{label: "Ctrl+Shift+P", keys: []string{"ctrl+shift+p"}}},
		ActProfileMac:   {{label: "Cmd+Shift+P", keys: []string{"cmd+shift+p"}}},
		ActNewTab:       {{label: "Ctrl+T", keys: []string{"ctrl+t"}}},
		ActEscape:       {{label: "Ctrl+.", keys: []string{"ctrl+."}}},
	}
}

// platformRemap holds per-platform key overrides/additions.
// On macOS we replace OS-conflicting bindings (Ctrl+L = lock screen,
// Ctrl+, = System Preferences, Ctrl+T = new tab in Terminal/Chrome) with
// Cmd-prefixed equivalents. On Windows/Linux the defaults are fine.
var platformRemap = map[Platform]map[Action][]keyBinding{
	PlatformDarwin: {
		ActReauth: {
			{label: "Cmd+L", keys: []string{"cmd+l"}},
		},
		ActSettings: {
			{label: "Cmd+,", keys: []string{"cmd+,"}},
		},
		ActNewTab: {
			{label: "Cmd+T", keys: []string{"cmd+t"}},
		},
		ActTier: {
			{label: "Cmd+Y", keys: []string{"cmd+y"}},
			{label: "Ctrl+Y", keys: []string{"ctrl+y"}}, // keep ctrl as alias
		},
		ActColorProfile: {
			{label: "Cmd+Shift+P", keys: []string{"cmd+shift+p"}},
		},
		ActProfileMac: {
			{label: "Cmd+Shift+P", keys: []string{"cmd+shift+p"}},
		},
	},
	PlatformWindows: {
		// Windows Terminal reserves Ctrl+T for new tab by default; we keep
		// our binding but the user can disable it in WT settings.
	},
	PlatformLinux: {
		// Most Linux DEs leave Ctrl+T free, but GNOME Terminal may map it
		// to "new tab". We expose Ctrl+T for v9 and document the
		// workaround in the help overlay.
	},
}

// mergeBindings prepends platform-specific bindings before the default
// ones, so Label() returns the platform-native form first. Aliases
// (e.g. Ctrl+Y on macOS) are still appended as fallbacks.
func mergeBindings(existing, extra []keyBinding) []keyBinding {
	seen := map[string]bool{}
	out := make([]keyBinding, 0, len(existing)+len(extra))
	for _, b := range extra {
		if !seen[b.label] {
			out = append(out, b)
			seen[b.label] = true
		}
	}
	for _, b := range existing {
		if !seen[b.label] {
			out = append(out, b)
			seen[b.label] = true
		}
	}
	return out
}

// Label returns the primary (first) display label for an Action.
// Falls back to empty string if unknown.
func (km *KeyMap) Label(a Action) string {
	if bs, ok := km.bindings[a]; ok && len(bs) > 0 {
		return bs[0].label
	}
	return ""
}

// Labels returns all display labels for an Action (primary + alternates).
func (km *KeyMap) Labels(a Action) []string {
	if bs, ok := km.bindings[a]; ok {
		out := make([]string, len(bs))
		for i, b := range bs {
			out[i] = b.label
		}
		return out
	}
	return nil
}

// Matches reports whether a bubbletea key-event string matches this Action.
// On macOS both "cmd+l" and "ctrl+l" resolve to ActReauth so user muscle
// memory from Linux/Windows keeps working.
func (km *KeyMap) Matches(a Action, keyStr string) bool {
	// Don't trim — a literal space " " is a valid key (Enter alias for
	// some terminals). Just normalize case.
	keyStr = strings.ToLower(keyStr)
	if keyStr == "" {
		return false
	}
	for _, b := range km.bindings[a] {
		for _, k := range b.keys {
			if strings.EqualFold(k, keyStr) {
				return true
			}
		}
	}
	return false
}

// HelpRow describes one line in the help overlay.
type HelpRow struct {
	Action Action
	Keys   []string // display labels
	Desc   string   // i18n key suffix under "help."
}

// HelpRows returns the ordered list of actions to display in the help
// overlay, with the resolved key labels for the active platform.
func (km *KeyMap) HelpRows() []HelpRow {
	order := []Action{
		ActRun, ActCancel, ActCycleMode, ActLang, ActTier,
		ActReauth, ActSearch, ActCopy, ActJump, ActSettings, ActCapabilities,
		ActInstallHint, ActSelectFallback, ActOpenPlot, ActStatusBar,
		ActColorProfile, ActProfileMac, ActNewTab, ActEscape, ActHelp, ActQuit,
	}
	rows := make([]HelpRow, 0, len(order))
	for _, a := range order {
		rows = append(rows, HelpRow{
			Action: a,
			Keys:   km.Labels(a),
			Desc:   helpDescKey(a),
		})
	}
	return rows
}

func helpDescKey(a Action) string {
	switch a {
	case ActRun:
		return "help.run"
	case ActCancel:
		return "help.cancel"
	case ActCycleMode:
		return "help.tab"
	case ActLang:
		return "help.lang"
	case ActTier:
		return "help.tier"
	case ActReauth:
		return "reauth.success"
	case ActSearch:
		return "search.title"
	case ActCopy:
		return "clipboard.copied"
	case ActJump:
		return "help.hidden"
	case ActSettings:
		return "settings.title"
	case ActCapabilities:
		return "sim.capabilities.title"
	case ActInstallHint:
		return "sim.action.install"
	case ActSelectFallback:
		return "sim.action.fallback"
	case ActOpenPlot:
		return "sim.action.plot"
	case ActColorProfile, ActProfileMac:
		return "profile.cycle"
	case ActNewTab:
		return "help.hidden"
	case ActEscape:
		return "help.cancel"
	case ActHelp:
		return "help.toggle"
	case ActQuit:
		return "help.quit"
	}
	return ""
}

// FormatKeyList renders a list of key labels as a single string.
// On macOS we use the unicode arrow (⌘) for compact display where
// the full "Cmd+" prefix would be too wide. Single-char keys are
// returned as-is.
func FormatKeyList(labels []string) string {
	return strings.Join(labels, " / ")
}

// PlatformName returns a human-readable platform name for the help footer.
func (p Platform) Display() string {
	switch p {
	case PlatformDarwin:
		return "macOS"
	case PlatformLinux:
		return "Linux"
	case PlatformWindows:
		return "Windows"
	case PlatformBSD:
		return "BSD"
	default:
		return "Unknown"
	}
}

// AllActions returns all defined Actions in deterministic order.
// Used by tests and tooling.
func AllActions() []Action {
	return []Action{
		ActRun, ActHelp, ActQuit, ActCancel, ActCycleMode, ActLang,
		ActReauth, ActSearch, ActCopy, ActJump, ActTier, ActSettings,
		ActUp, ActDown, ActColorProfile, ActProfileMac, ActNewTab, ActEscape,
	}
}

// SortedKeys returns the actions mapped to bindings in alphabetical order
// of the action name — used by introspection tools.
func (km *KeyMap) SortedKeys() []string {
	acts := make([]string, 0, len(km.bindings))
	for a := range km.bindings {
		acts = append(acts, string(a))
	}
	sort.Strings(acts)
	return acts
}
