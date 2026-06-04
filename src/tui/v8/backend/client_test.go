package backend

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClient_Health(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/health" {
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	h, err := c.Health(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if h.Status != "ok" {
		t.Fatalf("expected status ok, got %s", h.Status)
	}
}

func TestClient_OneClick(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v8/discover/one-click" && r.Method == "POST" {
			var req OneClickRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				w.WriteHeader(http.StatusBadRequest)
				return
			}
			resp := OneClickResponse{JobID: "job_123", Status: "queued"}
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.OneClick(ctx, OneClickRequest{Problem: "test topic", Domain: "science"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.JobID != "job_123" {
		t.Fatalf("expected job_id job_123, got %s", resp.JobID)
	}
	if resp.Status != "queued" {
		t.Fatalf("expected status queued, got %s", resp.Status)
	}
}

func TestClient_OneClick_ServerError(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err := c.OneClick(ctx, OneClickRequest{Problem: "x", Domain: "science"})
	if err == nil {
		t.Fatal("expected error on 500")
	}
}

func TestClient_OneClick_NetworkError(t *testing.T) {
	c := NewClient("http://127.0.0.1:1")
	c.HTTP.Timeout = 100 * time.Millisecond
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err := c.OneClick(ctx, OneClickRequest{Problem: "x", Domain: "science"})
	if err == nil {
		t.Fatal("expected error on unreachable server")
	}
}

func TestClient_Flash(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v8/discover/flash" {
			resp := FlashResponse{JobID: "job_flash", Status: "queued"}
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.Flash(ctx, FlashRequest{Problem: "flash-topic", Domain: "science"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.JobID != "job_flash" {
		t.Fatalf("expected job_id job_flash, got %s", resp.JobID)
	}
}

func TestClient_Search(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v8/knowledge/search" {
			resp := SearchResponse{
				Query:       "search-topic",
				Total:       3,
				Results:     []SearchResult{{Title: "Paper 1"}},
				SourcesUsed: []string{"arxiv"},
			}
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.Search(ctx, SearchRequest{Query: "search-topic", MaxResults: 20})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Total != 3 {
		t.Fatalf("expected total 3, got %d", resp.Total)
	}
}

func TestClient_Verify(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v8/verification/verify" {
			resp := VerifyResponse{VerifyID: "v1", Verified: true, Method: "hoare"}
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.Verify(ctx, VerifyRequest{Code: "x", FormalMethod: "hoare"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !resp.Verified {
		t.Fatal("expected verified true")
	}
}

func TestClient_JobStatus(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v8/discover/status/job_123" {
			resp := JobStatusResponse{JobID: "job_123", Status: "complete", Progress: 1.0}
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.JobStatus(ctx, "job_123")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Status != "complete" {
		t.Fatalf("expected status complete, got %s", resp.Status)
	}
}

func TestClient_PostRetry_PreservesBody(t *testing.T) {
	attempts := 0
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts < 2 {
			w.WriteHeader(http.StatusServiceUnavailable)
			return
		}
		// Verify body is intact on retry
		var req OneClickRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Fatalf("decode body on attempt %d: %v", attempts, err)
		}
		if req.Problem != "test-problem" {
			t.Fatalf("expected problem 'test-problem' on attempt %d, got %s", attempts, req.Problem)
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(OneClickResponse{JobID: "job-123", Status: "queued"})
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.OneClick(ctx, OneClickRequest{Problem: "test-problem", Domain: "science"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.JobID != "job-123" {
		t.Fatalf("expected job-123, got %s", resp.JobID)
	}
	if attempts != 2 {
		t.Fatalf("expected 2 attempts, got %d", attempts)
	}
}

func TestClient_C4Navigate(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v8/discover/navigate-c4" {
			resp := C4NavigateResponse{Start: "C4State(T=0, S=0, A=0)", End: "C4State(T=2, S=2, A=2)", Steps: 6}
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer ts.Close()

	c := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := c.C4Navigate(ctx, C4NavigateRequest{Problem: "test"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Steps != 6 {
		t.Fatalf("expected steps 6, got %d", resp.Steps)
	}
}
