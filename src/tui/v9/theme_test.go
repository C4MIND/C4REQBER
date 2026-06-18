package tui

import "testing"

func TestThemeNewForAllProfiles(t *testing.T) {
	profiles := []ColorProfile{
		ProfileDefault, ProfileHighContrast, ProfileProtanopia,
		ProfileDeuteranopia, ProfileTritanopia, ProfileMonochrome,
		ProfileSolarizedDark,
	}
	for _, p := range profiles {
		th := NewTheme(p)
		if th == nil {
			t.Errorf("NewTheme(%d) returned nil", p)
		}
		if th.Profile() != p {
			t.Errorf("Profile() = %d, want %d", th.Profile(), p)
		}
	}
}

func TestThemeStyleFallsBackGracefully(t *testing.T) {
	th := NewTheme(ProfileDefault)
	s := th.Style("nonexistent")
	// Should not panic; Style() returns empty Style for unknown names
	_ = s
}

func TestThemeCardKindStyle(t *testing.T) {
	th := NewTheme(ProfileDefault)
	// Every kind returns a Style without panicking
	for _, kind := range []CardKind{CardEmpty, CardPhase, CardHypothesis, CardPaper, CardCode, CardError, CardSimulation} {
		_ = th.CardKindStyle(kind)
	}
}

func TestThemeConnectionStyle(t *testing.T) {
	th := NewTheme(ProfileSolarizedDark)
	// Each state returns a Style
	for _, s := range []ConnectionState{ConnLive, ConnPolling, ConnOffline, ConnUnknown} {
		_ = th.ConnectionStyle(s)
	}
}

func TestThemeColorProfileString(t *testing.T) {
	cases := map[ColorProfile]string{
		ProfileDefault:        "default",
		ProfileHighContrast:   "high-contrast",
		ProfileProtanopia:     "protanopia",
		ProfileDeuteranopia:   "deuteranopia",
		ProfileTritanopia:     "tritanopia",
		ProfileMonochrome:     "monochrome",
		ProfileSolarizedDark:  "solarized-dark",
	}
	for p, want := range cases {
		if got := p.String(); got != want {
			t.Errorf("ColorProfile(%d).String() = %q, want %q", p, got, want)
		}
	}
}

func TestSolarizedDarkProfileIsDifferentFromDefault(t *testing.T) {
	def := ColorsFor(ProfileDefault)
	sol := ColorsFor(ProfileSolarizedDark)
	if def["primary"] == sol["primary"] {
		t.Error("solarized-dark should differ from default at primary")
	}
	if def["success"] == sol["success"] {
		t.Error("solarized-dark should differ from default at success")
	}
}

func TestProfileFromStringSolarized(t *testing.T) {
	cases := map[string]ColorProfile{
		"solarized-dark": ProfileSolarizedDark,
		"solarized":      ProfileSolarizedDark,
		"solar":          ProfileSolarizedDark,
		"default":        ProfileDefault,
		"":               ProfileDefault,
	}
	for s, want := range cases {
		got, ok := ProfileFromString(s)
		if !ok {
			t.Errorf("ProfileFromString(%q) should succeed", s)
		}
		if got != want {
			t.Errorf("ProfileFromString(%q) = %d, want %d", s, got, want)
		}
	}
}
