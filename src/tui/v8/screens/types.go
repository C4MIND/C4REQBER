// Package screens provides full-screen overlays for the TUI.
package screens

import (
	tea "github.com/charmbracelet/bubbletea"
)

// Screen is the identifier for an active overlay.
type Screen int

const (
	ScreenNone Screen = iota
	ScreenDashboard
	ScreenHelp
	ScreenPalette
	ScreenExport
	ScreenHistory
	ScreenDissertation
	ScreenKnowledgeGraph
	ScreenMatrixRain
	ScreenDiagnostic
	ScreenBibliography
	ScreenOnboarding
	ScreenTRIZ
	ScreenProvider
	ScreenCache
	ScreenSocial
	ScreenGPU
	ScreenPackages
	ScreenFireworks
	ScreenAgenda
)

// Model is the interface every overlay screen must implement.
type Model interface {
	tea.Model
	Title() string
	Done() bool
}
