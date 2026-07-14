package tui

import (
	"os"
	"testing"
)

// TestMain isolates every test in this package from the developer's
// real ~/.c4reqber by defaulting HOME to a fresh temp dir at package
// init. Tests that need to exercise persistence (e.g. resume_test.go,
// feed_persist_test.go) can still use t.Setenv("HOME", tmp) to
// override per-test, and the per-test value is restored at test end.
//
// Without this, every test that called NewApp("http://test") was
// silently reading (and sometimes writing) the developer's real
// state — causing the "test passed on my machine, failed on CI"
// class of bug, and occasionally mutating user data.
func TestMain(m *testing.M) {
	dir, err := os.MkdirTemp("", "c4reqber-tui-v9-test-*")
	if err != nil {
		panic("test setup: mkdir temp HOME: " + err.Error())
	}
	defer os.RemoveAll(dir)
	if err := os.Setenv("HOME", dir); err != nil {
		panic("test setup: setenv HOME: " + err.Error())
	}
	os.Exit(m.Run())
}
