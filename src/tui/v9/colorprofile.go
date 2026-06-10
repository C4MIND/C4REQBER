package tui

import (
	"image/color"

	"charm.land/lipgloss/v2"
)

// ColorProfile adjusts color mapping for accessibility.
type ColorProfile int

const (
	ProfileDefault ColorProfile = iota
	ProfileHighContrast
	ProfileProtanopia    // red-blind
	ProfileDeuteranopia  // green-blind
	ProfileTritanopia    // blue-blind
	ProfileMonochrome    // no color
)

// String returns the profile name.
func (p ColorProfile) String() string {
	switch p {
	case ProfileHighContrast:
		return "high-contrast"
	case ProfileProtanopia:
		return "protanopia"
	case ProfileDeuteranopia:
		return "deuteranopia"
	case ProfileTritanopia:
		return "tritanopia"
	case ProfileMonochrome:
		return "monochrome"
	default:
		return "default"
	}
}

// color maps semantic color names to lipgloss color strings per profile.
// Keys are semantic ("primary", "success", "warn", "error", "muted", "accent", "highlight").
type colorMap map[string]color.Color

func baseColors() colorMap {
	return colorMap{
		"primary":   lipgloss.Color("3"),
		"success":   lipgloss.Color("2"),
		"warn":      lipgloss.Color("3"),
		"error":     lipgloss.Color("1"),
		"muted":     lipgloss.Color("8"),
		"accent":    lipgloss.Color("5"),
		"highlight": lipgloss.Color("6"),
		"info":      lipgloss.Color("4"),
	}
}

func highContrastColors() colorMap {
	return colorMap{
		"primary":   lipgloss.Color("11"), // bright yellow
		"success":   lipgloss.Color("10"), // bright green
		"warn":      lipgloss.Color("11"),
		"error":     lipgloss.Color("9"),  // bright red
		"muted":     lipgloss.Color("15"), // bright white
		"accent":    lipgloss.Color("13"), // bright magenta
		"highlight": lipgloss.Color("14"), // bright cyan
		"info":      lipgloss.Color("12"), // bright blue
	}
}

func protanopiaColors() colorMap {
	// Red-blind: avoid pure red, use orange/yellow for warnings
	return colorMap{
		"primary":   lipgloss.Color("3"),
		"success":   lipgloss.Color("6"),  // cyan instead of green
		"warn":      lipgloss.Color("11"), // bright yellow
		"error":     lipgloss.Color("5"),  // magenta instead of red
		"muted":     lipgloss.Color("8"),
		"accent":    lipgloss.Color("5"),
		"highlight": lipgloss.Color("6"),
		"info":      lipgloss.Color("4"),
	}
}

func deuteranopiaColors() colorMap {
	// Green-blind: same as protanopia for most cases
	return protanopiaColors()
}

func tritanopiaColors() colorMap {
	// Blue-blind: avoid pure blue, use cyan/teal
	return colorMap{
		"primary":   lipgloss.Color("3"),
		"success":   lipgloss.Color("2"),
		"warn":      lipgloss.Color("3"),
		"error":     lipgloss.Color("1"),
		"muted":     lipgloss.Color("8"),
		"accent":    lipgloss.Color("5"),
		"highlight": lipgloss.Color("7"),  // white instead of cyan
		"info":      lipgloss.Color("6"),  // cyan instead of blue
	}
}

func monochromeColors() colorMap {
	// No color at all — just grayscale
	return colorMap{
		"primary":   lipgloss.Color("7"),  // white
		"success":   lipgloss.Color("15"), // bright white
		"warn":      lipgloss.Color("7"),
		"error":     lipgloss.Color("8"),  // gray
		"muted":     lipgloss.Color("8"),
		"accent":    lipgloss.Color("7"),
		"highlight": lipgloss.Color("15"),
		"info":      lipgloss.Color("7"),
	}
}

// ColorsFor returns the color map for the given profile.
func ColorsFor(p ColorProfile) colorMap {
	switch p {
	case ProfileHighContrast:
		return highContrastColors()
	case ProfileProtanopia:
		return protanopiaColors()
	case ProfileDeuteranopia:
		return deuteranopiaColors()
	case ProfileTritanopia:
		return tritanopiaColors()
	case ProfileMonochrome:
		return monochromeColors()
	default:
		return baseColors()
	}
}

// ProfileFromString parses "high-contrast", "protanopia", etc.
func ProfileFromString(s string) (ColorProfile, bool) {
	switch s {
	case "", "default":
		return ProfileDefault, true
	case "high-contrast", "hc":
		return ProfileHighContrast, true
	case "protanopia", "prot":
		return ProfileProtanopia, true
	case "deuteranopia", "deut":
		return ProfileDeuteranopia, true
	case "tritanopia", "trit":
		return ProfileTritanopia, true
	case "monochrome", "mono", "no-color":
		return ProfileMonochrome, true
	}
	return 0, false
}

// ProfileFromEnv reads C4_COLOR_PROFILE env var.
func ProfileFromEnv() ColorProfile {
	v := getEnv("C4_COLOR_PROFILE")
	if v == "" {
		return ProfileDefault
	}
	p, ok := ProfileFromString(v)
	if !ok {
		return ProfileDefault
	}
	return p
}

// Helper indirection to avoid os import here.
var getEnv = func(k string) string { return "" }

// SetEnvReader replaces the env reader (used by main to inject os.Getenv).
func SetEnvReader(fn func(string) string) { getEnv = fn }
