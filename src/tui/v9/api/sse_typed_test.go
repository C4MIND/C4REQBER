package api

import (
	"testing"
)

func TestDecodeTypedEventSimFinished(t *testing.T) {
	data := `{"type":"sim_finished","engine":"openmm","pattern":"protein_folding","engine_status":"success","verdict":"supports_hypothesis","elapsed_ms":12450,"cost_usd":0.012,"hypothesis_id":"42"}`
	e, err := DecodeTypedEvent(data)
	if err != nil {
		t.Fatal(err)
	}
	if e.Type != EventSimFinished {
		t.Errorf("type = %s, want sim_finished", e.Type)
	}
	if e.Engine != "openmm" {
		t.Errorf("engine = %s", e.Engine)
	}
	if e.Verdict != "supports_hypothesis" {
		t.Errorf("verdict = %s", e.Verdict)
	}
	if e.CostUSD != 0.012 {
		t.Errorf("cost = %f", e.CostUSD)
	}
}

func TestDecodeTypedEventLegacyPhase(t *testing.T) {
	data := `{"status":"running","phase":"D","progress":0.62}`
	e, err := DecodeTypedEvent(data)
	if err != nil {
		t.Fatal(err)
	}
	if e.Type != EventPhaseProgress {
		t.Errorf("legacy should infer phase_progress, got %s", e.Type)
	}
	if e.Phase != "D" {
		t.Errorf("phase = %s", e.Phase)
	}
	if e.Progress != 0.62 {
		t.Errorf("progress = %f", e.Progress)
	}
}

func TestDecodeTypedEventSimSkipped(t *testing.T) {
	data := `{"type":"sim_skipped","engine":"fenicsx","pattern":"elasticity_3d","reason":"no_arm64_wheel","install_hint":"conda install -c conda-forge fenics-dolfinx","fallback_used":"jaxsim"}`
	e, _ := DecodeTypedEvent(data)
	if e.Type != EventSimSkipped {
		t.Errorf("type = %s", e.Type)
	}
	if e.InstallHint == "" {
		t.Error("install hint should be present")
	}
	if e.FallbackUsed != "jaxsim" {
		t.Errorf("fallback = %s", e.FallbackUsed)
	}
}

func TestDecodeTypedEventEmptyData(t *testing.T) {
	_, err := DecodeTypedEvent("")
	if err == nil {
		t.Error("expected error on empty data")
	}
}

func TestLegacyExtractComplete(t *testing.T) {
	data := `{"status":"complete","phase":"G","progress":1.0,"result":{"hypothesis":{"text":"foo"}}}`
	status, phase, prog, result, completed := LegacyExtract(data)
	if !completed {
		t.Error("expected completed=true")
	}
	if status != "complete" {
		t.Errorf("status = %s", status)
	}
	if phase != "G" {
		t.Errorf("phase = %s", phase)
	}
	if prog != 1.0 {
		t.Errorf("progress = %f", prog)
	}
	if result == nil || result["hypothesis"] == nil {
		t.Error("result should contain hypothesis")
	}
}
