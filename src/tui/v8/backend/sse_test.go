package backend

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestSSE_Subscribe(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v8/discover/stream/job_1" {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "event: phase\ndata: {\"phase\":\"A: Framing\",\"status\":\"working\",\"progress\":0.5}\n\n")
		fmt.Fprint(w, "event: complete\ndata: {\"phase\":\"G: Quality\",\"status\":\"complete\",\"progress\":1.0}\n\n")
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	events, errCh, err := c.SubscribeSSE(ctx, "job_1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var gotEvents int
	for e := range events {
		gotEvents++
		if e.Event == "phase" {
			p, err := ParsePhaseEvent(e.Data)
			if err != nil {
				t.Fatalf("parse phase: %v", err)
			}
			if p.Phase != "A: Framing" {
				t.Fatalf("expected phase A: Framing, got %s", p.Phase)
			}
		}
		if e.Event == "complete" {
			r, err := ParseResultEvent(e.Data)
			if err != nil {
				t.Fatalf("parse result: %v", err)
			}
			if r.Status != "complete" {
				t.Fatalf("expected status complete, got %s", r.Status)
			}
		}
	}

	if gotEvents != 2 {
		t.Fatalf("expected 2 events, got %d", gotEvents)
	}

	select {
	case err := <-errCh:
		if err != nil {
			t.Fatalf("unexpected error from errCh: %v", err)
		}
	case <-time.After(time.Second):
	}
}

func TestSSE_ParsePhaseEvent(t *testing.T) {
	data := `{"phase":"B: Search","status":"working","progress":0.75,"detail":"fetching"}`
	p, err := ParsePhaseEvent(data)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.Phase != "B: Search" {
		t.Fatalf("expected phase B: Search, got %s", p.Phase)
	}
	if p.Progress != 0.75 {
		t.Fatalf("expected progress 0.75, got %f", p.Progress)
	}
}

func TestSSE_ParseResultEvent(t *testing.T) {
	data := `{"phase":"G: Quality","status":"complete","progress":1.0,"result":{"x":1},"errors":[]}`
	r, err := ParseResultEvent(data)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if r.Status != "complete" {
		t.Fatalf("expected status complete, got %s", r.Status)
	}
}

func TestSSE_Subscribe_NotFound(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, _, err := c.SubscribeSSE(ctx, "missing")
	if err == nil {
		t.Fatal("expected error on 404")
	}
}
