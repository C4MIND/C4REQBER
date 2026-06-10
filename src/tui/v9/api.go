package tui

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"time"
)

// API client wrapping real c4reqber backend.
// Auth: JWT bearer + CSRF double-submit cookie.

type apiClient struct {
	baseURL  string
	jar      *cookiejar.Jar
	token    string
	csrf     string
	client   *http.Client
}

func newAPIClient(baseURL string) *apiClient {
	jar, _ := cookiejar.New(nil)
	return &apiClient{
		baseURL: baseURL,
		jar:     jar,
		client:  &http.Client{Timeout: 30 * time.Second},
	}
}

func (a *apiClient) ensureCSRF(ctx context.Context) error {
	req, _ := http.NewRequestWithContext(ctx, "GET", a.baseURL+"/api/v1/health", nil)
	resp, err := a.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	for _, c := range resp.Cookies() {
		if c.Name == "csrf_token" {
			a.csrf = c.Value
		}
	}
	return nil
}

func (a *apiClient) register(ctx context.Context, email, password, name string) error {
	body := fmt.Sprintf(`{"email":%q,"password":%q,"name":%q}`, email, password, name)
	req, _ := http.NewRequestWithContext(ctx, "POST", a.baseURL+"/api/v1/auth/register", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	if a.csrf != "" {
		req.Header.Set("X-CSRF-Token", a.csrf)
	}
	resp, err := a.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("register status %d", resp.StatusCode)
	}
	return nil
}

func (a *apiClient) login(ctx context.Context, email, password string) error {
	body := fmt.Sprintf(`{"email":%q,"password":%q,"name":""}`, email, password)
	req, _ := http.NewRequestWithContext(ctx, "POST", a.baseURL+"/api/v1/auth/login", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	if a.csrf != "" {
		req.Header.Set("X-CSRF-Token", a.csrf)
	}
	resp, err := a.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("login status %d", resp.StatusCode)
	}
	var out struct {
		AccessToken string `json:"access_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return err
	}
	a.token = out.AccessToken
	return nil
}

func (a *apiClient) submit(ctx context.Context, problem, domain string) (string, error) {
	if domain == "" {
		domain = "science"
	}
	body := fmt.Sprintf(`{"problem":%q,"domain":%q}`, problem, domain)
	req, _ := http.NewRequestWithContext(ctx, "POST", a.baseURL+"/v8/discover/one-click", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	if a.token != "" {
		req.Header.Set("Authorization", "Bearer "+a.token)
	}
	if a.csrf != "" {
		req.Header.Set("X-CSRF-Token", a.csrf)
	}
	resp, err := a.client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("submit status %d", resp.StatusCode)
	}
	var out struct {
		JobID string `json:"job_id"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", err
	}
	return out.JobID, nil
}

func (a *apiClient) poll(ctx context.Context, jobID string) (apiPollMsg, error) {
	u := a.baseURL + "/v8/discover/status/" + url.PathEscape(jobID)
	req, _ := http.NewRequestWithContext(ctx, "GET", u, nil)
	if a.token != "" {
		req.Header.Set("Authorization", "Bearer "+a.token)
	}
	if a.csrf != "" {
		req.Header.Set("X-CSRF-Token", a.csrf)
	}
	resp, err := a.client.Do(req)
	if err != nil {
		return apiPollMsg{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return apiPollMsg{}, fmt.Errorf("poll status %d", resp.StatusCode)
	}
	var raw map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return apiPollMsg{}, err
	}
	msg := apiPollMsg{
		status:   stringField(raw, "status"),
		phase:    stringField(raw, "phase"),
		progress: 0,
	}
	if p, ok := raw["progress"].(float64); ok {
		msg.progress = p
	}
	if res, ok := raw["result"].(map[string]any); ok {
		msg.result = res
	}
	msg.completed = msg.status == "complete" || msg.status == "failed" || msg.status == "partial"
	return msg, nil
}

func (a *apiClient) papers(ctx context.Context, query string, maxResults int) ([]map[string]any, error) {
	if maxResults <= 0 {
		maxResults = 3
	}
	body := fmt.Sprintf(`{"query":%q,"max_results":%d}`, query, maxResults)
	req, _ := http.NewRequestWithContext(ctx, "POST", a.baseURL+"/v8/knowledge/search", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	if a.token != "" {
		req.Header.Set("Authorization", "Bearer "+a.token)
	}
	if a.csrf != "" {
		req.Header.Set("X-CSRF-Token", a.csrf)
	}
	resp, err := a.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("papers status %d", resp.StatusCode)
	}
	var raw struct {
		Results []map[string]any `json:"results"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, err
	}
	return raw.Results, nil
}
