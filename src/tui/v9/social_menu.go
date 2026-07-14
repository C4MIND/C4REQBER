package tui

import (
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// socialMsg is delivered when a blast social subprocess completes.
type socialMsg struct {
	output string
	err    error
}

// SocialAction identifies a menu row in the social publishing overlay.
type SocialAction int

const (
	socialActionRefresh SocialAction = iota
	socialActionHealth
	socialActionPublish
	socialActionPostMastodon
	socialActionPostBluesky
	socialActionCount
)

func socialDraftsDir() string {
	return filepath.Join(userConfigDir(), "drafts")
}

// loadSocialDrafts returns draft folder names newest-first.
func loadSocialDrafts() []string {
	dir := socialDraftsDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	names := make([]string, 0, len(entries))
	for _, e := range entries {
		if e.IsDir() {
			names = append(names, e.Name())
		}
	}
	sort.Slice(names, func(i, j int) bool { return names[i] > names[j] })
	return names
}

func selectedSocialDraft(m *model) string {
	if len(m.socialDrafts) == 0 {
		return ""
	}
	if m.socialDraftCursor < 0 || m.socialDraftCursor >= len(m.socialDrafts) {
		return m.socialDrafts[0]
	}
	return m.socialDrafts[m.socialDraftCursor]
}

func blastBin() string {
	if p, err := exec.LookPath("blast"); err == nil {
		return p
	}
	return "blast"
}

// socialCmd runs `blast social <args...>` off the UI thread.
func socialCmd(args ...string) tea.Cmd {
	return func() tea.Msg {
		cmd := exec.Command(blastBin(), append([]string{"social"}, args...)...)
		out, err := cmd.CombinedOutput()
		text := strings.TrimSpace(string(out))
		if text == "" && err != nil {
			text = err.Error()
		}
		return socialMsg{output: text, err: err}
	}
}

func (m *model) refreshSocialDrafts() {
	m.socialDrafts = loadSocialDrafts()
	if m.socialDraftCursor >= len(m.socialDrafts) {
		m.socialDraftCursor = 0
	}
}

func (m *model) runSocialAction(action SocialAction) tea.Cmd {
	switch action {
	case socialActionRefresh:
		m.refreshSocialDrafts()
		m.socialOutput = i18n.T("social.refreshed")
		return nil
	case socialActionHealth:
		m.socialLoading = true
		m.socialOutput = i18n.T("social.running")
		return socialCmd("health")
	default:
		draft := selectedSocialDraft(m)
		if draft == "" {
			m.socialOutput = i18n.T("social.no_drafts")
			return nil
		}
		m.socialLoading = true
		m.socialOutput = i18n.T("social.running")
		switch action {
		case socialActionPublish:
			return socialCmd("publish", "--id", draft)
		case socialActionPostMastodon:
			return socialCmd("post", "--id", draft, "--platform", "mastodon")
		case socialActionPostBluesky:
			return socialCmd("post", "--id", draft, "--platform", "bluesky")
		}
	}
	return nil
}

// RenderSocialMenu renders the social publishing overlay.
func RenderSocialMenu(
	drafts []string,
	draftCursor, actionCursor int,
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
		Width(min(76, width-4))

	var body strings.Builder
	body.WriteString(titleStyle.Render("📣  "+i18n.T("social.title")) + "\n\n")
	body.WriteString(dimStyle.Render(i18n.T("social.drafts")) + "\n")
	if len(drafts) == 0 {
		body.WriteString("  " + dimStyle.Render(i18n.T("social.no_drafts")) + "\n")
	} else {
		maxDrafts := 6
		if len(drafts) < maxDrafts {
			maxDrafts = len(drafts)
		}
		for i := 0; i < maxDrafts; i++ {
			marker := "  "
			line := labelStyle.Render(drafts[i])
			if i == draftCursor {
				marker = cursorStyle.Render("▶ ")
				line = cursorStyle.Render(drafts[i])
			}
			body.WriteString(marker + line + "\n")
		}
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("social.actions")) + "\n")
	actions := []struct {
		key string
	}{
		{"social.action.refresh"},
		{"social.action.health"},
		{"social.action.publish"},
		{"social.action.post_mastodon"},
		{"social.action.post_bluesky"},
	}
	for i, act := range actions {
		marker := "  "
		line := labelStyle.Render(i18n.T(act.key))
		if i == actionCursor {
			marker = cursorStyle.Render("▶ ")
			line = cursorStyle.Render(i18n.T(act.key))
		}
		body.WriteString(marker + line + "\n")
	}
	if loading {
		body.WriteString("\n" + dimStyle.Render(i18n.T("social.running")) + "\n")
	} else if output != "" {
		body.WriteString("\n" + dimStyle.Render(truncate(output, 400)) + "\n")
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("social.hint")))
	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, boxStyle.Render(body.String()))
}

func truncateSocialNav(m *model, up bool) {
	// Two zones: drafts (if any) then actions.
	draftCount := len(m.socialDrafts)
	if draftCount > 6 {
		draftCount = 6
	}
	totalActions := int(socialActionCount)

	if up {
		if m.socialFocusActions {
			if m.socialActionCursor > 0 {
				m.socialActionCursor--
			} else if draftCount > 0 {
				m.socialFocusActions = false
				m.socialDraftCursor = draftCount - 1
			}
		} else if m.socialDraftCursor > 0 {
			m.socialDraftCursor--
		}
		return
	}
	if !m.socialFocusActions {
		if m.socialDraftCursor < draftCount-1 {
			m.socialDraftCursor++
		} else {
			m.socialFocusActions = true
			m.socialActionCursor = 0
		}
		return
	}
	if m.socialActionCursor < totalActions-1 {
		m.socialActionCursor++
	}
}

func socialMenuEnter(m *model) tea.Cmd {
	if m.socialFocusActions {
		return m.runSocialAction(SocialAction(m.socialActionCursor))
	}
	return nil
}

func openSocialMenu(m *model) {
	m.socialVisible = true
	m.socialLoading = false
	m.socialOutput = ""
	m.socialDraftCursor = 0
	m.socialActionCursor = 0
	m.socialFocusActions = len(m.socialDrafts) == 0
	m.refreshSocialDrafts()
	if len(m.socialDrafts) == 0 {
		m.socialFocusActions = true
	}
	m.setToast("📣 " + i18n.T("social.title"))
}
