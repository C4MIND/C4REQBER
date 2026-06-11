package tui

import (
	"fmt"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// SettingsRow is one option in the in-app settings menu (Ctrl+,).
type SettingsRow struct {
	Key         string // i18n key for label
	Value       string // current value (formatted)
	Description string // i18n key for description
}

// CurrentSettings returns the live settings for the in-app menu.
func (m *model) CurrentSettings() []SettingsRow {
	tel := m.tel.Get()
	// Per-stage LLM config (v9.12.5): show which model each phase uses
	stageInfo := ""
	if m.llmTier.String() == "C1" {
		stageInfo = "A:local B:cheap C:cheap D:balanced E:— F:balanced G:cheap"
	} else if m.llmTier.String() == "C2" {
		stageInfo = "A:local B:balanced C:balanced D:premium E:— F:premium G:balanced"
	} else {
		stageInfo = "A:local B:balanced C:balanced D:premium E:— F:premium G:premium"
	}
	return []SettingsRow{
		{Key: "settings.llm_tier", Value: m.llmTier.String() + " (" + m.llmTier.ModelFor() + " · ~$" + fmt.Sprintf("%.3f", m.llmTier.EstimatedCost()) + ")", Description: "settings.llm_tier.desc"},
		{Key: "settings.llm_stage", Value: stageInfo, Description: "settings.llm_stage.desc"},
		{Key: "settings.color_profile", Value: m.colorProfile.String(), Description: "settings.color_profile.desc"},
		{Key: "settings.dream_idle", Value: fmt.Sprintf("%ds", m.dream.idleSeconds), Description: "settings.dream_idle.desc"},
		{Key: "settings.lang", Value: string(i18n.GetLang()), Description: "settings.lang.desc"},
		{Key: "settings.api_url", Value: m.apiURL, Description: "settings.api_url.desc"},
		{Key: "settings.save_history", Value: boolOnOff(m.saveHistory), Description: "settings.save_history.desc"},
		{Key: "settings.telemetry", Value: fmt.Sprintf("disc=%d ok=%d fail=%d abort=%d", tel.Discoveries, tel.DiscoveriesOK, tel.DiscoveriesFail, tel.DiscoveriesAbort), Description: "settings.telemetry.desc"},
		{Key: "settings.sim_preference", Value: m.simPreference, Description: "settings.sim_preference.desc"},
		{Key: "settings.sim_cost_limit", Value: fmt.Sprintf("$%.2f", m.simCostLimit), Description: "settings.sim_cost_limit.desc"},
		{Key: "settings.sim_spend", Value: fmt.Sprintf("$%.4f (cap $%.2f)", m.simSpendThisSession, m.simCostLimit), Description: "settings.sim_spend.desc"},
		{Key: "settings.capabilities_status", Value: capsim.ShortSummary(m.capsimReport), Description: "settings.capabilities_status.desc"},
	}
}

func boolOnOff(b bool) string {
	if b {
		return "ON"
	}
	return "OFF"
}

// RenderSettingsMenu renders the settings overlay (Ctrl+, to toggle).
// cursor is the currently highlighted row (0-indexed).
func RenderSettingsMenu(cursor, width, height int) string {
	m := NewAppFresh("http://test")
	if m == nil {
		return ""
	}
	// We can't easily access the calling model's settings here,
	// so we re-fetch from a fresh model — but the user expects CURRENT values.
	// For now we render with placeholder and let caller substitute if needed.
	_ = m
	// Use static rows for the demo render (caller passes live rows via the wrapper).
	rows := []SettingsRow{
		{Key: "settings.llm_tier", Value: "C2 (qwen-2.5-72b · ~$0.012)", Description: "settings.llm_tier.desc"},
		{Key: "settings.color_profile", Value: "default", Description: "settings.color_profile.desc"},
		{Key: "settings.dream_idle", Value: "300s", Description: "settings.dream_idle.desc"},
		{Key: "settings.lang", Value: "en", Description: "settings.lang.desc"},
		{Key: "settings.api_url", Value: "http://127.0.0.1:8000", Description: "settings.api_url.desc"},
		{Key: "settings.save_history", Value: "ON", Description: "settings.save_history.desc"},
		{Key: "settings.telemetry", Value: "disc=0 ok=0 fail=0 abort=0", Description: "settings.telemetry.desc"},
	}
	return renderSettingsMenuInner(rows, cursor, width, height)
}

// RenderSettingsMenuWith renders the settings menu with explicit values (preferred).
func RenderSettingsMenuWith(rows []SettingsRow, cursor, width, height int) string {
	return renderSettingsMenuInner(rows, cursor, width, height)
}

func renderSettingsMenuInner(rows []SettingsRow, cursor, width, height int) string {
	if width < 30 {
		width = 80
	}
	if height < 10 {
		height = 24
	}
	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3")).Padding(0, 2)
	labelStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Width(20)
	valueStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6"))
	cursorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Bold(true)
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("3")).
		Padding(1, 2).
		Width(min(70, width-4))

	var body string
	body = titleStyle.Render("⚙  "+i18n.T("settings.title")) + "\n\n"
	for i, row := range rows {
		marker := "  "
		label := labelStyle.Render(i18n.T(row.Key))
		value := valueStyle.Render(row.Value)
		if i == cursor {
			marker = cursorStyle.Render("▶ ")
			label = cursorStyle.Render(i18n.T(row.Key))
			value = cursorStyle.Render(row.Value)
		}
		body += fmt.Sprintf("%s%s  %s\n", marker, label, value)
	}
	body += "\n" + dimStyle.Render(i18n.T("settings.hint"))

	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, boxStyle.Render(body))
}
