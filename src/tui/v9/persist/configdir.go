package persist

import (
	"os"
	"path/filepath"
)

// UserConfigDir returns the unified config directory:
// $C4REQBER_CONFIG when set, otherwise ~/.c4reqber.
// Matches src/config/paths.py CONFIG_DIR.
func UserConfigDir() string {
	if p := os.Getenv("C4REQBER_CONFIG"); p != "" {
		return p
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return ".c4reqber"
	}
	return filepath.Join(home, ".c4reqber")
}

// dataDir resolves where TUI data files live. When C4REQBER_CONFIG is set,
// that path is authoritative. Otherwise prefer ~/.c4reqber, with a one-time
// fallback to ~/.config/c4reqber for legacy XDG installs.
func dataDir() string {
	if os.Getenv("C4REQBER_CONFIG") != "" {
		return UserConfigDir()
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return ".c4reqber"
	}
	dir := filepath.Join(home, ".c4reqber")
	if _, statErr := os.Stat(dir); os.IsNotExist(statErr) {
		return filepath.Join(home, ".config", "c4reqber")
	}
	return dir
}
