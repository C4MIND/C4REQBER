package tui

import (
	"fmt"
	"strings"
	"time"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// Achievement kinds
type AchievementKind int

const (
	AchFirstDiscovery AchievementKind = iota
	AchQualityS
	AchMultiPaper
	AchTenDiscoveries
	AchSpeedster
	AchLinguist
	AchStreak
)

type Achievement struct {
	Kind        AchievementKind
	Name        string // i18n key
	Description string // i18n key
	Unlocked    bool
	UnlockedAt  time.Time
}

// AchievementSystem tracks user achievements.
type AchievementSystem struct {
	Items      []Achievement
	Unlocked   int
	Total      int
	LastUnlock time.Time
}

func NewAchievements() *AchievementSystem {
	return &AchievementSystem{
		Items: []Achievement{
			{Kind: AchFirstDiscovery, Name: "achievement.first.name", Description: "achievement.first.desc"},
			{Kind: AchQualityS, Name: "achievement.qualityS.name", Description: "achievement.qualityS.desc"},
			{Kind: AchMultiPaper, Name: "achievement.multiPaper.name", Description: "achievement.multiPaper.desc"},
			{Kind: AchTenDiscoveries, Name: "achievement.ten.name", Description: "achievement.ten.desc"},
			{Kind: AchSpeedster, Name: "achievement.speed.name", Description: "achievement.speed.desc"},
			{Kind: AchLinguist, Name: "achievement.linguist.name", Description: "achievement.linguist.desc"},
			{Kind: AchStreak, Name: "achievement.streak.name", Description: "achievement.streak.desc"},
		},
		Total: 7,
	}
}

// Check looks for new unlocks based on run state.
// Pass:
//   - discoveries int (total completed discoveries)
//   - lastQuality float (0.0..1.0 from last hypothesis)
//   - papersCount int (papers in last discovery)
//   - secondsTaken float
//   - langsUsed []string (distinct lang codes user has seen)
func (a *AchievementSystem) Check(discoveries int, lastQuality float64, papersCount int, secondsTaken float64, langsUsed []string) []Achievement {
	justUnlocked := []Achievement{}
	for i := range a.Items {
		ach := &a.Items[i]
		if ach.Unlocked {
			continue
		}
		var unlock bool
		switch ach.Kind {
		case AchFirstDiscovery:
			unlock = discoveries >= 1
		case AchQualityS:
			unlock = lastQuality >= 0.8
		case AchMultiPaper:
			unlock = papersCount >= 3
		case AchTenDiscoveries:
			unlock = discoveries >= 10
		case AchSpeedster:
			unlock = secondsTaken > 0 && secondsTaken < 30
		case AchLinguist:
			unlock = len(langsUsed) >= 3
		case AchStreak:
			unlock = discoveries >= 5 // simplified: 5 in session
		}
		if unlock {
			ach.Unlocked = true
			ach.UnlockedAt = time.Now()
			a.Unlocked++
			a.LastUnlock = ach.UnlockedAt
			justUnlocked = append(justUnlocked, *ach)
		}
	}
	return justUnlocked
}

// renderAchievementCard renders an achievement unlock banner.
func renderAchievementCard(a Achievement, width int) string {
	style := lipgloss.NewStyle().Width(width - 2).Padding(0, 1).Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("3"))
	title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3")).Render("🏆 " + i18n.T(a.Name))
	body := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(i18n.T(a.Description))
	stamp := lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(a.UnlockedAt.Format("15:04:05"))
	return style.Render(title + "  " + stamp + "\n" + body)
}

// cycleLangName returns the next lang code, or "—" if no change.
func cycleLangName(current i18n.Lang) i18n.Lang {
	cycle := []i18n.Lang{i18n.LangEN, i18n.LangRU, i18n.LangZH, i18n.LangJA, i18n.LangDE, i18n.LangAR, i18n.LangHI}
	for i, l := range cycle {
		if l == current {
			return cycle[(i+1)%len(cycle)]
		}
	}
	return i18n.LangEN
}

// joinStrings helper for LangList
func joinStrings(parts []string, sep string) string {
	return strings.Join(parts, sep)
}

// fmtDiscoveryMeta is a helper for the discovery complete card.
func fmtDiscoveryMeta(quality float64, paperCount int) string {
	return fmt.Sprintf("quality=%.0f%% · papers=%d", quality*100, paperCount)
}
