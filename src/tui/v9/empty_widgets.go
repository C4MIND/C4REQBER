package tui

import (
	"fmt"
	"strings"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// EmptyWidgets returns a list of Card structs to render in the feed
// area when no discoveries have been made yet. Each widget takes a
// known height (3-5 lines) so the viewport doesn't show a huge
// black void below the empty placeholder.
//
// v9.13.x polish: simplified to a SINGLE clean placeholder card. The
// previous 7-widget wall (tip / examples / status / shortcuts / modes /
// achievements) was reported as "куча команд reflected in chat" — it
// visually overwhelmed the fixed layout and made the feed look chaotic
// at first run. Help lives in the footer keymap, ? overlay, and Ctrl+,
// settings — not in the feed.
func (m *model) emptyWidgets() []Card {
	now := m.startedAt
	if now.IsZero() {
		now = timeNow()
	}
	return []Card{
		{
			Kind:  CardEmpty,
			Title: i18n.T("empty.title"),
			Body:  i18n.T("empty.hint"),
			Time:  now,
		},
	}
}

// tipExample returns a rotating example query to inspire the user.
// Cycles every 3 idle frames so the widget feels alive without
// flickering.
func (m *model) tipExample() string {
	examples := []string{
		"What if horizontal gene transfer shapes whale acoustic dialects?",
		"Why does sleep downscale cortical synapses — is it active maintenance?",
		"How could CRISPR-Cas13 target non-coding RNA in neurons?",
		"Can a quantum-coherent cryptochrome explain bird magnetoreception?",
		"What if phase separation drives embryonic cell-fate decisions?",
	}
	if len(examples) == 0 {
		return ""
	}
	idx := (int(m.tick/120) + m.completedDisc) % len(examples)
	if idx < 0 {
		idx = -idx
	}
	return examples[idx]
}

// tipShortcuts returns a formatted multi-line string of the most
// useful keybindings for the current platform. Uses KeyMap so the
// labels match the user's OS (Cmd on Mac, Ctrl elsewhere).
func (m *model) tipShortcuts() string {
	if m.keymap == nil {
		return ""
	}
	lines := []string{
		fmt.Sprintf("%s  %s   %s  %s   %s  %s",
			m.keymap.Label(ActRun), i18n.T("keymap.run"),
			m.keymap.Label(ActHelp), i18n.T("keymap.help"),
			m.keymap.Label(ActQuit), i18n.T("keymap.quit"),
		),
		fmt.Sprintf("%s  %s   %s  %s   %s  %s",
			m.keymap.Label(ActCycleMode), i18n.T("keymap.cycle_mode"),
			m.keymap.Label(ActLang), i18n.T("keymap.lang"),
			m.keymap.Label(ActTier), i18n.T("keymap.cycle_tier"),
		),
		fmt.Sprintf("%s  %s   %s  %s   %s  %s",
			m.keymap.Label(ActColorProfile), i18n.T("profile.cycle"),
			m.keymap.Label(ActSettings), i18n.T("settings.title"),
			m.keymap.Label(ActNewTab), i18n.T("keymap.telemetry"),
		),
	}
	return strings.Join(lines, "\n")
}

// tipModes describes the 4 mode variants briefly so the user knows
// what each one does without having to read the docs.
func (m *model) tipModes() string {
	return strings.Join([]string{
		fmt.Sprintf("▶ Discover   —  %s", i18n.T("widget.mode.discover")),
		fmt.Sprintf("▶ Flash      —  %s", i18n.T("widget.mode.flash")),
		fmt.Sprintf("▶ Turbo      —  %s", i18n.T("widget.mode.turbo")),
		fmt.Sprintf("▶ Factory    —  %s", i18n.T("widget.mode.factory")),
	}, "\n")
}

// renderEmptyWidgets renders the empty-state widgets as a single
// string suitable for the viewport content. The widgets are
// framed with bubblezone.Mark for clickability (future).
func (m *model) renderEmptyWidgets() string {
	cards := m.emptyWidgets()
	var b strings.Builder
	for i, c := range cards {
		if i > 0 {
			b.WriteString("\n")
		}
		b.WriteString(renderCard(c, m.width, "", false, false))
	}
	return b.String()
}

// timeNow is a package-level variable so tests can stub it.

// timeNow is a package-level variable so tests can stub it.
var timeNow = func() time.Time { return time.Now() }

// timeSecond returns a time.Duration of n seconds, used in widget
// timestamps so the 5 widget cards have distinct times.
func timeSecond(n int) time.Duration { return time.Duration(n) * time.Second }
