package tui

import (
	"math/rand"
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
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

// TestBuildDissolveSequence_Shape verifies the web-parity dissolve:
// 16 forms (seed, noise, 13 cube-glitch, clean cube, final), all padded
// to the same width, with a valid C4R start row and cell map.
func TestBuildDissolveSequence_Shape(t *testing.T) {
	const h = 40
	rng := rand.New(rand.NewSource(42))
	forms, c4rStart, cells := buildDissolveSequence(h, v8RawANSISmall, false, rng)
	wantForms := 2 + splashDissolveGlitchForms + 2
	if len(forms) != wantForms {
		t.Fatalf("expected %d forms, got %d", wantForms, len(forms))
	}
	if c4rStart < 0 {
		t.Fatal("c4rStart should be >= 0 for non-compact art")
	}
	if len(cells) == 0 {
		t.Fatal("cell map should not be empty")
	}
	width := lenRunes(forms[0][0])
	for i, f := range forms {
		for j, l := range f {
			if lenRunes(l) != width {
				t.Errorf("form %d line %d width %d != %d (all forms must share one width)",
					i, j, lenRunes(l), width)
			}
		}
	}
}

// TestBuildDissolveSequence_CellsMatchFinal verifies every cell in the
// map points at a '1' in the aligned final form — the invariant that
// makes mid-animation C4R geometry identical to the final geometry.
func TestBuildDissolveSequence_CellsMatchFinal(t *testing.T) {
	const h = 40
	rng := rand.New(rand.NewSource(42))
	forms, c4rStart, cells := buildDissolveSequence(h, v8RawANSISmall, false, rng)
	final := forms[len(forms)-1]
	count1 := 0
	for y := c4rStart; y < len(final); y++ {
		for _, r := range []rune(final[y]) {
			if r == '1' {
				count1++
			}
		}
	}
	if len(cells) != count1 {
		t.Errorf("cell map has %d cells, final form has %d '1' runes", len(cells), count1)
	}
	for _, c := range cells {
		y, x := c[0], c[1]
		if y < c4rStart || y >= len(final) {
			t.Fatalf("cell row %d outside C4R block [%d, %d)", y, c4rStart, len(final))
		}
		runes := []rune(final[y])
		if x >= len(runes) || runes[x] != '1' {
			t.Errorf("cell (%d,%d) does not point at '1' in final form", y, x)
		}
	}
}

// TestSplash_DissolveNeverBendsC4R runs the model through the entire
// dissolve tick-by-tick and asserts every '1' visible in the C4R region
// sits at a coordinate from the final form's cell map — i.e. the letter
// walls and bars can never appear shifted mid-animation (web parity).
func TestSplash_DissolveNeverBendsC4R(t *testing.T) {
	m := NewSplash("v9.14.0", "")
	m.width, m.height = 200, 50
	u, _ := m.Update(tea.KeyPressMsg{Code: ' '}) // crystal → dissolve
	mm := u.(SplashModel)
	if mm.phase != "dissolve" {
		t.Fatalf("phase = %s, want dissolve", mm.phase)
	}
	if mm.c4rStartRow < 0 || len(mm.c4rCells) == 0 {
		t.Fatal("dissolve must carry a C4R cell map")
	}
	valid := map[[2]int]bool{}
	for _, c := range mm.c4rCells {
		valid[c] = true
	}
	total := mm.totalMorphTicks()
	if got := total * int(splashTickInterval/time.Millisecond); got < 10000 {
		t.Errorf("dissolve duration %dms, want >= 10s (web parity ~11.25s)", got)
	}
	for tick := 0; tick <= total; tick++ {
		u, _ = mm.Update(splashTickMsg{tick: tick})
		mm = u.(SplashModel)
		for y := mm.c4rStartRow; y < len(mm.morphLines); y++ {
			for x, r := range []rune(mm.morphLines[y]) {
				if r == '1' && !valid[[2]int{y, x}] {
					t.Fatalf("tick %d: '1' at (%d,%d) not in final cell map", tick, y, x)
				}
			}
		}
	}
	if mm.phase != "waiting" {
		t.Errorf("after %d ticks phase = %s, want waiting", total, mm.phase)
	}
	// Entering waiting must not replay the bloom (would re-assemble C4R).
	if mm.bloomFrame != splashBloomFrames {
		t.Errorf("bloomFrame = %d, want %d (no bloom replay)", mm.bloomFrame, splashBloomFrames)
	}
}

// TestPaintC4RCellsSplash_ExactCoordinates verifies the assembly overlay
// only ever paints '1' at coordinates present in the cell map, at any
// partial reveal count.
func TestPaintC4RCellsSplash_ExactCoordinates(t *testing.T) {
	const h = 40
	rng := rand.New(rand.NewSource(42))
	forms, c4rStart, cells := buildDissolveSequence(h, v8RawANSISmall, false, rng)
	final := forms[len(forms)-1]
	valid := map[[2]int]bool{}
	for _, c := range cells {
		valid[c] = true
	}
	for _, count := range []int{0, 1, len(cells) / 3, len(cells) / 2, len(cells) - 1, len(cells)} {
		lines := make([]string, len(final))
		for i, l := range final {
			if i >= c4rStart {
				lines[i] = strings.Repeat(" ", lenRunes(l))
			} else {
				lines[i] = l
			}
		}
		paintC4RCellsSplash(lines, cells, count, splashC4RFringe, 7, rng)
		for y := c4rStart; y < len(lines); y++ {
			for x, r := range []rune(lines[y]) {
				if r == '1' && !valid[[2]int{y, x}] {
					t.Errorf("count=%d: '1' painted at (%d,%d) which is not in the cell map", count, y, x)
				}
			}
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
