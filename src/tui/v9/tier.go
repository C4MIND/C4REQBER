package tui

import (
	"fmt"
	"strings"
)

// LLMTier represents the depth/cost tier of the LLM pipeline.
// C1 = cheap (qwen-2.5-7b, deepseek-chat) — brainstorming, fast
// C2 = balanced (qwen-2.5-72b, claude-haiku) — quality
// C3 = premium (claude-sonnet, gpt-4) — final validation
type LLMTier int

const (
	TierC1 LLMTier = 1
	TierC2 LLMTier = 2
	TierC3 LLMTier = 3
)

// String returns the canonical tier name.
func (t LLMTier) String() string {
	switch t {
	case TierC1:
		return "C1"
	case TierC2:
		return "C2"
	case TierC3:
		return "C3"
	default:
		return "?"
	}
}

// ModelFor returns the recommended model name for this tier.
func (t LLMTier) ModelFor() string {
	switch t {
	case TierC1:
		return "deepseek-chat-v3.1"
	case TierC2:
		return "qwen-2.5-72b-instruct"
	case TierC3:
		return "claude-sonnet-4.6"
	}
	return "unknown"
}

// EstimatedCost returns the rough cost in USD per run.
func (t LLMTier) EstimatedCost() float64 {
	switch t {
	case TierC1:
		return 0.001
	case TierC2:
		return 0.012
	case TierC3:
		return 0.045
	}
	return 0
}

// CycleLLMTier returns the next tier in C1→C2→C3→C1 cycle.
func CycleLLMTier(t LLMTier) LLMTier {
	switch t {
	case TierC1:
		return TierC2
	case TierC2:
		return TierC3
	default:
		return TierC1
	}
}

// TierFromString parses "C1"/"C2"/"C3" (case-insensitive) into a tier.
func TierFromString(s string) (LLMTier, bool) {
	switch strings.ToUpper(strings.TrimSpace(s)) {
	case "C1":
		return TierC1, true
	case "C2":
		return TierC2, true
	case "C3":
		return TierC3, true
	}
	return 0, false
}

// FormatTierBadge returns a styled label like "C1 · deepseek-chat · ~$0.001".
func (t LLMTier) FormatTierBadge() string {
	return fmt.Sprintf("%s · %s · ~$%.3f", t, t.ModelFor(), t.EstimatedCost())
}
