// Headless e2e probe — used by CI for live integration smoke tests.
// Usage: c4tui-v9 probe <query>
package main

import (
	"fmt"
	"os"

	"github.com/figuramax/c4reqber-tui-v9/probe"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: c4tui-v9 probe <query>")
		os.Exit(1)
	}
	query := os.Args[1]
	apiURL := os.Getenv("C4_API_URL")
	if apiURL == "" {
		apiURL = "http://127.0.0.1:8000"
	}
	if err := probe.Run(apiURL, query); err != nil {
		fmt.Fprintln(os.Stderr, "probe error:", err)
		os.Exit(1)
	}
}
