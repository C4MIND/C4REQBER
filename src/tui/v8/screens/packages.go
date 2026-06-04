package screens

import (
	"fmt"

	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// PackageInstaller shows installable plugin packages.
type PackageInstaller struct {
	width    int
	height   int
	cursor   int
	packages []pkgInfo
	done     bool
}

type pkgInfo struct {
	name        string
	version     string
	installed   bool
	description string
}

// NewPackageInstaller creates the package installer overlay.
func NewPackageInstaller() PackageInstaller {
	return PackageInstaller{
		packages: []pkgInfo{
			{"triz-plugin", "1.2.0", false, "TRIZ contradiction solver"},
			{"lean4-verifier", "0.9.1", false, "Formal verification via Lean 4"},
			{"arxiv-scraper", "2.0.0", true, "Enhanced arXiv integration"},
			{"bibtex-gen", "1.0.3", true, "Bibliography exporter"},
			{"news-feed", "0.5.0", false, "Real-time research news"},
			{"newton-sim", "1.1.0", false, "Physics simulation bridge"},
		},
	}
}

func (p PackageInstaller) Title() string { return "Package Installer" }
func (p PackageInstaller) Done() bool    { return p.done }

func (p PackageInstaller) Init() tea.Cmd { return nil }

func (p PackageInstaller) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		p.width = msg.Width
		p.height = msg.Height
		return p, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q":
			p.done = true
			return p, nil
		case "up", "k":
			if p.cursor > 0 {
				p.cursor--
			}
		case "down", "j":
			if p.cursor < len(p.packages)-1 {
				p.cursor++
			}
		case "enter":
			if !p.packages[p.cursor].installed {
				p.packages[p.cursor].installed = true
			}
		}
	}
	return p, nil
}

func (p PackageInstaller) View() string {
	if p.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Package Installer")
	sub := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Plugins and extensions")

	var items []string
	for i, pkg := range p.packages {
		style := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Foreground)
		cursor := "  "
		if i == p.cursor {
			style = lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Cyan).Background(styles.ActiveTheme().Border)
			cursor = "> "
		}
		status := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Success).Render("installed")
		if !pkg.installed {
			status = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Red).Render("not installed")
		}
		line := fmt.Sprintf("%s%s  %s  %s  %s", cursor, pkg.name, pkg.version, status, pkg.description)
		items = append(items, style.MaxWidth(p.width-10).Render(line))
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		sub,
		"",
		lipgloss.JoinVertical(lipgloss.Left, items...),
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Enter to install  •  Esc/Q to close"),
	)

	box := lipgloss.NewStyle().
		Width(min(70, p.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)

	return lipgloss.Place(
		p.width, p.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}
