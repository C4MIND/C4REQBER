package persist

import (
	"path/filepath"
	"testing"
)

func TestUserConfigDir_Default(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("C4REQBER_CONFIG", "")
	want := filepath.Join(tmp, ".c4reqber")
	if got := UserConfigDir(); got != want {
		t.Fatalf("UserConfigDir() = %q, want %q", got, want)
	}
}

func TestUserConfigDir_Override(t *testing.T) {
	custom := t.TempDir()
	t.Setenv("C4REQBER_CONFIG", custom)
	if got := UserConfigDir(); got != custom {
		t.Fatalf("UserConfigDir() = %q, want %q", got, custom)
	}
}

func TestDataDir_RespectsOverride(t *testing.T) {
	custom := t.TempDir()
	t.Setenv("HOME", t.TempDir())
	t.Setenv("C4REQBER_CONFIG", custom)
	if got := dataDir(); got != custom {
		t.Fatalf("dataDir() = %q, want %q", got, custom)
	}
}
