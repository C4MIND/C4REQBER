package screens

import "testing"

func TestScreenConstants(t *testing.T) {
	// Ensure Screen constants are ordered correctly and unique.
	screens := []Screen{
		ScreenNone,
		ScreenDashboard,
		ScreenHelp,
		ScreenPalette,
		ScreenExport,
		ScreenHistory,
		ScreenDissertation,
		ScreenKnowledgeGraph,
		ScreenMatrixRain,
		ScreenDiagnostic,
		ScreenBibliography,
		ScreenOnboarding,
		ScreenTRIZ,
		ScreenProvider,
		ScreenCache,
		ScreenSocial,
		ScreenGPU,
		ScreenPackages,
		ScreenFireworks,
		ScreenAgenda,
	}
	seen := make(map[Screen]bool)
	for i, s := range screens {
		if int(s) != i {
			t.Errorf("screen constant out of order: got %d, want %d", s, i)
		}
		if seen[s] {
			t.Errorf("duplicate screen constant: %d", s)
		}
		seen[s] = true
	}
}
