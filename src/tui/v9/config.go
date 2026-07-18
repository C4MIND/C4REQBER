package tui

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// Config holds runtime configuration loaded from env vars + defaults.
type Config struct {
	APIURL       string
	Lang         i18n.Lang
	DreamIdle    int // seconds; 0 = disabled
	NoColor      bool
	Width        int
	Height       int
	ExtraQuotes  []string     // env C4_DREAM_QUOTES (newline-separated)
	SaveHistory  bool         // env C4_SAVE_HISTORY (default true)
	LLMTier      LLMTier      // env C4_LLM_TIER (C1/C2/C3, default C2)
	ColorProfile ColorProfile // env C4_COLOR_PROFILE
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() Config {
	return Config{
		APIURL:       "http://127.0.0.1:8000",
		Lang:         i18n.LangEN,
		DreamIdle:    300,
		NoColor:      false,
		Width:        0,
		Height:       0,
		ExtraQuotes:  nil,
		SaveHistory:  true,
		LLMTier:      TierC2,
		ColorProfile: ProfileDefault,
	}
}

// LoadConfig reads environment variables and returns a Config.
// Recognized env vars:
//
//	C4_API_URL       - backend URL (default: http://127.0.0.1:8000)
//	C4_LANG          - starting language (en/ru/zh/ja/de/ar/hi)
//	C4_DREAM_IDLE    - seconds of idle before dream mode (0=disabled, default 300)
//	C4_NO_COLOR      - if set (any value), disable colors
//	C4_WIDTH         - initial width (0=auto)
//	C4_HEIGHT        - initial height (0=auto)
//	C4_DREAM_QUOTES  - newline-separated extra dream quotes to append
//	C4_SAVE_HISTORY  - "0"/"false" to disable telemetry history save
func LoadConfig() Config {
	cfg := DefaultConfig()
	if v := os.Getenv("C4_API_URL"); v != "" {
		cfg.APIURL = v
	}
	if v := os.Getenv("C4_LANG"); v != "" {
		if l, ok := i18n.FromString(v); ok {
			cfg.Lang = l
		}
	}
	if v := os.Getenv("C4_DREAM_IDLE"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n >= 0 {
			cfg.DreamIdle = n
		}
	}
	if _, ok := os.LookupEnv("C4_NO_COLOR"); ok {
		cfg.NoColor = true
	}
	if v := os.Getenv("C4_WIDTH"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			cfg.Width = n
		}
	}
	if v := os.Getenv("C4_HEIGHT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			cfg.Height = n
		}
	}
	if v := os.Getenv("C4_DREAM_QUOTES"); v != "" {
		for _, line := range strings.Split(v, "\n") {
			line = strings.TrimSpace(line)
			if line != "" {
				cfg.ExtraQuotes = append(cfg.ExtraQuotes, line)
			}
		}
	}
	if v := os.Getenv("C4_SAVE_HISTORY"); v != "" {
		v = strings.ToLower(v)
		if v == "0" || v == "false" || v == "no" || v == "off" {
			cfg.SaveHistory = false
		}
	}
	if v := os.Getenv("C4_LLM_TIER"); v != "" {
		if t, ok := TierFromString(v); ok {
			cfg.LLMTier = t
		}
	}
	if v := os.Getenv("C4_COLOR_PROFILE"); v != "" {
		if p, ok := ProfileFromString(v); ok {
			cfg.ColorProfile = p
		}
	}
	return cfg
}

// String returns a human-readable summary of the config.
func (c Config) String() string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("API=%s Lang=%s DreamIdle=%ds", c.APIURL, c.Lang, c.DreamIdle))
	b.WriteString(fmt.Sprintf(" LLM=%s Profile=%s", c.LLMTier, c.ColorProfile))
	if c.NoColor {
		b.WriteString(" NoColor")
	}
	if c.Width > 0 {
		b.WriteString(fmt.Sprintf(" W=%d", c.Width))
	}
	if c.Height > 0 {
		b.WriteString(fmt.Sprintf(" H=%d", c.Height))
	}
	if len(c.ExtraQuotes) > 0 {
		b.WriteString(fmt.Sprintf(" Quotes+%d", len(c.ExtraQuotes)))
	}
	if !c.SaveHistory {
		b.WriteString(" NoHistory")
	}
	return b.String()
}

