package main

import (
	"testing"
	"time"

	"c4tui/config"
	"c4tui/widgets"
)

func TestSplitHeight(t *testing.T) {
	tests := []struct {
		name     string
		total    int
		ratioNum int
		ratioDen int
		minA     int
		minB     int
		wantA    int
		wantB    int
	}{
		{"exact fit", 100, 1, 2, 10, 10, 50, 50},
		{"priority a when total tight", 15, 1, 2, 10, 10, 15, 0},
		{"both mins satisfied", 30, 1, 2, 10, 10, 15, 15},
		{"clamp a to min", 25, 1, 10, 10, 10, 10, 15},
		{"clamp b to min", 25, 9, 10, 10, 10, 15, 10},
		{"total zero", 0, 1, 2, 1, 1, 0, 0},
		{"negative total", -5, 1, 2, 1, 1, -5, 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotA, gotB := splitHeight(tt.total, tt.ratioNum, tt.ratioDen, tt.minA, tt.minB)
			if gotA != tt.wantA || gotB != tt.wantB {
				t.Errorf("splitHeight(%d, %d, %d, %d, %d) = (%d, %d), want (%d, %d)",
					tt.total, tt.ratioNum, tt.ratioDen, tt.minA, tt.minB,
					gotA, gotB, tt.wantA, tt.wantB)
			}
		})
	}
}

func makeTestModel(width, height int) model {
	cfg := config.Default()
	return model{
		Width:  width,
		Height: height,
		Cfg:    cfg,
		Chat:   widgets.NewChat(cfg),
		Help:   widgets.NewHelp(cfg),
		Pipeline: func() widgets.Pipeline {
			p := widgets.NewPipeline(cfg)
			p.Running = false
			p.StartTime = time.Time{}
			return p
		}(),
	}
}

func TestComputeLayout_Wide(t *testing.T) {
	m := makeTestModel(120, 40)
	l := m.computeLayout()

	if l.veryNarrow {
		t.Error("expected not veryNarrow for 120 cols")
	}
	if l.narrow {
		t.Error("expected not narrow for 120 cols")
	}
	if l.leftW+l.midW+l.rightW != m.Width {
		t.Errorf("columns don't sum to width: %d + %d + %d = %d, want %d",
			l.leftW, l.midW, l.rightW, l.leftW+l.midW+l.rightW, m.Width)
	}
	if l.bodyH <= 0 {
		t.Errorf("bodyH should be positive, got %d", l.bodyH)
	}
	if !l.showCube {
		t.Error("expected showCube on wide screen")
	}
}

func TestComputeLayout_Narrow(t *testing.T) {
	m := makeTestModel(80, 40)
	l := m.computeLayout()

	if l.veryNarrow {
		t.Error("expected not veryNarrow for 80 cols")
	}
	if !l.narrow {
		t.Error("expected narrow for 80 cols")
	}
	if l.leftW+l.rightW != m.Width {
		t.Errorf("columns don't sum to width: %d + %d = %d, want %d",
			l.leftW, l.rightW, l.leftW+l.rightW, m.Width)
	}
	if l.midW != l.rightW {
		t.Errorf("expected midW == rightW in narrow mode, got %d vs %d", l.midW, l.rightW)
	}
}

func TestComputeLayout_VeryNarrow(t *testing.T) {
	m := makeTestModel(60, 40)
	l := m.computeLayout()

	if !l.veryNarrow {
		t.Error("expected veryNarrow for 60 cols")
	}
	if l.leftW != m.Width || l.midW != m.Width || l.rightW != m.Width {
		t.Errorf("expected full-width columns in veryNarrow mode, got left=%d mid=%d right=%d",
			l.leftW, l.midW, l.rightW)
	}
	if l.showCube {
		t.Error("expected showCube=false on veryNarrow screen")
	}
}

func TestComputeLayout_Short(t *testing.T) {
	m := makeTestModel(120, 20)
	l := m.computeLayout()

	if !l.short {
		t.Error("expected short for 20 rows")
	}
	if l.showCube {
		t.Error("expected showCube=false on short screen")
	}
	if l.chatH > 1 {
		t.Errorf("expected chatH <= 1 on short screen, got %d", l.chatH)
	}
	if l.helpH > 1 {
		t.Errorf("expected helpH <= 1 on short screen, got %d", l.helpH)
	}
}

func TestComputeLayout_EmergencyTiny(t *testing.T) {
	m := makeTestModel(40, 5)
	l := m.computeLayout()

	if l.bodyH < 1 {
		t.Errorf("expected bodyH >= 1 even in tiny terminal, got %d", l.bodyH)
	}
	if l.showCube {
		t.Error("expected showCube=false in tiny terminal")
	}
}

func TestComputeLayout_ExpandedChat(t *testing.T) {
	m := makeTestModel(120, 40)
	m.Chat.Expanded = true
	l := m.computeLayout()

	if l.chatH < 4 {
		t.Errorf("expected expanded chatH >= 4, got %d", l.chatH)
	}
	if l.chatH > m.Height/3 {
		t.Errorf("expected expanded chatH <= height/3, got %d", l.chatH)
	}
}

func TestComputeLayout_VisibleHelp(t *testing.T) {
	m := makeTestModel(120, 40)
	m.Help.Visible = true
	l := m.computeLayout()

	if l.helpH < 4 {
		t.Errorf("expected visible helpH >= 4, got %d", l.helpH)
	}
}

func TestComputeLayout_RunningPipeline(t *testing.T) {
	m := makeTestModel(120, 40)
	m.Pipeline.Running = true
	m.Pipeline.StartTime = time.Now()
	l := m.computeLayout()

	// When running, pipeline should get more height than when idle
	idleM := makeTestModel(120, 40)
	idleL := idleM.computeLayout()

	if l.pipeH <= idleL.pipeH {
		t.Errorf("expected running pipeline height (%d) > idle pipeline height (%d)", l.pipeH, idleL.pipeH)
	}
}

func TestComputeLayout_BodyNonNegative(t *testing.T) {
	// Stress-test various sizes to ensure bodyH never goes negative
	for w := 10; w <= 200; w += 10 {
		for h := 1; h <= 50; h++ {
			m := makeTestModel(w, h)
			l := m.computeLayout()
			if l.bodyH < 0 {
				t.Fatalf("bodyH negative at %dx%d: got %d", w, h, l.bodyH)
			}
			if l.c4H < 0 {
				t.Fatalf("c4H negative at %dx%d: got %d", w, h, l.c4H)
			}
			if l.inputH < 0 {
				t.Fatalf("inputH negative at %dx%d: got %d", w, h, l.inputH)
			}
			if l.pipeH < 0 {
				t.Fatalf("pipeH negative at %dx%d: got %d", w, h, l.pipeH)
			}
		}
	}
}
