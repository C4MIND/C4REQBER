package tui

import "github.com/figuramax/c4reqber-tui-v9/persist"

// userConfigDir returns ~/.c4reqber or $C4REQBER_CONFIG (matches src/config/paths.py).
func userConfigDir() string {
	return persist.UserConfigDir()
}