// ApplyToModel mutates the model according to config (called on startup).
func (c Config) ApplyToModel(m *model) {
	if c.DreamIdle >= 0 && m.dream != nil {
		m.dream.idleSeconds = c.DreamIdle
	}
	if len(c.ExtraQuotes) > 0 {
		// Append to dream quotes (mutates package var)
		dreamQuotes = append(dreamQuotes, c.ExtraQuotes...)
	}
	if c.LLMTier != 0 {
		m.llmTier = c.LLMTier
	}
	if c.ColorProfile != 0 {
		m.colorProfile = c.ColorProfile
	}
}

// HelpOverlay renders a fullscreen keymap help.
func HelpOverlay(width, height int) string {
	return HelpOverlayWith(width, height, NewKeyMap(DetectPlatform()))
}

// HelpOverlayWith renders the help overlay using a specific keymap, so
// the displayed shortcuts match the active platform (Cmd+L on macOS,
// Ctrl+L on Linux/Windows, etc.).
func HelpOverlayWith(width, height int, km *KeyMap) string {
	if width < 20 {
		width = 80
	}
	if height < 10 {
		height = 24
	}
	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3"))
	sectionStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6"))
	keyStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("2")).Width(14)
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	boxStyle := lipgloss.NewStyle().Width(width-2).Padding(0, 1)

	// Resolve platform-specific keys. Display "Cmd+L / Ctrl+L" if both
	// are bound (e.g. macOS keeps Ctrl aliases for muscle memory).
	langKey := FormatKeyList(km.Labels(ActLang))
	tierKey := FormatKeyList(km.Labels(ActTier))
	tabKey := km.Label(ActCycleMode)
	telKey := km.Label(ActNewTab)
	helpKey := km.Label(ActHelp)
	cancelKey := km.Label(ActCancel)
	quitKey := km.Label(ActQuit)
	runKey := km.Label(ActRun)
	setKey := FormatKeyList(km.Labels(ActSettings))
	profKey := FormatKeyList(km.Labels(ActColorProfile))
	reaKey := km.Label(ActReauth)

	type entry struct{ key, desc string }
	sections := []struct {
		title   string
		entries []entry
	}{
		{"Navigation", []entry{
			{tabKey, i18n.T("help.tab")},
			{langKey, i18n.T("help.lang")},
			{tierKey, i18n.T("tier.cycle")},
			{telKey, i18n.T("help.telemetry")},
			{helpKey, i18n.T("help.toggle")},
			{cancelKey, i18n.T("help.cancel")},
			{quitKey, i18n.T("help.quit")},
		}},
		{"Run", []entry{
			{runKey, i18n.T("help.run")},
			{"mouse", i18n.T("help.mouse")},
			{profKey, i18n.T("profile.cycle")},
			{setKey, i18n.T("settings.title")},
			{reaKey, i18n.T("reauth.success")},
		}},
		{"Display", []entry{
			{"rain", i18n.T("help.rain")},
			{"burst", i18n.T("help.burst")},
			{"sparks", i18n.T("help.sparks")},
		}},
		{"Simulation", []entry{
			{km.Label(ActCapabilities), i18n.T("sim.capabilities.title")},
			{km.Label(ActInstallHint), i18n.T("sim.action.install")},
			{km.Label(ActSelectFallback), i18n.T("sim.action.fallback")},
			{km.Label(ActOpenPlot), i18n.T("sim.action.plot")},
		}},
	}

	var b strings.Builder
	title := "✨ C4REQBER v9 — " + i18n.T("help.title")
	if km != nil {
		title += " (" + km.Platform.Display() + ")"
	}
	b.WriteString(titleStyle.Render(title))
	b.WriteString("\n\n")
	for _, s := range sections {
		b.WriteString(sectionStyle.Render(s.title))
		b.WriteString("\n")
		for _, e := range s.entries {
			b.WriteString("  ")
			b.WriteString(keyStyle.Render(e.key))
			b.WriteString(e.desc)
			b.WriteString("\n")
		}
		b.WriteString("\n")
	}
	b.WriteString(dimStyle.Render(i18n.T("help.footer")))
	return boxStyle.Render(b.String())
}
