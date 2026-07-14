# TURBO-CDI Design System

A comprehensive design system providing consistent visual language across CLI and Web interfaces.

## Overview

The TURBO-CDI Design System ensures cohesive user experience through:

- **Color Tokens**: Semantic color system with dark theme support
- **Typography**: Scalable type scale with Inter font family
- **Spacing**: 8px grid-based spacing system
- **Components**: Reusable UI components for both CLI and Web

## Quick Start

### CLI Usage

```python
from src.design import DesignTokens, StyledPanel, PanelType, ErrorDisplay

# Use color tokens
print(f"Primary color: {DesignTokens.PRIMARY.hex}")

# Create styled panels
panel = StyledPanel.create(
    "Your content here",
    "Title",
    PanelType.SUCCESS
)
console.print(panel)

# Standardized error display
ErrorDisplay.show_error(
    "Connection failed",
    suggestion="Check your internet connection"
)
```

### Web Usage

```css
@import 'styles/design-system.css';

.my-component {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}
```

## Color System

### Brand Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `PRIMARY` | #4ECDC4 | 78, 205, 196 | Primary actions, discovery |
| `SECONDARY` | #FF6B6B | 255, 107, 107 | Warnings, alerts |
| `ACCENT` | #FFE66D | 255, 230, 109 | Highlights, confidence |
| `SUCCESS` | #2ecc71 | 46, 204, 113 | Validation, success |
| `WARNING` | #f39c12 | 243, 156, 18 | Cautions, pending |
| `ERROR` | #e74c3c | 231, 76, 60 | Errors, failures |
| `INFO` | #3498db | 52, 152, 219 | Information, IDs |

### Dark Theme Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `DARK_BG_PRIMARY` | #0f0f1a | Main background |
| `DARK_BG_SECONDARY` | #1a1a2e | Cards, surfaces |
| `DARK_BG_TERTIARY` | #16213e | Elevated elements |
| `DARK_BG_ELEVATED` | #0f3460 | Active/Selected |

## Spacing System

Based on 8px grid:

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight spacing |
| `space-2` | 8px | Default spacing |
| `space-4` | 16px | Section padding |
| `space-6` | 24px | Large gaps |
| `space-8` | 32px | Section margins |

## Typography

### Font Stack

```python
TYPOGRAPHY["family"]["sans"]   # Inter + system fonts
TYPOGRAPHY["family"]["mono"]   # JetBrains Mono + Fira Code
```

### Type Scale

| Token | Size | Usage |
|-------|------|-------|
| `text-xs` | 12px | Captions, labels |
| `text-sm` | 14px | Small text |
| `text-base` | 16px | Body text |
| `text-lg` | 18px | Large body |
| `text-xl` | 20px | Lead text |
| `text-2xl` | 24px | H3 headings |
| `text-3xl` | 30px | H2 headings |
| `text-4xl` | 36px | H1 headings |

## CLI Components

### StyledPanel

Creates consistently styled panels:

```python
from src.design.cli_output import StyledPanel, PanelType

# Pre-defined panel types
StyledPanel.info("Content", "Info")
StyledPanel.success("Operation completed", "Success")
StyledPanel.warning("Check settings", "Warning")
StyledPanel.error("Failed to connect", "Error")
StyledPanel.result(hypothesis_data, "Hypothesis")
StyledPanel.discovery(summary, "Discovery")
```

### StyledTable

Creates standardized tables:

```python
from src.design.cli_output import StyledTable

# Pre-defined tables
table = StyledTable.hypothesis_table()
table = StyledTable.discovery_table()
table = StyledTable.search_results_table()

# Custom table
table = StyledTable.create(
    "Custom Table",
    [
        {"name": "ID", "type": "id", "width": 8},
        {"name": "Name", "type": "name"},
        {"name": "Value", "type": "value"},
    ]
)
```

### Progress Indicators

```python
from src.design.cli_output import ProgressIndicator

# Discovery operations
with ProgressIndicator.discovery_progress() as progress:
    task = progress.add_task("Analyzing...", total=100)
    # ... do work ...
    progress.update(task, advance=10)

# Search operations
with ProgressIndicator.search_progress() as progress:
    task = progress.add_task("Searching...")

# Multi-agent operations
with ProgressIndicator.agent_progress() as progress:
    task = progress.add_task("Running agents...", total=100)

# Validation operations
with ProgressIndicator.validation_progress() as progress:
    task = progress.add_task("Validating...", total=100)
```

