package tui

import (
	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// WizardState is the state of the first-run wizard.
type WizardState struct {
	step    int // 0=hello, 1=try-demo, 2=help, 3=done
	active  bool
}

// NewWizardState returns a fresh wizard.
func NewWizardState() *WizardState {
	return &WizardState{step: 0}
}

// Show activates the wizard.
func (w *WizardState) Show() {
	w.active = true
	w.step = 0
}

// Hide deactivates the wizard.
func (w *WizardState) Hide() { w.active = false }

// Active returns whether wizard is shown.
func (w *WizardState) Active() bool { return w.active }

// Step returns the current step.
func (w *WizardState) Step() int { return w.step }

// Next advances to next step.
func (w *WizardState) Next() {
	if w.step < 3 {
		w.step++
	}
}

// Done marks wizard as finished.
func (w *WizardState) Done() {
	w.active = false
	w.step = 3
}

// RenderWizard renders the wizard overlay.
func RenderWizard(width, height int) string {
	if width < 30 {
		width = 80
	}
	if height < 10 {
		height = 24
	}
	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3")).Padding(0, 2)
	bodyStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Padding(1, 2)
	accentStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6"))
	boxStyle := lipgloss.NewStyle().
		Width(width-4).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("3")).
		Padding(1, 2)

	var body string
	switch 0 { // placeholder
	}

	switch currentWizardStep() {
	case 0:
		body = accentStyle.Render("✨ Welcome to C4REQBER v9!\n\n") +
			bodyStyle.Render(i18n.T("wizard.welcome")+"\n\n"+
				i18n.T("wizard.intro")+"\n\n"+
				accentStyle.Render("Press Enter → next · Esc → skip"))
	case 1:
		body = accentStyle.Render("🎮 "+i18n.T("wizard.demo_title")+"\n\n") +
			bodyStyle.Render(i18n.T("wizard.demo_body")+"\n\n"+
				"  d → "+i18n.T("wizard.run_demo")+"\n"+
				"  r → "+i18n.T("wizard.real_discovery")+"\n"+
				"  ? → "+i18n.T("wizard.show_help")+"\n\n"+
				accentStyle.Render("Press Enter → next · Esc → skip"))
	case 2:
		body = accentStyle.Render("⌨️  "+i18n.T("wizard.keys_title")+"\n\n") +
			bodyStyle.Render(i18n.T("wizard.keys_body")+"\n\n"+
				"  Tab    — cycle mode (DISCOVER/FLASH/TURBO/TURBOFACTORY)\n"+
				"  ⇧L     — cycle language (EN/RU/ZH/JA/DE/AR/HI)\n"+
				"  Ctrl+T — telemetry panel\n"+
				"  Ctrl+Y — cycle LLM tier (C1/C2/C3)\n"+
				"  ?      — this help overlay\n"+
				"  Esc    — cancel running discovery\n"+
				"  Ctrl+C — quit\n\n"+
				accentStyle.Render("Press Enter → start · Esc → skip"))
	default:
		body = bodyStyle.Render("Ready.")
	}
	return boxStyle.Render(titleStyle.Render("🚀 "+i18n.T("wizard.title")) + "\n\n" + body)
}

var currentWizardStep = func() int { return 0 }
