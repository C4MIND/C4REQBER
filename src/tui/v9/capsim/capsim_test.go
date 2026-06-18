package capsim

import "testing"

func TestFallbackIsValid(t *testing.T) {
	r := Fallback()
	if r == nil {
		t.Fatal("Fallback returned nil")
	}
	if len(r.Engines) != 0 || len(r.Verifiers) != 0 {
		t.Errorf("Fallback should have empty engines/verifiers, got %d/%d", len(r.Engines), len(r.Verifiers))
	}
}

func TestGroupByDomainStableOrder(t *testing.T) {
	r := &Report{
		Engines: []Engine{
			{ID: "openmm", Domain: DomainBiology},
			{ID: "newton", Domain: DomainPhysics},
			{ID: "cobra", Domain: DomainBiology},
		},
	}
	groups := r.GroupByDomain()
	if len(groups) != 2 {
		t.Fatalf("expected 2 domain groups, got %d", len(groups))
	}
	// Physics must come before Biology (stable order)
	if groups[0].Domain != DomainPhysics {
		t.Errorf("first group should be physics, got %s", groups[0].Domain)
	}
	if groups[1].Domain != DomainBiology {
		t.Errorf("second group should be biology, got %s", groups[1].Domain)
	}
}

func TestByID(t *testing.T) {
	r := &Report{Engines: []Engine{{ID: "openmm"}, {ID: "fenicsx"}}}
	if r.ByID("openmm") == nil {
		t.Error("expected to find openmm")
	}
	if r.ByID("nope") != nil {
		t.Error("expected nil for unknown engine")
	}
}

func TestFilterAvailable(t *testing.T) {
	r := &Report{
		Engines: []Engine{
			{ID: "a", Status: StatusAvailable},
			{ID: "b", Status: StatusSlow},
			{ID: "c", Status: StatusUnavailable},
			{ID: "d", Status: StatusBudget},
		},
	}
	avail := r.FilterAvailable()
	if len(avail) != 2 {
		t.Fatalf("expected 2 available, got %d", len(avail))
	}
}
