package widgets

import (
	"testing"

	"c4tui/config"
)

func TestCubeMascot_Emotions(t *testing.T) {
	for _, e := range []Emotion{EmotionIdle, EmotionThinking, EmotionHappy, EmotionSurprised, EmotionError} {
		if e == "" {
			t.Fatalf("empty emotion value")
		}
	}
}

func TestCubeMascot_View(t *testing.T) {
	cfg := config.Default()
	m := NewMascot(cfg)
	m.SetEmotion(EmotionHappy)
	v := m.View(30)
	if v == "" {
		t.Fatal("empty mascot view")
	}
}

func TestCubeMascot_UpdateIdle(t *testing.T) {
	cfg := config.Default()
	m := NewMascot(cfg)
	m.SetEmotion(EmotionIdle)
	m.FrameIdx = 0
	newM, cmd := m.Update(IdleTickMsg{})
	if newM.FrameIdx != 1 {
		t.Fatalf("expected frame 1, got %d", newM.FrameIdx)
	}
	if cmd == nil {
		t.Fatal("expected next tick command")
	}
}

func TestCubeMascot_UpdateThinking(t *testing.T) {
	cfg := config.Default()
	m := NewMascot(cfg)
	m.SetEmotion(EmotionThinking)
	m.FrameIdx = 0
	newM, cmd := m.Update(IdleTickMsg{})
	if newM.FrameIdx != 1 {
		t.Fatalf("expected frame advance to 1, got %d", newM.FrameIdx)
	}
	if cmd == nil {
		t.Fatal("expected next tick command")
	}
}

func TestCubeMascot_BuildCube(t *testing.T) {
	cfg := config.Default()
	m := NewMascot(cfg)
	m.SetEmotion(EmotionIdle)
	m.CurrentPhase = 2
	lines := m.buildCube()
	if len(lines) != 6 {
		t.Fatalf("expected 6 lines, got %d", len(lines))
	}
	for i, line := range lines {
		if len([]rune(line)) == 0 {
			t.Fatalf("line %d is empty", i)
		}
	}
}

func TestCubeMascot_FramesCount(t *testing.T) {
	if len(cubeFrames) != 3 {
		t.Fatalf("expected 3 frames, got %d", len(cubeFrames))
	}
	for fi, frame := range cubeFrames {
		if len(frame) != 6 {
			t.Fatalf("frame %d expected 6 lines, got %d", fi, len(frame))
		}
		for li, line := range frame {
			if len([]rune(line)) == 0 {
				t.Fatalf("frame %d line %d is empty", fi, li)
			}
		}
	}
}

func TestCubeMascot_PipelineState(t *testing.T) {
	cfg := config.Default()
	m := NewMascot(cfg)
	m.SetPipelineState(true, 3)
	if !m.PipelineRunning {
		t.Fatal("expected pipeline running")
	}
	if m.CurrentPhase != 3 {
		t.Fatalf("expected phase 3, got %d", m.CurrentPhase)
	}
}

func TestCubeMascot_Jump(t *testing.T) {
	cfg := config.Default()
	m := NewMascot(cfg)
	m.Jump()
	if !m.Jumping {
		t.Fatal("expected jumping")
	}
	// Simulate tick during jump — frame should advance rapidly
	newM, _ := m.Update(IdleTickMsg{})
	if !newM.Jumping {
		t.Fatal("expected still jumping after first tick")
	}
}

func TestCubeMascot_ThemePalette(t *testing.T) {
	frame, accent, c4r := cubeThemePalette()
	if frame == "" || accent == "" || c4r == "" {
		t.Fatal("theme palette returned empty colors")
	}
}
