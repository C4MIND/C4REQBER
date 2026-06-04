package backend

import (
	"context"
	"fmt"
	"time"
)

// Bridge wraps Client calls with rate limiting + graceful degradation.
type Bridge struct {
	Client        *Client
	LLMLimiter    *RateLimiter
	SearchLimiter *RateLimiter
}

// NewBridge creates a Bridge with the given API base URL.
func NewBridge(baseURL string) *Bridge {
	return &Bridge{
		Client:        NewClient(baseURL),
		LLMLimiter:    NewRateLimiter(10, 60*time.Second),
		SearchLimiter: NewRateLimiter(5, 60*time.Second),
	}
}

// NewBridgeWithCredentials creates a Bridge with API key and dev bypass token.
func NewBridgeWithCredentials(baseURL, apiKey, devBypass string) *Bridge {
	client := NewClient(baseURL)
	client.SetCredentials(apiKey, devBypass)
	return &Bridge{
		Client:        client,
		LLMLimiter:    NewRateLimiter(10, 60*time.Second),
		SearchLimiter: NewRateLimiter(5, 60*time.Second),
	}
}

// NewBridgeWithClient creates a Bridge with an existing client and limiters.
func NewBridgeWithClient(client *Client, llm, search *RateLimiter) *Bridge {
	return &Bridge{
		Client:        client,
		LLMLimiter:    llm,
		SearchLimiter: search,
	}
}

// Health checks backend status. Returns ok and a detail message (empty on success).
func (b *Bridge) Health(ctx context.Context) (bool, string) {
	_, err := b.Client.Health(ctx)
	if err != nil {
		return false, err.Error()
	}
	return true, ""
}

// discoverCall is a generic helper for rate-limited backend calls.
func (b *Bridge) discoverCall(
	ctx context.Context,
	limiter *RateLimiter,
	call func(context.Context) error,
) error {
	if err := limiter.Acquire(); err != nil {
		return fmt.Errorf("rate limit acquire: %w", err)
	}
	defer limiter.Release(1)
	if err := call(ctx); err != nil {
		return fmt.Errorf("backend call: %w", err)
	}
	return nil
}

// Discover runs discovery with rate limiting and graceful fallback.
func (b *Bridge) Discover(ctx context.Context, problem, domain string) (*OneClickResponse, error) {
	var resp *OneClickResponse
	err := b.discoverCall(ctx, b.LLMLimiter, func(ctx context.Context) error {
		var err error
		resp, err = b.Client.OneClick(ctx, OneClickRequest{Problem: problem, Domain: domain})
		return err
	})
	return resp, err
}

// Flash runs flash discovery with rate limiting.
func (b *Bridge) Flash(ctx context.Context, problem, domain string) (*FlashResponse, error) {
	var resp *FlashResponse
	err := b.discoverCall(ctx, b.LLMLimiter, func(ctx context.Context) error {
		var err error
		resp, err = b.Client.Flash(ctx, FlashRequest{Problem: problem, Domain: domain, Level: "simple"})
		return err
	})
	return resp, err
}

// Search runs search with rate limiting.
func (b *Bridge) Search(ctx context.Context, query string) (*SearchResponse, error) {
	var resp *SearchResponse
	err := b.discoverCall(ctx, b.SearchLimiter, func(ctx context.Context) error {
		var err error
		resp, err = b.Client.Search(ctx, SearchRequest{Query: query, MaxResults: 20})
		return err
	})
	return resp, err
}

// Verify runs verification with rate limiting.
func (b *Bridge) Verify(ctx context.Context, code, method string) (*VerifyResponse, error) {
	var resp *VerifyResponse
	err := b.discoverCall(ctx, b.LLMLimiter, func(ctx context.Context) error {
		var err error
		resp, err = b.Client.Verify(ctx, VerifyRequest{Code: code, FormalMethod: method, Proof: "sorry"})
		return err
	})
	return resp, err
}

// C4Navigate runs C4 pathfinding with rate limiting.
func (b *Bridge) C4Navigate(ctx context.Context, problem string) (*C4NavigateResponse, error) {
	var resp *C4NavigateResponse
	err := b.discoverCall(ctx, b.LLMLimiter, func(ctx context.Context) error {
		var err error
		resp, err = b.Client.C4Navigate(ctx, C4NavigateRequest{Problem: problem})
		return err
	})
	return resp, err
}

// Turbo runs deep agentic discovery with extended timeout.
func (b *Bridge) Turbo(ctx context.Context, problem, domain string) (*OneClickResponse, error) {
	var resp *OneClickResponse
	err := b.discoverCall(ctx, b.LLMLimiter, func(ctx context.Context) error {
		var err error
		resp, err = b.Client.OneClick(ctx, OneClickRequest{Problem: problem, Domain: domain, Turbo: true})
		return err
	})
	return resp, err
}

// TurboFactory runs batch discovery on multiple problems.
func (b *Bridge) TurboFactory(ctx context.Context, problems []string, domain string) ([]*OneClickResponse, error) {
	if err := b.LLMLimiter.AcquireN(len(problems)); err != nil {
		return nil, fmt.Errorf("rate limit acquire batch: %w", err)
	}
	results := make([]*OneClickResponse, 0, len(problems))
	for _, problem := range problems {
		resp, err := b.Client.OneClick(ctx, OneClickRequest{Problem: problem, Domain: domain, Turbo: true})
		if err != nil {
			b.LLMLimiter.Release(len(problems) - len(results))
			return nil, fmt.Errorf("one-click turbo: %w", err)
		}
		results = append(results, resp)
	}
	return results, nil
}
