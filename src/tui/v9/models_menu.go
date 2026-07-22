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

type modelsSaveMsg struct {
	tier   string
	output string
	err    error
}

type modelsConfigPayload struct {
	CostTier         string              `json:"cost_tier"`
	ConfigPath        string              `json:"config_path"`
	Phases            []modelsPhaseRow    `json:"phases"`
	Council           map[string][]string `json:"council"`
	EstimatedCostUSD  float64             `json:"estimated_cost_usd"`
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

// Cost tiers accepted by `blast config --tier` (ModelAssignment SSOT).
var modelsCostTier = []string{"budget", "balanced", "premium", "local", "ultra_budget"}

// Map council budget labels → ModelAssignment cost_tier names.
var councilToCostTier = map[string]string{
	"cheap":         "budget",
	"budget":        "budget",
	"balanced":      "balanced",
	"premium":       "premium",
	"local":         "local",
	"ultra_budget":  "ultra_budget",
}

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

func modelsSaveTierCmd(tier string) tea.Cmd {
	return func() tea.Msg {
		cmd := exec.Command(blastBin(), "config", "--tier", tier, "--save")
		out, err := cmd.CombinedOutput()
		text := strings.TrimSpace(string(out))
		if text == "" && err != nil {
			text = err.Error()
		}
		return modelsSaveMsg{tier: tier, output: text, err: err}
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
		for _, tier := range councilTierOrdered(m.modelsCouncil) {
			rows = append(rows, tier+": "+strings.Join(m.modelsCouncil[tier], ", "))
		}
		if len(rows) == 0 {
			rows = append(rows, i18n.T("models.no_council"))
		}
		return rows
	}
	rows := make([]string, 0, len(m.modelsPhases))
	for _, p := range m.modelsPhases {
		modelName := p.Model
		if modelName == "" {
			modelName = "(compute — no LLM)"
		}
		rows = append(rows, "Phase "+p.Phase+": "+truncate(modelName, 40))
	}
	return rows
}

func councilTierOrdered(council map[string][]string) []string {
	if council == nil {
		return nil
	}
	tiers := make([]string, 0, len(council))
	for tier := range council {
		tiers = append(tiers, tier)
	}
	ordered := make([]string, 0, len(tiers))
	seen := map[string]bool{}
	for _, pref := range []string{"cheap", "budget", "balanced", "premium", "local", "ultra_budget"} {
		if _, ok := council[pref]; ok {
			ordered = append(ordered, pref)
			seen[pref] = true
		}
	}
	for _, t := range tiers {
		if !seen[t] {
			ordered = append(ordered, t)
		}
	}
	return ordered
}

func modelsToggleView(m *model) {
	m.modelsView = 1 - m.modelsView
	m.modelsCursor = 0
	label := i18n.T("models.view.phases")
	if m.modelsView == modelsViewCouncil {
		label = i18n.T("models.view.council")
	}
	m.modelsOutput = label
}

func nextCostTier(current string) string {
	if current == "" {
		return "balanced"
	}
	for i, t := range modelsCostTier {
		if t == current {
			return modelsCostTier[(i+1)%len(modelsCostTier)]
		}
	}
	return "balanced"
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
	// Persist via blast config --tier/--save (models.json SSOT).
	if m.modelsView == modelsViewCouncil {
		tiers := councilTierOrdered(m.modelsCouncil)
		if len(tiers) == 0 {
			m.modelsOutput = i18n.T("models.no_council")
			return nil
		}
		idx := m.modelsCursor
		if idx < 0 || idx >= len(tiers) {
			idx = 0
		}
		raw := tiers[idx]
		tier := councilToCostTier[raw]
		if tier == "" {
			tier = raw
		}
		m.modelsLoading = true
		m.setToast("💾 " + i18n.T("models.tier") + ": " + tier)
		return modelsSaveTierCmd(tier)
	}
	// Phases view: cycle cost tier and persist.
	next := nextCostTier(m.modelsCostTier)
	m.modelsLoading = true
	m.setToast("💾 " + i18n.T("models.tier") + ": " + next)
	return modelsSaveTierCmd(next)
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
		for _, tier := range councilTierOrdered(council) {
			models := council[tier]
			rows = append(rows, tier+": "+truncate(strings.Join(models, ", "), 50))
		}
		if len(rows) == 0 {
			rows = append(rows, i18n.T("models.no_council"))
		}
	} else {
		for _, p := range phases {
			modelName := p.Model
			if modelName == "" {
				modelName = "(no LLM)"
			}
			rows = append(rows, "Phase "+p.Phase+": "+truncate(modelName, 44))
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
