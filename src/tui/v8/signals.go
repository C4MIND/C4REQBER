package main

import (
	"os"
	"os/signal"

	tea "github.com/charmbracelet/bubbletea"
)

// shutdownMsg is sent when an OS signal requests graceful termination.
type shutdownMsg struct{}

// listenForSignals returns a command that listens for SIGINT/SIGTERM.
func listenForSignals() tea.Cmd {
	return func() tea.Msg {
		c := make(chan os.Signal, 1)
		signal.Notify(c, os.Interrupt)
		<-c
		return shutdownMsg{}
	}
}
