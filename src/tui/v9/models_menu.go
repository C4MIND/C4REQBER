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

type modelsConfigMsg struct {
	payload modelsConfigPayload
	output  string
	err     error
}

type modelsConfigPayload struct {
	CostTier          string                   `json:"cost_tier"`
	ConfigPath        string                   `json:"config_path"`
	Phases            []modelsPhaseRow         `json:"phases"`
	Council           map[string][]string      `json:"council"`
	EstimatedCostUSD  float64                  `json:"estimated_cost_usd"`
}

type modelsPhaseRow struct {
	Phase       string  `json:"phase"`
	Description string  `json:"description"`
	Model       string  `json:"model"`
	Temperature float64 `json:"temperature"`
	MaxTokens   int     `json:"max_tokens"`
}

const modelsViewPhases = 0
const modelsViewCouncil = 1

func modelsConfigCmd() tea.Cmd {
	return func() tea.Msg {
		cmd := exec.Command(blastBin(), "config", "--show", "--json")
		out, err := cmd.Output()
		if err != nil {
			text := strings.TrimSpace(string(out))
			if text == "" {
				text = err.Error()
			}
			return modelsConfigMsg{output: text, err: err}
		}
		var payload modelsConfigPayload
		if jerr := json.Unmarshal(out, &payload); jerr != nil {
			return modelsConfigMsg{output: strings.TrimSpace(string(out)), err: jerr}
		}
		return modelsConfigMsg{payload: payload}
	}
}

func openModelsMenu(m *model) tea.Cmd {
	m.modelsVisible = true
	m.modelsLoading = true
	m.modelsOutput = ""
	m.modelsView = modelsViewPhases
	m.modelsCursor = 0
	m.setToast("🧠 " + i18n.T("models.title"))
	return modelsConfigCmd()
}

func (m *model) applyModelsPayload(p modelsConfigPayload) {
	m.modelsPhases = p.Phases
	m.modelsCouncil = p.Council
	m.modelsCostTier = p.CostTier
	m.modelsEstCost = p.EstimatedCostUSD
}

func modelsRows(m *model) []string {
	if m.modelsView == modelsViewCouncil {
		rows := make([]string, 0)
		for tier, models := range m.modelsCouncil {
			rows = append(rows, tier+": "+strings.Join(models, ", "))
		}
		if len(rows) == 0 {
			rows = append(rows, i18n.T("models.no_council"))
		}
		return rows
	}
	rows := make([]string, 0, len(m.modelsPhases))
	for _, p := range m.modelsPhases {
		model := p.Model
		if model == "" {
			model = "(compute — no LLM)"
		}
		rows = append(rows, "Phase "+p.Phase+": "+truncate(model, 40))
	}
	return rows
}

func truncateModelsNav(m *model, up bool) {
	rows := modelsRows(m)
	if len(rows) == 0 {
		return
	}
	if up {
		if m.modelsCursor > 0 {
			m.modelsCursor--
		}
		return
	}
	if m.modelsCursor < len(rows)-1 {
		m.modelsCursor++
	}
}

func modelsMenuEnter(m *model) tea.Cmd {
	// Tab between phases / council views
	m.modelsView = 1 - m.modelsView
	m.modelsCursor = 0
	label := i18n.T("models.view.phases")
	if m.modelsView == modelsViewCouncil {
		label = i18n.T("models.view.council")
	}
	m.modelsOutput = label
	return nil
}

func RenderModelsMenu(
	phases []modelsPhaseRow,
	council map[string][]string,
	view, cursor int,
	costTier string,
	estCost float64,
	output string,
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
	body.WriteString(titleStyle.Render("🧠  "+i18n.T("models.title")) + "\n")
	body.WriteString(dimStyle.Render(i18n.T("models.tier")+": "+costTier+" · ~$"+formatCost(estCost)) + "\n\n")

	viewLabel := i18n.T("models.view.phases")
	rows := make([]string, 0)
	if view == modelsViewCouncil {
		viewLabel = i18n.T("models.view.council")
		for tier, models := range council {
			rows = append(rows, tier+": "+truncate(strings.Join(models, ", "), 50))
		}
		if len(rows) == 0 {
			rows = append(rows, i18n.T("models.no_council"))
		}
	} else {
		for _, p := range phases {
			model := p.Model
			if model == "" {
				model = "(no LLM)"
			}
			rows = append(rows, "Phase "+p.Phase+": "+truncate(model, 44))
		}
	}
	body.WriteString(dimStyle.Render(viewLabel) + "\n")
	for i, row := range rows {
		marker := "  "
		line := labelStyle.Render(row)
		if i == cursor {
			marker = cursorStyle.Render("▶ ")
			line = cursorStyle.Render(row)
		}
		body.WriteString(marker + line + "\n")
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("models.hint_switch")) + "\n")
	if loading {
		body.WriteString(dimStyle.Render(i18n.T("models.running")) + "\n")
	} else if output != "" {
		body.WriteString(dimStyle.Render(truncate(output, 200)) + "\n")
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("models.hint")))
	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, boxStyle.Render(body.String()))
}

func formatCost(v float64) string {
	return strings.TrimRight(strings.TrimRight(fmt.Sprintf("%.4f", v), "0"), ".")
}
