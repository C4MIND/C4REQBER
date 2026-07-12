package tui

import (
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

func TestApplySimCostAccumulates(t *testing.T) {
	m := NewAppFresh("http://test")
	m.simSpendThisSession = 0
	m.ApplySimCost(0.001)
	m.ApplySimCost(0.005)
	if m.simSpendThisSession != 0.006 {
		t.Errorf("expected $0.006, got %f", m.simSpendThisSession)
	}
}

func TestApplySimCostRejectsNegative(t *testing.T) {
	m := NewAppFresh("http://test")
	m.simSpendThisSession = 1.0
	m.ApplySimCost(-5.0)
	if m.simSpendThisSession != 1.0 {
		t.Errorf("negative cost should be ignored; got %f", m.simSpendThisSession)
	}
}

func TestCapsimShortSummaryWithReport(t *testing.T) {
	defer SetLang(i18n.LangEN)
	SetLang(i18n.LangEN)
	r := &capsim.Report{Engines: []capsim.Engine{
		{Status: capsim.StatusAvailable},
		{Status: capsim.StatusSlow},
		{Status: capsim.StatusUnavailable},
	}}
	if got := capsim.ShortSummary(r); got != "⏚ 2/3 engines" {
		t.Errorf("ShortSummary = %q", got)
	}
}
