// Package tui — command palette Registry constructor (binds to model).
// This file lives in the root tui package because it captures *model
// closures. The actual matching logic is in commands/palette.go.
package tui

import (
	"fmt"
	"strings"

	"charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/commands"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// MatchResult aliases the commands package type.
type MatchResult = commands.MatchResult

// Registry aliases the commands package type.
type Registry = commands.Registry

// NewRegistry aliases the commands constructor.
func NewRegistry() *Registry { return commands.NewRegistry() }

// buildRegistry constructs the default registry. Called once from
// NewApp / NewAppFresh.
func buildRegistry() *commands.Registry {
	r := commands.NewRegistry()
	// ── App ────────────────────────────────────────────────────
	r.Register(commands.Command{
		ID: "app.quit", Title: "Quit", Aliases: []string{"q", "exit"},
		Category: "App", Key: "Ctrl+C", Icon: "⏏",
		Run: func() any { return tea.Quit() },
	})
	r.Register(commands.Command{
		ID: "app.help", Title: "Show help overlay", Aliases: []string{"h", "?"},
		Category: "App", Key: "?", Icon: "?",
		Run: nil, // bound below via Bind
	})
	r.Register(commands.Command{
		ID: "app.settings", Title: "Open settings", Aliases: []string{"s", "prefs", "preferences"},
		Category: "Settings", Key: "Ctrl+,", Icon: "⚙",
		Run: nil,
	})
	r.Register(commands.Command{
		ID: "app.capabilities", Title: "Show simulation capabilities", Aliases: []string{"capsim", "engines", "sims"},
		Category: "Sim", Key: "Ctrl+Shift+C", Icon: "⏚",
		Run: nil,
	})
	r.Register(commands.Command{
		ID: "app.debug", Title: "Show debug overlay", Aliases: []string{"debug", "diag", "diagnostics"},
		Category: "App", Key: "Ctrl+Shift+D", Icon: "🔧",
		Run: nil,
	})
	r.Register(commands.Command{
		ID: "app.status_bar", Title: "Toggle status bar", Aliases: []string{"statusbar", "status"},
		Category: "App", Key: "Ctrl+B", Icon: "📊",
		Run: nil,
	})
	r.Register(commands.Command{
		ID: "app.wizard", Title: "Re-run first-run wizard", Aliases: []string{"tour", "onboard", "wizard"},
		Category: "App", Icon: "🧙",
		Run: nil,
	})
	r.Register(commands.Command{
		ID: "app.history", Title: "Show history", Aliases: []string{"hist"},
		Category: "App", Icon: "📜",
		Run: nil,
	})
	// ── Mode ───────────────────────────────────────────────────
	r.Register(commands.Command{
		ID: "mode.discover", Title: "Switch to DISCOVER mode", Aliases: []string{"d", "discover"},
		Category: "Mode", Icon: "🔬", Run: nil,
	})
	r.Register(commands.Command{
		ID: "mode.flash", Title: "Switch to FLASH mode", Aliases: []string{"f", "flash", "quick"},
		Category: "Mode", Icon: "⚡", Run: nil,
	})
	r.Register(commands.Command{
		ID: "mode.turbo", Title: "Switch to TURBO mode", Aliases: []string{"t", "turbo"},
		Category: "Mode", Icon: "🚀", Run: nil,
	})
	r.Register(commands.Command{
		ID: "mode.factory", Title: "Switch to TURBOFACTORY mode", Aliases: []string{"tf", "factory"},
		Category: "Mode", Icon: "🏭", Run: nil,
	})
	r.Register(commands.Command{
		ID: "mode.cycle", Title: "Cycle mode (next)", Aliases: []string{"cycle"},
		Category: "Mode", Key: "Tab", Icon: "🔄", Run: nil,
	})
	// ── Sim ────────────────────────────────────────────────────
	r.Register(commands.Command{
		ID: "sim.list", Title: "List simulation capabilities", Aliases: []string{"simlist", "sims"},
		Category: "Sim", Icon: "⏚", Run: nil,
	})
	r.Register(commands.Command{
		ID: "sim.cost", Title: "Show sim cost this session", Aliases: []string{"simcost"},
		Category: "Sim", Icon: "$", Run: nil,
	})
	r.Register(commands.Command{
		ID: "sim.refresh", Title: "Refresh sim capabilities (force)", Aliases: []string{"simrefresh"},
		Category: "Sim", Icon: "↻", Run: nil,
	})
	r.Register(commands.Command{
		ID: "sim.preference.auto", Title: "Sim preference: auto", Aliases: []string{"simauto"},
		Category: "Sim", Icon: "🟢", Run: nil,
	})
	r.Register(commands.Command{
		ID: "sim.preference.cpu", Title: "Sim preference: cpu_only", Aliases: []string{"simcpu"},
		Category: "Sim", Icon: "🟡", Run: nil,
	})
	r.Register(commands.Command{
		ID: "sim.preference.off", Title: "Sim preference: off (skip sims)", Aliases: []string{"simoff"},
		Category: "Sim", Icon: "⏸", Run: nil,
	})
	// ── Theme ───────────────────────────────────────────────────
	r.Register(commands.Command{
		ID: "theme.default", Title: "Theme: default", Aliases: []string{"themedefault"},
		Category: "Theme", Icon: "🎨", Run: nil,
	})
	r.Register(commands.Command{
		ID: "theme.high-contrast", Title: "Theme: high-contrast", Aliases: []string{"hc"},
		Category: "Theme", Icon: "🎨", Run: nil,
	})
	r.Register(commands.Command{
		ID: "theme.solarized", Title: "Theme: solarized-dark", Aliases: []string{"solar", "solarized"},
		Category: "Theme", Icon: "🎨", Run: nil,
	})
	r.Register(commands.Command{
		ID: "theme.cycle", Title: "Cycle color profile", Aliases: []string{"theme"},
		Category: "Theme", Key: "Ctrl+Shift+P", Icon: "🎨", Run: nil,
	})
	// ── Feed ───────────────────────────────────────────────────
	r.Register(commands.Command{
		ID: "feed.clear", Title: "Clear feed", Aliases: []string{"clear", "wipe"},
		Category: "Feed", Key: "Ctrl+K", Icon: "🗑", Run: nil,
	})
	r.Register(commands.Command{
		ID: "feed.follow", Title: "Toggle follow mode", Aliases: []string{"follow"},
		Category: "Feed", Key: "F", Icon: "▶", Run: nil,
	})
	r.Register(commands.Command{
		ID: "feed.first", Title: "Focus first card", Aliases: []string{"first", "top"},
		Category: "Feed", Key: "g g", Icon: "⤒", Run: nil,
	})
	r.Register(commands.Command{
		ID: "feed.last", Title: "Focus last card", Aliases: []string{"last", "bottom"},
		Category: "Feed", Key: "G", Icon: "⤓", Run: nil,
	})
	// ── Language ───────────────────────────────────────────────
	for _, lang := range []string{"en", "ru", "zh", "ja", "de", "ar", "hi"} {
		langCopy := lang
		r.Register(commands.Command{
			ID: "lang." + langCopy, Title: "Language: " + langCopy,
			Aliases: []string{"lang" + langCopy, "i18n" + langCopy},
			Category: "Language", Icon: "🌐", Run: nil,
		})
	}
	// ── Help ───────────────────────────────────────────────────
	r.Register(commands.Command{
		ID: "help.shortcuts", Title: "Show keyboard shortcuts", Aliases: []string{"keys", "shortcuts"},
		Category: "Help", Icon: "🗝", Run: nil,
	})
	return r
}

// bindRegistry walks the registry and replaces placeholder nil Runs
// with the actual *model-bound closures. Called once per app init.
func (m *model) bindRegistry() {
	if m.paletteRegistry == nil {
		return
	}
	// Re-register with bound Run functions by finding each command by ID
	// and replacing it.
	bindings := map[string]func() any{
		"app.help": func() any {
			m.showHelp = !m.showHelp
			if m.showHelp {
				m.setToast(i18n.T("help.shown"))
			} else {
				m.setToast(i18n.T("help.hidden"))
			}
			return nil
		},
		"app.settings": func() any {
			m.settingsVisible = !m.settingsVisible
			return nil
		},
		"app.capabilities": func() any {
			m.showCapabilities = !m.showCapabilities
			if m.showCapabilities {
				m.capsimLoading = true
				return capsimCmd(m.capsimClient, false)
			}
			return nil
		},
		"app.debug": func() any {
			m.showDebug = !m.showDebug
			return nil
		},
		"app.status_bar": func() any {
			m.showStatusBar = !m.showStatusBar
			return nil
		},
		"app.wizard": func() any {
			m.wizard.Show()
			if m.store != nil {
				m.store.MarkFirstRun()
			}
			return nil
		},
		"app.history": func() any {
			m.setToast("📜 history: see resume (auto-loaded from feed.jsonl)")
			return nil
		},
		"mode.discover": func() any { m.mode = ModeDiscover; m.setToast("🔬 DISCOVER"); return nil },
		"mode.flash":    func() any { m.mode = ModeFlash; m.setToast("⚡ FLASH"); return nil },
		"mode.turbo":    func() any { m.mode = ModeTurbo; m.setToast("🚀 TURBO"); return nil },
		"mode.factory":  func() any { m.mode = ModeTurboFactory; m.setToast("🏭 TURBOFACTORY"); return nil },
		"mode.cycle": func() any {
			m.cycleMode()
			m.setToast("🔄 " + string(m.mode))
			return nil
		},
		"sim.list": func() any {
			m.showCapabilities = true
			return capsimCmd(m.capsimClient, false)
		},
		"sim.cost": func() any {
			m.setToast(fmt.Sprintf("$%.4f spent on sims this session", m.simSpendThisSession))
			return nil
		},
		"sim.refresh": func() any {
			if m.capsimClient != nil {
				m.capsimClient.Invalidate()
			}
			m.showCapabilities = true
			return capsimCmd(m.capsimClient, true)
		},
		"sim.preference.auto": func() any { m.simPreference = "auto"; m.setToast("🟢 sim preference: auto"); return nil },
		"sim.preference.cpu":  func() any { m.simPreference = "cpu_only"; m.setToast("🟡 sim preference: cpu_only"); return nil },
		"sim.preference.off":  func() any { m.simPreference = "off"; m.setToast("⏸ sim preference: off"); return nil },
		"theme.default":       func() any { m.colorProfile = ProfileDefault; m.theme = NewTheme(ProfileDefault); m.setToast("🎨 default"); return nil },
		"theme.high-contrast": func() any { m.colorProfile = ProfileHighContrast; m.theme = NewTheme(ProfileHighContrast); m.setToast("🎨 high-contrast"); return nil },
		"theme.solarized":     func() any { m.colorProfile = ProfileSolarizedDark; m.theme = NewTheme(ProfileSolarizedDark); m.setToast("🎨 solarized-dark"); return nil },
		"theme.cycle": func() any {
			switch m.colorProfile {
			case ProfileDefault:
				m.colorProfile = ProfileHighContrast
			case ProfileHighContrast:
				m.colorProfile = ProfileProtanopia
			case ProfileProtanopia:
				m.colorProfile = ProfileDeuteranopia
			case ProfileDeuteranopia:
				m.colorProfile = ProfileTritanopia
			case ProfileTritanopia:
				m.colorProfile = ProfileMonochrome
			case ProfileMonochrome:
				m.colorProfile = ProfileSolarizedDark
			default:
				m.colorProfile = ProfileDefault
			}
			m.theme = NewTheme(m.colorProfile)
			m.setToast("🎨 " + m.colorProfile.String())
			return nil
		},
		"feed.clear": func() any {
			if m.running {
				m.setToast("🗑 cannot clear while a discovery is running")
			} else {
				m.feed = nil
				m.zoneIDs = nil
				m.rebuildFeedContent()
				m.setToast("🗑 feed cleared")
			}
			return nil
		},
		"feed.follow": func() any { m.follow = !m.follow; m.setToast(fmt.Sprintf("▶ follow=%v", m.follow)); return nil },
		"feed.first":  func() any { if len(m.feed) > 0 { m.focusedCardIdx = 0; m.follow = false }; return nil },
		"feed.last":   func() any { if len(m.feed) > 0 { m.focusedCardIdx = len(m.feed) - 1; m.follow = true }; return nil },
		"help.shortcuts": func() any { m.showHelp = true; return nil },
	}
	// Languages
	for _, lang := range []string{"en", "ru", "zh", "ja", "de", "ar", "hi"} {
		langCopy := lang
		bindings["lang."+langCopy] = func() any {
			i18n.SetLang(i18n.Lang(langCopy))
			m.setToast("🌐 lang: " + langCopy)
			return nil
		}
	}
	// Walk the registry's all-cmds, find each by ID, and swap Run
	all := m.paletteRegistry.All()
	for i, c := range all {
		if b, ok := bindings[c.ID]; ok {
			c.Run = b
			all[i] = c
		}
	}
}

// cycleMode advances the mode to the next in the cycle:
// DISCOVER → FLASH → TURBO → TURBOFACTORY → DISCOVER.
func (m *model) cycleMode() {
	switch m.mode {
	case ModeDiscover:
		m.mode = ModeFlash
	case ModeFlash:
		m.mode = ModeTurbo
	case ModeTurbo:
		m.mode = ModeTurboFactory
	default:
		m.mode = ModeDiscover
	}
}

// openPalette opens the palette and recomputes matches for empty query.
func (m *model) openPalette() {
	m.paletteActive = true
	m.paletteQuery = ""
	m.paletteFocused = 0
	m.paletteMatches = m.paletteRegistry.Match("")
}

// runPaletteFocused executes the focused command.
func (m *model) runPaletteFocused() {
	if m.paletteFocused < 0 || m.paletteFocused >= len(m.paletteMatches) {
		return
	}
	cmd := m.paletteMatches[m.paletteFocused].Cmd
	m.paletteActive = false
	if cmd.Run != nil {
		_ = cmd.Run()
	}
}

// refreshPaletteMatches recomputes matches for the current query.
func (m *model) refreshPaletteMatches() {
	m.paletteMatches = m.paletteRegistry.Match(m.paletteQuery)
	if m.paletteFocused >= len(m.paletteMatches) {
		m.paletteFocused = len(m.paletteMatches) - 1
	}
	if m.paletteFocused < 0 {
		m.paletteFocused = 0
	}
}

// silence unused import (audit 2026-06-22 M-3: hack removed, strings IS used at line 360)

// RenderCommandPalette renders the fullscreen palette overlay.
// Pure function so it's testable independently of the model.
func RenderCommandPalette(query string, matches []MatchResult, focusedIdx int, width, height int) string {
	if width < 50 {
		width = 50
	}
	if height < 10 {
		height = 20
	}
	var b strings.Builder
	b.WriteString("⌘ Command Palette (: to open, Esc to close)\n\n")
	b.WriteString("> ")
	b.WriteString(query)
	b.WriteString("█\n\n")
	if len(matches) == 0 {
		b.WriteString("  (no matches — try 'help', 'settings', 'capabilities', 'sim list', 'theme')\n")
		return b.String()
	}
	maxRows := height - 6
	if maxRows < 5 {
		maxRows = 5
	}
	end := len(matches)
	if end > maxRows {
		end = maxRows
	}
	start := 0
	if focusedIdx >= maxRows {
		start = focusedIdx - maxRows + 1
	}
	if start+end > len(matches) {
		start = len(matches) - end
		if start < 0 {
			start = 0
		}
	}
	for i := start; i < start+end; i++ {
		m := matches[i]
		prefix := "  "
		if i == focusedIdx {
			prefix = "▶ "
		}
		icon := m.Cmd.Icon
		if icon == "" {
			icon = "·"
		}
		cat := ""
		if m.Cmd.Category != "" {
			cat = "  " + m.Cmd.Category
		}
		keyHint := ""
		if m.Cmd.Key != "" {
			keyHint = "  [" + m.Cmd.Key + "]"
		}
		line := fmt.Sprintf("%s%s %s%s%s", prefix, icon, m.Cmd.Title, cat, keyHint)
		b.WriteString(line)
		b.WriteString("\n")
	}
	b.WriteString("\n")
	b.WriteString(fmt.Sprintf("  %d commands  ·  ↑↓ to navigate  ·  Enter to run  ·  Esc to close",
		len(matches)))
	return b.String()
}
