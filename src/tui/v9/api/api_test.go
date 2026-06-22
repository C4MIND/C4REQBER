// Package api_test: integration tests using httptest server.
// These run WITHOUT a real c4reqber backend — perfect for CI.
package api

import (
	"context"
	"encoding/json"
	"math"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func mockServer(t *testing.T, routes map[string]http.HandlerFunc) *httptest.Server {
	t.Helper()
	mux := http.NewServeMux()
	for path, h := range routes {
		mux.HandleFunc(path, h)
	}
	srv := httptest.NewServer(mux)
	t.Cleanup(srv.Close)
	return srv
}

func writeJSON(w http.ResponseWriter, status int, body string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write([]byte(body))
}

func TestMock_RegisterLoginSubmit(t *testing.T) {
	srv := mockServer(t, map[string]http.HandlerFunc{
		"/api/v1/health": func(w http.ResponseWriter, r *http.Request) {
			http.SetCookie(w, &http.Cookie{Name: "csrf_token", Value: "test-csrf-token-1234567890abcdef", MaxAge: 3600, Path: "/", SameSite: http.SameSiteStrictMode})
			writeJSON(w, 200, `{"status":"healthy"}`)
		},
		"/api/v1/auth/register": func(w http.ResponseWriter, r *http.Request) {
			var body map[string]any
			json.NewDecoder(r.Body).Decode(&body)
			if body["email"] == "" {
				http.Error(w, "missing email", 400)
				return
			}
			writeJSON(w, 200, `{"id":"u-1","email":"kilo@test.com","name":"Kilo"}`)
		},
		"/api/v1/auth/login": func(w http.ResponseWriter, r *http.Request) {
			var body map[string]any
			json.NewDecoder(r.Body).Decode(&body)
			if body["email"] != "kilo@test.com" {
				http.Error(w, "invalid creds", http.StatusUnauthorized)
				return
			}
			writeJSON(w, 200, `{"access_token":"jwt-test-token","token_type":"bearer"}`)
		},
		"/v8/discover/one-click": func(w http.ResponseWriter, r *http.Request) {
			writeJSON(w, 200, `{"job_id":"job_test_1","status":"queued"}`)
		},
	})

	c := New(srv.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := c.Health(ctx); err != nil {
		t.Fatal(err)
	}
	if c.CSRF() == "" {
		t.Error("CSRF token not harvested")
	}
	if err := c.Register(ctx, "kilo@test.com", "test12345", "Kilo"); err != nil {
		t.Fatal(err)
	}
	if err := c.Login(ctx, "kilo@test.com", "test12345"); err != nil {
		t.Fatal(err)
	}
	if c.Token() != "jwt-test-token" {
		t.Error("JWT token not stored")
	}
	id, err := c.OneClick(ctx, "test discovery", "science")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(id, "job_") {
		t.Errorf("job_id %q missing 'job_' prefix", id)
	}
}

func TestMock_FlashReturnsInline(t *testing.T) {
	srv := mockServer(t, map[string]http.HandlerFunc{
		"/v8/discover/flash": func(w http.ResponseWriter, r *http.Request) {
			writeJSON(w, 200, `{
				"hypothesis": {"source": "LLMProvider/v8", "text": "Use truncated 17-nt guides"},
				"papers": [{"title": "Optimized sgRNA", "venue": "Nature", "year": 2016, "doi": "10.1038/..."}]
			}`)
		},
	})
	c := New(srv.URL)
	ctx := context.Background()
	res, err := c.Flash(ctx, "test", "science")
	if err != nil {
		t.Fatal(err)
	}
	hyp, _ := res["hypothesis"].(map[string]any)
	if hyp["text"] != "Use truncated 17-nt guides" {
		t.Errorf("hypothesis text wrong: %v", hyp)
	}
}

func TestMock_KnowledgeSearch(t *testing.T) {
	srv := mockServer(t, map[string]http.HandlerFunc{
		"/v8/knowledge/search": func(w http.ResponseWriter, r *http.Request) {
			writeJSON(w, 200, `{
				"results": [
					{"title": "Memory function of sleep", "authors": ["Diekelmann"], "year": 2010, "venue": "Nature", "doi": "10.1038/nrn2762", "citation_count": 3728, "source": "openalex"},
					{"title": "Sleep and synaptic homeostasis", "authors": ["Tononi"], "year": 2014, "venue": "Neuron", "doi": "10.1016/...", "citation_count": 2380, "source": "openalex"}
				],
				"total": 28,
				"query": "sleep memory"
			}`)
		},
	})
	c := New(srv.URL)
	ctx := context.Background()
	papers, err := c.KnowledgeSearch(ctx, "sleep memory", 5)
	if err != nil {
		t.Fatal(err)
	}
	if len(papers) != 2 {
		t.Errorf("got %d papers, want 2", len(papers))
	}
	if papers[0]["title"] != "Memory function of sleep" {
		t.Errorf("first paper title wrong: %v", papers[0])
	}
}

func TestMock_JobStatusParsing(t *testing.T) {
	srv := mockServer(t, map[string]http.HandlerFunc{
		"/v8/discover/status/job_test_1": func(w http.ResponseWriter, r *http.Request) {
			writeJSON(w, 200, `{
				"job_id": "job_test_1",
				"status": "phase_e",
				"phase": "E: Sim",
				"progress": 0.6,
				"result": null,
				"errors": []
			}`)
		},
	})
	c := New(srv.URL)
	ctx := context.Background()
	js, err := c.JobStatus(ctx, "job_test_1")
	if err != nil {
		t.Fatal(err)
	}
	if js.Status != "phase_e" {
		t.Errorf("status wrong: %s", js.Status)
	}
	if js.Phase != "E: Sim" {
		t.Errorf("phase wrong: %s", js.Phase)
	}
	if math.Abs(js.Progress-0.6) > 0.001 {
		t.Errorf("progress wrong: %v", js.Progress)
	}
	if js.Completed {
		t.Error("should not be completed")
	}
}

func TestMock_JobStatusCompleted(t *testing.T) {
	srv := mockServer(t, map[string]http.HandlerFunc{
		"/v8/discover/status/job_done": func(w http.ResponseWriter, r *http.Request) {
			writeJSON(w, 200, `{
				"job_id": "job_done",
				"status": "complete",
				"phase": "G: Quality",
				"progress": 1.0,
				"completed_at": 1234567890.5,
				"result": {
					"hypothesis": {"text": "done hypothesis", "source": "LLMProvider/v8"},
					"papers": [
						{"title": "Paper 1", "year": 2020, "venue": "Nature", "doi": "10.1/x", "citation_count": 100, "source": "openalex"},
						{"title": "Paper 2", "year": 2021, "venue": "Science", "doi": "10.2/y", "citation_count": 200, "source": "arxiv"}
					],
					"total_time_seconds": 47.2
				}
			}`)
		},
	})
	c := New(srv.URL)
	ctx := context.Background()
	js, err := c.JobStatus(ctx, "job_done")
	if err != nil {
		t.Fatal(err)
	}
	if !js.Completed {
		t.Error("should be completed")
	}
	if js.Result == nil {
		t.Fatal("result should not be nil")
	}
	hyp, _ := js.Result["hypothesis"].(map[string]any)
	if hyp["text"] != "done hypothesis" {
		t.Errorf("hypothesis text wrong: %v", hyp["text"])
	}
}

func TestMock_SSEParseEvent(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  SSEEvent
	}{
		{"empty", "", SSEEvent{}},
		{"event-only", "event: phase\n\n", SSEEvent{Event: "phase"}},
		{"data-only", "data: {\"status\":\"phase_b\"}\n\n", SSEEvent{Data: "{\"status\":\"phase_b\"}"}},
		{"full", "event: phase\ndata: {\"status\":\"phase_b\"}\n\n", SSEEvent{Event: "phase", Data: "{\"status\":\"phase_b\"}"}},
		{"multiline-data", "data: line1\ndata: line2\n\n", SSEEvent{Data: "line1\nline2"}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parseSSEEvent(tt.input)
			if got != tt.want {
				t.Errorf("got %+v, want %+v", got, tt.want)
			}
		})
	}
}

func TestMock_SSEBoundaryIndex(t *testing.T) {
	tests := []struct {
		input string
		want  int
	}{
		{"", -1},
		{"a", -1},
		{"a\nb", -1},
		{"a\n\n", 1},
		{"a\n\nb", 1},
		{"a\n\n\nb", 1}, // returns first occurrence
	}
	for _, tt := range tests {
		got := indexOfSSEBoundary(tt.input)
		if got != tt.want {
			t.Errorf("indexOfSSEBoundary(%q) = %d, want %d", tt.input, got, tt.want)
		}
	}
}
