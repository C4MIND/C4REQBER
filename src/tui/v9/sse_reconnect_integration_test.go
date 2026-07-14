package tui

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

func TestSSEReconnectOpensNewHTTPStream(t *testing.T) {
	var streamCalls atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v8/discover/stream/job-1" {
			http.NotFound(w, r)
			return
		}
		streamCalls.Add(1)
		w.Header().Set("Content-Type", "text/event-stream")
		_, _ = fmt.Fprint(w, "event: phase_progress\n")
		_, _ = fmt.Fprint(w, "data: {\"type\":\"phase_progress\",\"phase\":\"B\"}\n\n")
	}))
	defer server.Close()

	m := NewAppFresh(server.URL)
	m.api = api.New(server.URL)
	m.running = true
	m.jobID = "job-1"
	m.sseRetryCount = 1
	m.sseEvents = nil
	m.sseCancel = nil

	_, command := m.Update(sseReconnectMsg{})
	if command == nil {
		t.Fatal("reconnect did not return an SSE command")
	}

	done := make(chan any, 1)
	go func() { done <- command() }()
	select {
	case message := <-done:
		if _, ok := message.(sseEventMsg); !ok {
			t.Fatalf("reconnect command returned %T, want sseEventMsg", message)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("reconnect command did not open a new stream")
	}
	if calls := streamCalls.Load(); calls != 1 {
		t.Fatalf("stream endpoint called %d times, want 1", calls)
	}
}
