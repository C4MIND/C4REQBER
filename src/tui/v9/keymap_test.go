package tui

import (
	"runtime"
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

func TestKeyMap_DetectPlatform(t *testing.T) {
	p := DetectPlatform()
	switch p {
	case PlatformDarwin, PlatformLinux, PlatformWindows, PlatformBSD, PlatformUnknown:
		// ok
	default:
		t.Errorf("DetectPlatform returned unknown value: %q", p)
	}
	if p.Display() == "" {
		t.Error("Platform.Display() returned empty string")
	}
}

func TestKeyMap_NewKeyMap_AllPlatforms(t *testing.T) {
	platforms := []Platform{
		PlatformDarwin, PlatformLinux, PlatformWindows, PlatformBSD, PlatformUnknown,
	}
	for _, p := range platforms {
		km := NewKeyMap(p)
		if km.Platform != p {
			t.Errorf("NewKeyMap(%q).Platform = %q, want %q", p, km.Platform, p)
		}
		for _, a := range AllActions() {
			if km.Label(a) == "" {
				t.Errorf("platform %q: Action %q has no primary label", p, a)
			}
		}
	}
}

func TestKeyMap_Darwin_UsesCmdPrefix(t *testing.T) {
	km := NewKeyMap(PlatformDarwin)
	if got := km.Label(ActReauth); got != "Cmd+L" {
		t.Errorf("darwin ActReauth label = %q, want Cmd+L", got)
	}
	if got := km.Label(ActSettings); got != "Cmd+," {
		t.Errorf("darwin ActSettings label = %q, want Cmd+,", got)
	}
	if got := km.Label(ActNewTab); got != "Cmd+T" {
		t.Errorf("darwin ActNewTab label = %q, want Cmd+T", got)
	}
	if got := km.Label(ActTier); got != "Cmd+Y" {
		t.Errorf("darwin ActTier primary label = %q, want Cmd+Y", got)
	}
	allTier := km.Labels(ActTier)
	hasCtrl := false
	for _, l := range allTier {
		if l == "Ctrl+Y" {
			hasCtrl = true
		}
	}
	if !hasCtrl {
		t.Errorf("darwin ActTier should keep Ctrl+Y alias, got %v", allTier)
	}
}

func TestKeyMap_Linux_UsesCtrlPrefix(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	if got := km.Label(ActReauth); got != "Ctrl+L" {
		t.Errorf("linux ActReauth label = %q, want Ctrl+L", got)
	}
	if got := km.Label(ActSettings); got != "Ctrl+," {
		t.Errorf("linux ActSettings label = %q, want Ctrl+,", got)
	}
	if got := km.Label(ActNewTab); got != "Ctrl+T" {
		t.Errorf("linux ActNewTab label = %q, want Ctrl+T", got)
	}
}

func TestKeyMap_Windows_UsesCtrlPrefix(t *testing.T) {
	km := NewKeyMap(PlatformWindows)
	if got := km.Label(ActReauth); got != "Ctrl+L" {
		t.Errorf("windows ActReauth label = %q, want Ctrl+L", got)
	}
}

func TestKeyMap_Matches_BubbleteaKeys(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	cases := []struct {
		action Action
		key    string
	}{
		{ActQuit, "ctrl+c"},
		{ActRun, "enter"},
		{ActRun, " "},
		{ActHelp, "?"},
		{ActCycleMode, "tab"},
		{ActReauth, "ctrl+l"},
		{ActSearch, "/"},
		{ActCopy, "c"},
		// j/k drive card focus (v9.13); Jump moved to ctrl+j to free them.
		{ActFocusNext, "j"},
		{ActFocusPrev, "k"},
		{ActJump, "ctrl+j"},
		{ActTier, "ctrl+y"},
		{ActSettings, "ctrl+,"},
		{ActUp, "up"},
		{ActDown, "down"},
		{ActColorProfile, "ctrl+shift+p"},
		{ActNewTab, "ctrl+t"},
		{ActEscape, "ctrl+."},
		{ActLang, "l"},
		{ActLang, "shift+l"},
	}
	for _, c := range cases {
		if !km.Matches(c.action, c.key) {
			t.Errorf("Matches(%q, %q) = false, want true", c.action, c.key)
		}
	}
}

func TestKeyMap_Matches_Darwin_Aliases(t *testing.T) {
	km := NewKeyMap(PlatformDarwin)
	if !km.Matches(ActTier, "ctrl+y") {
		t.Error("darwin: ctrl+y should still match ActTier (alias)")
	}
	if !km.Matches(ActTier, "cmd+y") {
		t.Error("darwin: cmd+y should match ActTier")
	}
	if !km.Matches(ActReauth, "cmd+l") {
		t.Error("darwin: cmd+l should match ActReauth")
	}
	if !km.Matches(ActReauth, "ctrl+l") {
		t.Error("darwin: ctrl+l should match ActReauth (alias)")
	}
	if !km.Matches(ActSettings, "cmd+,") {
		t.Error("darwin: cmd+, should match ActSettings")
	}
}

func TestKeyMap_Matches_CaseInsensitive(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	if !km.Matches(ActQuit, "CTRL+C") {
		t.Error("uppercase CTRL+C should match ActQuit")
	}
	if !km.Matches(ActRun, "ENTER") {
		t.Error("uppercase ENTER should match ActRun")
	}
}

func TestKeyMap_Matches_Negative(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	if km.Matches(ActQuit, "x") {
		t.Error("'x' should not match ActQuit")
	}
	if km.Matches(ActTier, "tab") {
		t.Error("'tab' should not match ActTier")
	}
	if km.Matches(ActRun, "") {
		t.Error("empty key should not match")
	}
}

func TestKeyMap_Labels_AllActions(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	for _, a := range AllActions() {
		labels := km.Labels(a)
		if len(labels) == 0 {
			t.Errorf("Action %q has no labels", a)
		}
		for _, l := range labels {
			if l == "" {
				t.Errorf("Action %q has empty label in %v", a, labels)
			}
		}
	}
}

func TestKeyMap_HelpRows_OrderedAndComplete(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	rows := km.HelpRows()
	if len(rows) == 0 {
		t.Fatal("HelpRows returned no rows")
	}
	for i, r := range rows {
		if len(r.Keys) == 0 {
			t.Errorf("HelpRow[%d] (%q) has no keys", i, r.Action)
		}
		if r.Desc == "" {
			t.Errorf("HelpRow[%d] (%q) has no description key", i, r.Action)
		}
	}
}

func TestKeyMap_FormatKeyList(t *testing.T) {
	if got := FormatKeyList([]string{"Cmd+L", "Ctrl+L"}); got != "Cmd+L / Ctrl+L" {
		t.Errorf("FormatKeyList = %q, want %q", got, "Cmd+L / Ctrl+L")
	}
	if got := FormatKeyList(nil); got != "" {
		t.Errorf("FormatKeyList(nil) = %q, want empty", got)
	}
}

func TestKeyMap_SortedKeys_Deterministic(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	keys := km.SortedKeys()
	if len(keys) == 0 {
		t.Fatal("SortedKeys returned no keys")
	}
	for i := 1; i < len(keys); i++ {
		if keys[i-1] >= keys[i] {
			t.Errorf("SortedKeys not sorted at index %d: %q >= %q", i, keys[i-1], keys[i])
		}
	}
}

func TestKeyMap_Label_UnknownAction(t *testing.T) {
	km := NewKeyMap(PlatformLinux)
	if got := km.Label(Action("nonexistent_action_xyz")); got != "" {
		t.Errorf("Label(unknown) = %q, want empty", got)
	}
	if got := km.Matches(Action("nonexistent"), "any"); got {
		t.Error("Matches(unknown action, any key) = true, want false")
	}
}

func TestKeyMap_AllActions_Unique(t *testing.T) {
	seen := map[Action]bool{}
	for _, a := range AllActions() {
		if seen[a] {
			t.Errorf("duplicate action: %q", a)
		}
		seen[a] = true
	}
}

func TestKeyMap_Keymap_AttachedToModel(t *testing.T) {
	m := NewAppFresh("http://localhost:1")
	if m.keymap == nil {
		t.Fatal("NewAppFresh did not initialize keymap")
	}
	expected := runtime.GOOS
	if string(m.keymap.Platform) != expected {
		t.Errorf("keymap.Platform = %q, want %q", m.keymap.Platform, expected)
	}
}

func TestKeyMap_Update_RoutesTabViaKeymap(t *testing.T) {
	m := NewAppFresh("http://localhost:1")
	if m.keymap == nil {
		t.Fatal("keymap not initialized")
	}
	// Capture the mode before and after pressing Tab.
	startMode := m.mode
	updated, _ := m.Update(tea.KeyPressMsg{Code: '\t'})
	m2, ok := updated.(*model)
	if !ok || m2 == nil {
		t.Fatal("Update returned non-model")
	}
	// Mode should have advanced (cycled past DISCOVER).
	if m2.mode == startMode {
		t.Errorf("Tab key did not change mode (still %q)", startMode)
	}
}

func TestKeyMap_Update_PlatformRespectsKeymap(t *testing.T) {
	// Verify that pressing a key whose label is "Cmd+L" on darwin
	// does the same thing as "Ctrl+L" on linux.
	kmDarwin := NewKeyMap(PlatformDarwin)
	kmLinux := NewKeyMap(PlatformLinux)
	// Both should have ActReauth reachable by *some* key.
	if !kmDarwin.Matches(ActReauth, "cmd+l") {
		t.Error("darwin: cmd+l should match ActReauth")
	}
	if !kmLinux.Matches(ActReauth, "ctrl+l") {
		t.Error("linux: ctrl+l should match ActReauth")
	}
}

func TestKeyMap_NoRegressionsInKeyList(t *testing.T) {
	// All actions should be in the sorted key list.
	km := NewKeyMap(PlatformLinux)
	keys := km.SortedKeys()
	keySet := map[string]bool{}
	for _, k := range keys {
		keySet[k] = true
	}
	for _, a := range AllActions() {
		if !keySet[string(a)] {
			t.Errorf("Action %q not in SortedKeys()", a)
		}
	}
}

func TestKeyMap_ReauthStringContainsLabel(t *testing.T) {
	// Sanity: the resolved label should appear in the Matches check.
	km := NewKeyMap(PlatformLinux)
	label := km.Label(ActReauth)
	if !strings.Contains(label, "Ctrl") {
		t.Errorf("linux ActReauth label %q should contain Ctrl", label)
	}
	km2 := NewKeyMap(PlatformDarwin)
	label2 := km2.Label(ActReauth)
	if !strings.Contains(label2, "Cmd") {
		t.Errorf("darwin ActReauth label %q should contain Cmd", label2)
	}
}
