package tui

import (
	"math/rand"
	"strings"
	"testing"
)

// TestBuildCrystalFrames_AllFramesAtSameXCenter verifies that
// the 12 crystal-phase frames have the same visual X-center, so
// the cube doesn't "jump" or "drift" during the 12-frame animation
// (user complaint: "фиолетовый в начале прыгает и приземляется
// где-то слево внизу").
func TestBuildCrystalFrames_AllFramesAtSameXCenter(t *testing.T) {
	const h = 40
	rng := rand.New(rand.NewSource(42))
	forms := buildCrystalFrames(v8RawANSISmall, h, false, rng, FinalFormTargetCenterSplash(h, false))
	if len(forms) != 12 {
		t.Fatalf("expected 12 frames, got %d", len(forms))
	}
	// Compute visual center of each frame's first non-blank row.
	centers := make([]float64, len(forms))
	for i, f := range forms {
		centers[i] = visualCenterColumnSplash(f)
		if centers[i] == 0 && i < 4 {
			for j, l := range f {
				if len(l) > 0 {
					t.Logf("frame %d L%d (%d chars): %q", i, j, len(l), l[:min(50, len(l))])
				} else {
					t.Logf("frame %d L%d (empty)", i, j)
				}
				if j > 3 {
					break
				}
			}
		}
	}
	// All centers should be within 1.0 col of each other.
	first := centers[0]
	for i, c := range centers {
		diff := c - first
		if diff < 0 {
			diff = -diff
		}
		if diff > 1.0 {
			t.Errorf("frame %d center %.1f differs from frame 0 center %.1f by %.1f cols (all frames should align)",
				i, c, first, diff)
		}
	}
}

// TestBuildCrystalFrames_PurpleCubeWithinCompositeWidth verifies
// the purple cube (form 0, full seedArt) is clipped to the
// composite's max width — not the full 170 chars of v8RawANSISmall.
// Without this clip, the purple cube is centered at col 84 on a
// 200-wide screen while the final form is at col 53, producing a
// 30+ col horizontal jump during the dissolve.
func TestBuildCrystalFrames_PurpleCubeWithinCompositeWidth(t *testing.T) {
	const h = 40
	final := buildSplashFinalForm(h, false)
	compositeMaxW := 0
	for _, l := range final {
		if w := contentWidthSplash(l); w > compositeMaxW {
			compositeMaxW = w
		}
	}
	if compositeMaxW == 0 {
		t.Fatal("could not determine composite max width")
	}
	t.Logf("compositeMaxW = %d", compositeMaxW)
	rng := rand.New(rand.NewSource(42))
	forms := buildCrystalFrames(v8RawANSISmall, h, false, rng, FinalFormTargetCenterSplash(h, false))
	// After AlignFormsCenterX, all forms are aligned to the same
	// X-center, so the post-alignment width is compositeMaxW + shift.
	// We allow up to compositeMaxW + 5 cols of headroom for the
	// shift, but the purple cube (frame 0) BEFORE shift must be
	// at most compositeMaxW wide.
	for i, f := range forms {
		// Only check frame 0 (purple cube, pre-shift copy is forms[0] before
		// AlignFormsCenterX mutates it). Since AlignFormsCenterX runs
		// in-place, we can only verify the post-alignment width is
		// reasonable: <= compositeMaxW + 8 (allow for shift + 1).
		for j, l := range f {
			w := contentWidthSplash(l)
			maxAllowed := compositeMaxW + 8
			if w > maxAllowed {
				t.Errorf("frame %d line %d has content width %d, exceeds composite+8=%d",
					i, j, w, maxAllowed)
			}
		}
	}
}

// TestBuildSplashForms_AllFormsAtSameXCenter verifies that
// the dissolve forms [purple, noise, C4R-intermediate, final]
// all have the same visual X-center.
func TestBuildSplashForms_AllFormsAtSameXCenter(t *testing.T) {
	const h = 40
	rng := rand.New(rand.NewSource(42))
	forms := buildSplashForms(h, v8RawANSISmall, false, rng)
	if len(forms) != 4 {
		t.Fatalf("expected 4 forms, got %d", len(forms))
	}
	centers := make([]float64, len(forms))
	for i, f := range forms {
		centers[i] = visualCenterColumnSplash(f)
	}
	first := centers[0]
	for i, c := range centers {
		diff := c - first
		if diff < 0 {
			diff = -diff
		}
		if diff > 2.0 {
			t.Errorf("form %d center %.1f differs from form 0 center %.1f by %.1f cols",
				i, c, first, diff)
		}
	}
}

// TestAlignFormsCenterX_LeftShiftIsNoop verifies that
// shiftLinesBySplash treats negative shifts as no-op (not as
// panic from strings.Repeat with negative count).
func TestAlignFormsCenterX_LeftShiftIsNoop(t *testing.T) {
	// Three forms, each at a different (positive) content width.
	// All should align to the same target without panicking.
	forms := [][]string{
		{"  X  ", " XXX "},
		{" YY ", "  YYY"},
		{"ZZZZ"},
	}
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("AlignFormsCenterX panicked: %v", r)
		}
	}()
	out := AlignFormsCenterX(forms, 3.5)
	if len(out) != 3 {
		t.Errorf("expected 3 forms back, got %d", len(out))
	}
	// After alignment, all forms should have the same X-center.
	c0 := visualCenterColumnSplash(out[0])
	for i := 1; i < len(out); i++ {
		ci := visualCenterColumnSplash(out[i])
		diff := ci - c0
		if diff < 0 {
			diff = -diff
		}
		if diff > 1.0 {
			t.Errorf("aligned form %d center %.1f differs from form 0 center %.1f", i, ci, c0)
		}
	}
	// All forms must still contain their original glyphs (no data loss).
	for i, f := range out {
		original := strings.Join(forms[i], "")
		aligned := strings.Join(f, "")
		// Each form should still contain all its original non-space chars.
		for _, r := range original {
			if r == ' ' {
				continue
			}
			if !strings.ContainsRune(aligned, r) {
				t.Errorf("form %d lost char %q after alignment", i, r)
			}
		}
	}
}
