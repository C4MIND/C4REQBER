package tui

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

type setupMsg struct {
	payload setupKeysPayload
	output  string
	err     error
}

type setupAssignMsg struct {
	envName string
	output  string
	err     error
}

type setupCategoryRow struct {
	ID          string
	Label       string
	Configured  int
	Total       int
}

type setupKeyRow struct {
	EnvName    string
	Category   string
	Label      string
	Configured bool
	Masked     string
	Required   bool
}

type setupKeysPayload struct {
	Categories []struct {
		ID          string `json:"id"`
		Label       string `json:"label"`
		Configured  int    `json:"configured"`
		Total       int    `json:"total"`
	} `json:"categories"`
	Keys []struct {
		EnvName    string `json:"env_name"`
		Category   string `json:"category"`
		Label      string `json:"label"`
		Configured bool   `json:"configured"`
		Masked     string `json:"masked"`
		Required   bool   `json:"required"`
	} `json:"keys"`
}

const setupActionCount = 2 // refresh, health

func setupKeysCmd() tea.Cmd {
	return func() tea.Msg {
		cmd := exec.Command(blastBin(), "config", "keys", "--json")
		out, err := cmd.Output()
		if err != nil {
			text := strings.TrimSpace(string(out))
			if text == "" && err != nil {
				text = err.Error()
			}
			return setupMsg{output: text, err: err}
		}
		var payload setupKeysPayload
		if jerr := json.Unmarshal(out, &payload); jerr != nil {
			return setupMsg{output: strings.TrimSpace(string(out)), err: jerr}
		}
		return setupMsg{payload: payload}
	}
}

func setupAssignCmd(envName, value string) tea.Cmd {
	return func() tea.Msg {
		assign := envName + "=" + value
		cmd := exec.Command(blastBin(), "config", "keys", "--assign", assign)
		out, err := cmd.CombinedOutput()
		text := strings.TrimSpace(string(out))
		if text == "" && err != nil {
			text = err.Error()
		}
		return setupAssignMsg{envName: envName, output: text, err: err}
	}
}

func (m *model) applySetupPayload(p setupKeysPayload) {
	m.setupCategories = nil
	for _, c := range p.Categories {
		m.setupCategories = append(m.setupCategories, setupCategoryRow{
			ID: c.ID, Label: c.Label, Configured: c.Configured, Total: c.Total,
		})
	}
	m.setupKeys = nil
	for _, k := range p.Keys {
		m.setupKeys = append(m.setupKeys, setupKeyRow{
			EnvName: k.EnvName, Category: k.Category, Label: k.Label,
			Configured: k.Configured, Masked: k.Masked, Required: k.Required,
		})
	}
}

func (m *model) setupKeysForCategory() []setupKeyRow {
	if m.setupSelectedCategory == "" {
		return nil
	}
	out := make([]setupKeyRow, 0)
	for _, k := range m.setupKeys {
		if k.Category == m.setupSelectedCategory {
			out = append(out, k)
		}
	}
	return out
}

func openSetupHub(m *model) tea.Cmd {
	m.setupVisible = true
	m.setupLoading = true
	m.setupOutput = ""
	m.setupCatCursor = 0
	m.setupKeyCursor = 0
	m.setupInCategory = false
	m.setupEditing = false
	m.setupEditEnvName = ""
	m.setupEditValue = ""
	m.setupFocusActions = false
	m.setupSelectedCategory = ""
	m.setToast("🔑 " + i18n.T("setup.title"))
	return setupKeysCmd()
}

func setupHealthCmd() tea.Cmd {
	return func() tea.Msg {
		cmd := exec.Command(blastBin(), "config", "keys", "--health")
		out, err := cmd.CombinedOutput()
		text := strings.TrimSpace(string(out))
		if text == "" && err != nil {
			text = err.Error()
		}
		return setupMsg{output: text, err: err}
	}
}

func (m *model) runSetupAction(action int) tea.Cmd {
	switch action {
	case 0:
		m.setupLoading = true
		m.setupOutput = i18n.T("setup.running")
		return setupKeysCmd()
	case 1:
		m.setupLoading = true
		m.setupOutput = i18n.T("setup.running")
		return setupHealthCmd()
	default:
		return nil
	}
}

func setupMenuEnter(m *model) tea.Cmd {
	if m.setupEditing {
		val := strings.TrimSpace(m.setupEditValue)
		if val == "" {
			m.setupOutput = i18n.T("setup.empty_value")
			return nil
		}
		m.setupLoading = true
		m.setupEditing = false
		env := m.setupEditEnvName
		m.setupEditEnvName = ""
		m.setupEditValue = ""
		return setupAssignCmd(env, val)
	}
	if m.setupFocusActions {
		return m.runSetupAction(m.setupActionCursor)
	}
	if m.setupInCategory {
		keys := m.setupKeysForCategory()
		if m.setupKeyCursor >= 0 && m.setupKeyCursor < len(keys) {
			row := keys[m.setupKeyCursor]
			m.setupEditing = true
			m.setupEditEnvName = row.EnvName
			m.setupEditValue = ""
			m.setupOutput = i18n.T("setup.enter_value") + " " + row.EnvName
		}
		return nil
	}
	if m.setupCatCursor >= 0 && m.setupCatCursor < len(m.setupCategories) {
		m.setupInCategory = true
		m.setupSelectedCategory = m.setupCategories[m.setupCatCursor].ID
		m.setupKeyCursor = 0
		m.setupFocusActions = false
	}
	return nil
}

