package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// AgendaQuestion is one scored research question from /v8/agenda/generate.
type AgendaQuestion struct {
	Text           string                 `json:"text"`
	Strategy       string                 `json:"strategy"`
	PriorityScore  float64                `json:"priority_score"`
	NoveltyScore   float64                `json:"novelty_score"`
	ImpactPotential float64               `json:"impact_potential"`
	Feasibility    map[string]interface{} `json:"feasibility"`
}

// AgendaGenerateResponse is the payload from POST /v8/agenda/generate.
type AgendaGenerateResponse struct {
	Questions []AgendaQuestion `json:"questions"`
	Count     int              `json:"count"`
}

// AgendaGenerateRequest seeds agenda generation from feed context.
type AgendaGenerateRequest struct {
	KnowledgeGraph map[string]interface{} `json:"knowledge_graph"`
	RecentResults  []map[string]interface{} `json:"recent_results"`
	NQuestions     int                    `json:"n_questions"`
}

// AgendaProgress is GET /v8/agenda/progress.
type AgendaProgress struct {
	ResultsCount   int      `json:"results_count"`
	CoveredTopics  []string `json:"covered_topics"`
	OpenGaps       []string `json:"open_gaps"`
	ApprovedCount  int      `json:"approved_count"`
	RejectedCount  int      `json:"rejected_count"`
	LatestApproved []string `json:"latest_approved"`
}

func (c *Client) agendaPOST(ctx context.Context, path string, body any) ([]byte, error) {
	payload, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.BaseURL+path, bytes.NewReader(payload))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	if c.csrf != "" {
		req.Header.Set("X-CSRF-Token", c.csrf)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("agenda %s status %d: %s", path, resp.StatusCode, string(data))
	}
	return data, nil
}

func (c *Client) agendaGET(ctx context.Context, path string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.BaseURL+path, nil)
	if err != nil {
		return nil, err
	}
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	if c.csrf != "" {
		req.Header.Set("X-CSRF-Token", c.csrf)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("agenda %s status %d: %s", path, resp.StatusCode, string(data))
	}
	return data, nil
}

// AgendaGenerate calls POST /v8/agenda/generate.
func (c *Client) AgendaGenerate(ctx context.Context, req AgendaGenerateRequest) (*AgendaGenerateResponse, error) {
	if req.NQuestions <= 0 {
		req.NQuestions = 5
	}
	data, err := c.agendaPOST(ctx, "/v8/agenda/generate", req)
	if err != nil {
		return nil, err
	}
	var out AgendaGenerateResponse
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// AgendaApprove calls POST /v8/agenda/approve.
func (c *Client) AgendaApprove(ctx context.Context, questionText, action, modifiedText string) (map[string]interface{}, error) {
	body := map[string]string{
		"question_text": questionText,
		"action":        action,
	}
	if modifiedText != "" {
		body["modified_text"] = modifiedText
	}
	data, err := c.agendaPOST(ctx, "/v8/agenda/approve", body)
	if err != nil {
		return nil, err
	}
	var out map[string]interface{}
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// AgendaProgress calls GET /v8/agenda/progress.
func (c *Client) AgendaProgress(ctx context.Context) (*AgendaProgress, error) {
	data, err := c.agendaGET(ctx, "/v8/agenda/progress")
	if err != nil {
		return nil, err
	}
	var out AgendaProgress
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}
	return &out, nil
}
