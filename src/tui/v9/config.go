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
	APIURL    string
	Lang      i18n.Lang
	DreamIdle int // seconds; 0 = disabled
	NoColor   bool
	Width     int
	Height    int
	ExtraQuotes []string // env C4_DREAM_QUOTES (newline-separated)
	SaveHistory bool    // env C4_SAVE_HISTORY (default true)
	LLMTier   LLMTier   // env C4_LLM_TIER (C1/C2/C3, default C2)
	ColorProfile ColorProfile // env C4_COLOR_PROFILE
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() Config {
	return Config{
		APIURL:      "http://127.0.0.1:8000",
		Lang:        i18n.LangEN,
		DreamIdle:   300,
		NoColor:     false,
		Width:       0,
		Height:      0,
		ExtraQuotes: nil,
		SaveHistory: true,
		LLMTier:     TierC2,
		ColorProfile: ProfileDefault,
	}
}

// LoadConfig reads environment variables and returns a Config.
// Recognized env vars:
//   C4_API_URL       - backend URL (default: http://127.0.0.1:8000)
//   C4_LANG          - starting language (en/ru/zh/ja/de/ar/hi)
//   C4_DREAM_IDLE    - seconds of idle before dream mode (0=disabled, default 300)
//   C4_NO_COLOR      - if set (any value), disable colors
//   C4_WIDTH         - initial width (0=auto)
//   C4_HEIGHT        - initial height (0=auto)
//   C4_DREAM_QUOTES  - newline-separated extra dream quotes to append
//   C4_SAVE_HISTORY  - "0"/"false" to disable telemetry history save
func LoadConfig() Config {
	cfg := DefaultConfig()
	if v := os.Getenv("C4_API_URL"); v != "" {
		cfg.APIURL = v
	}
	if v := os.Getenv("C4_LANG"); v != "" {
		lang := i18n.Lang(strings.ToLower(v))
		// Validate
		switch lang {
		case i18n.LangEN, i18n.LangRU, i18n.LangZH, i18n.LangJA,
			i18n.LangDE, i18n.LangAR, i18n.LangHI:
			cfg.Lang = lang
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
	if width < 20 {
		width = 80
	}
	if height < 10 {
		height = 24
	}
	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3"))
	sectionStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6"))
	keyStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("2")).Width(12)
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	boxStyle := lipgloss.NewStyle().Width(width - 2).Padding(0, 1)

	type entry struct{ key, desc string }
	sections := []struct {
		title   string
		entries []entry
	}{
		{"Navigation", []entry{
			{"Tab", i18n.T("help.tab")},
			{"Shift+L", i18n.T("help.lang")},
			{"Ctrl+T", i18n.T("help.telemetry")},
			{"?", i18n.T("help.toggle")},
			{"Esc", i18n.T("help.cancel")},
			{"Ctrl+C", i18n.T("help.quit")},
		}},
		{"Run", []entry{
			{"Enter", i18n.T("help.run")},
			{"mouse", i18n.T("help.mouse")},
		}},
		{"Display", []entry{
			{"rain", i18n.T("help.rain")},
			{"burst", i18n.T("help.burst")},
			{"sparks", i18n.T("help.sparks")},
		}},
	}

	var b strings.Builder
	b.WriteString(titleStyle.Render("✨ C4REQBER v9 — " + i18n.T("help.title")))
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