func truncateSetupNav(m *model, up bool) {
	if m.setupEditing {
		return
	}
	if m.setupFocusActions {
		if up {
			if m.setupActionCursor > 0 {
				m.setupActionCursor--
			} else if m.setupInCategory {
				m.setupFocusActions = false
				keys := m.setupKeysForCategory()
				if len(keys) > 0 {
					m.setupKeyCursor = len(keys) - 1
				}
			} else if len(m.setupCategories) > 0 {
				m.setupFocusActions = false
				m.setupCatCursor = len(m.setupCategories) - 1
			}
		} else if m.setupActionCursor < setupActionCount-1 {
			m.setupActionCursor++
		}
		return
	}
	if m.setupInCategory {
		keys := m.setupKeysForCategory()
		if up {
			if m.setupKeyCursor > 0 {
				m.setupKeyCursor--
			} else {
				m.setupInCategory = false
				m.setupSelectedCategory = ""
			}
			return
		}
		if m.setupKeyCursor < len(keys)-1 {
			m.setupKeyCursor++
			return
		}
		m.setupFocusActions = true
		m.setupActionCursor = 0
		return
	}
	if up {
		if m.setupCatCursor > 0 {
			m.setupCatCursor--
		}
		return
	}
	if m.setupCatCursor < len(m.setupCategories)-1 {
		m.setupCatCursor++
		return
	}
	m.setupFocusActions = true
	m.setupActionCursor = 0
}

func RenderSetupHub(
	categories []setupCategoryRow,
	keys []setupKeyRow,
	selectedCategory string,
	inCategory, editing bool,
	catCursor, keyCursor, actionCursor int,
	focusActions bool,
	editEnv, editValue, output string,
	loading bool,
	width, height int,
) string {
	if width < 40 {
		width = 80
	}
	if height < 12 {
		height = 24
	}
	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3"))
	labelStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("7"))
	cursorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Bold(true)
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("3")).
		Padding(1, 2).
		Width(min(78, width-4))

	var body strings.Builder
	body.WriteString(titleStyle.Render("🔑  "+i18n.T("setup.title")) + "\n\n")

	if !inCategory {
		body.WriteString(dimStyle.Render(i18n.T("setup.categories")) + "\n")
		if len(categories) == 0 {
			body.WriteString("  " + dimStyle.Render(i18n.T("setup.loading")) + "\n")
		}
		for i, cat := range categories {
			marker := "  "
			line := labelStyle.Render(fmt.Sprintf("%s  %d/%d", cat.Label, cat.Configured, cat.Total))
			if i == catCursor && !focusActions {
				marker = cursorStyle.Render("▶ ")
				line = cursorStyle.Render(fmt.Sprintf("%s  %d/%d", cat.Label, cat.Configured, cat.Total))
			}
			body.WriteString(marker + line + "\n")
		}
	} else {
		body.WriteString(dimStyle.Render(selectedCategory) + "\n")
		filtered := make([]setupKeyRow, 0)
		for _, k := range keys {
			if k.Category == selectedCategory {
				filtered = append(filtered, k)
			}
		}
		window := 8
		start := 0
		if keyCursor >= window {
			start = keyCursor - window + 1
		}
		end := start + window
		if end > len(filtered) {
			end = len(filtered)
		}
		for i := start; i < end; i++ {
			k := filtered[i]
			icon := "○"
			if k.Configured {
				icon = "●"
			}
			marker := "  "
			val := k.Masked
			if val == "" {
				val = "(not set)"
			}
			line := fmt.Sprintf("%s %s  %s", icon, k.EnvName, val)
			if i == keyCursor && !focusActions && !editing {
				marker = cursorStyle.Render("▶ ")
				line = cursorStyle.Render(fmt.Sprintf("%s %s  %s", icon, k.EnvName, val))
			} else {
				line = labelStyle.Render(line)
			}
			body.WriteString(marker + line + "\n")
		}
	}

	body.WriteString("\n" + dimStyle.Render(i18n.T("setup.actions")) + "\n")
	actions := []string{"setup.action.refresh", "setup.action.health"}
	for i, act := range actions {
		marker := "  "
		line := labelStyle.Render(i18n.T(act))
		if focusActions && i == actionCursor {
			marker = cursorStyle.Render("▶ ")
			line = cursorStyle.Render(i18n.T(act))
		}
		body.WriteString(marker + line + "\n")
	}

	if editing {
		body.WriteString("\n" + cursorStyle.Render(editEnv+": ") + editValue + "▌\n")
	} else if loading {
		body.WriteString("\n" + dimStyle.Render(i18n.T("setup.running")) + "\n")
	} else if output != "" {
		body.WriteString("\n" + dimStyle.Render(truncate(output, 360)) + "\n")
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("setup.hint")))
	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, boxStyle.Render(body.String()))
}