### Error Display

```python
from src.design.cli_output import ErrorDisplay

# Show error with suggestion
ErrorDisplay.show_error(
    "Database connection failed",
    suggestion="Check DATABASE_URL environment variable"
)

# Show warning
ErrorDisplay.show_warning(
    "Using cached results",
    suggestion="Results may be outdated"
)

# Show info
ErrorDisplay.show_info("New version available", "Update")
```

### Result Display

```python
from src.design.cli_output import ResultDisplay

# Hypothesis card
ResultDisplay.hypothesis_card(
    hypothesis="Quantum entanglement enables...",
    confidence=0.87,
    method="C4+TRIZ Hybrid",
    c4_path=["Present", "Abstract", "System"],
    supporting_evidence=["Paper A", "Paper B"]
)

# Metrics grid
ResultDisplay.metrics_grid({
    "Hypotheses": 12,
    "Confidence": "87%",
    "Time": "2.3s",
    "Sources": 45
})

# Discovery summary
ResultDisplay.discovery_summary(
    problem="Quantum computing optimization",
    hypotheses_count=5,
    avg_confidence=0.82,
    methods_used=["C4", "TRIZ", "Analogy"]
)
```

### Status Indicators

```python
from src.design.cli_output import StatusIndicator

# Status badge
badge = StatusIndicator.get_status_badge("success")
# Output: "[green]✓ SUCCESS[/green]"

# Confidence bar
bar = StatusIndicator.get_confidence_bar(0.75, width=20)
# Visual bar with percentage
```

## Web CSS Variables

All design tokens are available as CSS custom properties:

```css
/* Colors */
color: var(--color-primary);
background-color: var(--bg-secondary);

/* Spacing */
padding: var(--space-4);
margin: var(--space-2);

/* Typography */
font-family: var(--font-sans);
font-size: var(--text-lg);
font-weight: var(--font-semibold);

/* Border radius */
border-radius: var(--radius-lg);

/* Shadows */
box-shadow: var(--shadow-lg);
box-shadow: var(--shadow-glow-primary);

/* Transitions */
transition: all var(--transition-normal) var(--ease-out);
```

## Icons

Icon system uses consistent symbols across CLI and Web:

```python
from src.design import ICONS

ICONS["discover"]   # 🔬
ICONS["search"]     # 🔍
ICONS["hypothesis"] # 💡
ICONS["success"]    # ✓
ICONS["error"]      # ✗
ICONS["warning"]    # ⚠️
ICONS["agent"]      # 🤖
```

## File Structure

```
src/design/
├── __init__.py      # Public API exports
├── tokens.py        # Design tokens (colors, spacing, typography)
└── cli_output.py    # CLI output components

web-v2/styles/
└── design-system.css # CSS custom properties

docs/design-system/
└── README.md        # This documentation
```

## Migration Guide

### From Hardcoded Colors

**Before:**
```python
print("[cyan]Some text[/cyan]")
```

**After:**
```python
from src.design import DesignTokens
print(f"[{DesignTokens.INFO.hex}]Some text[/{DesignTokens.INFO.hex}]")
```

### From Inconsistent Panels

**Before:**
```python
from rich.panel import Panel
Panel(content, title="Title", border_style="cyan")
```

**After:**
```python
from src.design.cli_output import StyledPanel, PanelType
StyledPanel.create(content, "Title", PanelType.INFO)
```

## Best Practices

1. **Always use design tokens** - Never hardcode colors or values
2. **Use semantic types** - Choose panel/table types based on content meaning
3. **Maintain consistency** - Use the same patterns across all commands
4. **Test contrast** - Ensure text is readable on all backgrounds
5. **Consider accessibility** - Add proper labels and ARIA attributes

## Contributing

When adding new tokens:

1. Add to `src/design/tokens.py`
2. Update CSS variables in `web-v2/styles/design-system.css`
3. Document in this README
4. Update version in `__init__.py`
