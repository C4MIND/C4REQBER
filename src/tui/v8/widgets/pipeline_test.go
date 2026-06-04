package widgets

import (
	"testing"

	"c4tui/config"
)

func TestNewPipeline(t *testing.T) {
	cfg := config.Default()
	p := NewPipeline(cfg)
	if len(p.Bars) != 7 {
		t.Errorf("expected 7 progress bars, got %d", len(p.Bars))
	}
	if len(p.Statuses) != 7 {
		t.Errorf("expected 7 statuses, got %d", len(p.Statuses))
	}
}

func TestPipeline_StartAndStop(t *testing.T) {
	cfg := config.Default()
	p := NewPipeline(cfg)
	p.Start()
	if !p.Running {
		t.Error("expected Running=true after Start")
	}
	p.Stop()
	if p.Running {
		t.Error("expected Running=false after Stop")
	}
}

func TestPipeline_SetPhaseName(t *testing.T) {
	cfg := config.Default()
	p := NewPipeline(cfg)
	p.Start()
	p.SetPhaseName("A: Framing", "working", 0.5)
	if p.Statuses[0] != "●" {
		t.Errorf("expected status '●' for working phase, got %q", p.Statuses[0])
	}
	if p.Progress[0] != 0.5 {
		t.Errorf("expected progress 0.5, got %f", p.Progress[0])
	}
}

func TestPipeline_View_Idle(t *testing.T) {
	cfg := config.Default()
	p := NewPipeline(cfg)
	v := p.View(80)
	if v == "" {
		t.Error("idle pipeline should render non-empty string")
	}
}

func TestPipeline_View_Running(t *testing.T) {
	cfg := config.Default()
	p := NewPipeline(cfg)
	p.Start()
	p.SetPhaseName("A: Framing", "working", 0.5)
	v := p.View(80)
	if v == "" {
		t.Error("running pipeline should render non-empty string")
	}
}

func TestPhaseIndex(t *testing.T) {
	if PhaseIndex("A: Framing") != 0 {
		t.Error("expected Framing = 0")
	}
	if PhaseIndex("G: Quality") != 6 {
		t.Error("expected Quality = 6")
	}
	if PhaseIndex("unknown") != -1 {
		t.Error("expected unknown = -1")
	}
}
