package telemetry

import (
	"sync"
	"testing"
	"time"
)

func TestTelemetryBasics(t *testing.T) {
	tel := New()
	tel.IncTick()
	tel.IncTick()
	tel.IncTick()
	tel.IncDiscovery()
	tel.IncMode("DISCOVER")
	tel.IncMode("FLASH")
	tel.IncMode("DISCOVER")
	tel.IncLang("EN")
	tel.IncLang("RU")
	tel.AddCost(0.01)
	tel.AddCost(0.005)
	got := tel.Get()
	if got.TotalTicks != 3 {
		t.Errorf("TotalTicks = %d, want 3", got.TotalTicks)
	}
	if got.Discoveries != 1 {
		t.Errorf("Discoveries = %d, want 1", got.Discoveries)
	}
	if got.ModeUseCount["DISCOVER"] != 2 {
		t.Errorf("DISCOVER = %d, want 2", got.ModeUseCount["DISCOVER"])
	}
	if got.ModeUseCount["FLASH"] != 1 {
		t.Errorf("FLASH = %d, want 1", got.ModeUseCount["FLASH"])
	}
	if got.LangUseCount["EN"] != 1 {
		t.Errorf("EN = %d", got.LangUseCount["EN"])
	}
	cost := got.TotalCost
	if cost < 0.0149 || cost > 0.0151 {
		t.Errorf("TotalCost = %f, want ~0.015", cost)
	}
}

func TestTelemetryDiscoveryResult(t *testing.T) {
	tel := New()
	tel.IncDiscoveryResult(true, 30.0)
	tel.IncDiscoveryResult(false, 10.0)
	tel.IncDiscoveryResult(true, 20.0)
	got := tel.Get()
	if got.Discoveries != 3 {
		t.Errorf("Discoveries = %d, want 3", got.Discoveries)
	}
	if got.DiscoveriesOK != 2 {
		t.Errorf("DiscoveriesOK = %d, want 2", got.DiscoveriesOK)
	}
	if got.DiscoveriesFail != 1 {
		t.Errorf("DiscoveriesFail = %d, want 1", got.DiscoveriesFail)
	}
	if got.TotalLatencySec != 60.0 {
		t.Errorf("TotalLatencySec = %f, want 60", got.TotalLatencySec)
	}
	if got.LongestRunSec != 30.0 {
		t.Errorf("LongestRunSec = %f, want 30", got.LongestRunSec)
	}
}

func TestTelemetryAPICounters(t *testing.T) {
	tel := New()
	tel.IncAPICall()
	tel.IncAPICall()
	tel.IncAPICall()
	tel.IncAPIError()
	got := tel.Get()
	if got.TotalAPICalls != 3 {
		t.Errorf("TotalAPICalls = %d", got.TotalAPICalls)
	}
	if got.APIErrors != 1 {
		t.Errorf("APIErrors = %d", got.APIErrors)
	}
}

func TestTelemetryConcurrentSafe(t *testing.T) {
	tel := New()
	done := make(chan bool, 4)
	for i := 0; i < 4; i++ {
		go func(n int) {
			for j := 0; j < 100; j++ {
				tel.IncTick()
				tel.IncDiscoveryResult(true, 0.001)
				tel.IncMode("DISCOVER")
			}
			done <- true
		}(i)
	}
	for i := 0; i < 4; i++ {
		<-done
	}
	got := tel.Get()
	if got.TotalTicks != 400 {
		t.Errorf("TotalTicks = %d, want 400", got.TotalTicks)
	}
	if got.DiscoveriesOK != 400 {
		t.Errorf("DiscoveriesOK = %d, want 400", got.DiscoveriesOK)
	}
	if got.ModeUseCount["DISCOVER"] != 400 {
		t.Errorf("DISCOVER = %d, want 400", got.ModeUseCount["DISCOVER"])
	}
}

func TestTelemetrySessionStart(t *testing.T) {
	tel := New()
	got := tel.Get()
	if time.Since(got.SessionStart) > 5*time.Second {
		t.Errorf("SessionStart should be ~now, got %s ago", time.Since(got.SessionStart))
	}
}

func TestTelemetryAbort(t *testing.T) {
	tel := New()
	tel.IncDiscovery()
	tel.IncAbort()
	tel.IncAbort()
	got := tel.Get()
	if got.Discoveries != 1 {
		t.Errorf("Discoveries = %d, want 1", got.Discoveries)
	}
	if got.DiscoveriesAbort != 2 {
		t.Errorf("DiscoveriesAbort = %d, want 2", got.DiscoveriesAbort)
	}
}

func TestTelemetryModeCountCopy(t *testing.T) {
	tel := New()
	tel.IncMode("DISCOVER")
	got1 := tel.Get()
	got1.ModeUseCount["FLASH"] = 99 // mutate the copy
	got2 := tel.Get()                  // should be unchanged
	if got2.ModeUseCount["FLASH"] != 0 {
		t.Errorf("internal state leaked: FLASH = %d", got2.ModeUseCount["FLASH"])
	}
}

// _ is required to import sync in this file
var _ = sync.Mutex{}
