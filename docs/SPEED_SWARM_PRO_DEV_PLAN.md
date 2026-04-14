# TURBO-CDI v4.5 → v5.0
# SPEED-SWARM-PRO Development Plan
## Achieving 10/10 UX + Visual Design Excellence

**Version:** 5.0 Roadmap  
**Duration:** 12 Weeks  
**Team:** 4-6 Engineers + 1 Designer  
**Target:** UX 10/10, Visual Design 10/10  

---

## 🎯 EXECUTIVE SUMMARY

### Current State
| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **UX Score** | 4.2/10 | 10/10 | -5.8 |
| **Visual Design** | 3.8/10 | 10/10 | -6.2 |
| **Web UI Coverage** | 15% | 100% | +85% |
| **Design System** | None | Complete | New |

### Strategic Approach: SPEED-SWARM-PRO

```
┌─────────────────────────────────────────────────────────────────┐
│  SPEED PHASE (Weeks 1-3)    │  Critical fixes, foundation       │
│  SWARM PHASE (Weeks 4-8)    │  Parallel feature implementation  │
│  PRO PHASE (Weeks 9-12)     │  Polish, performance, launch      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📐 PHASE 1: SPEED (Weeks 1-3)
### Foundation & Critical Fixes

**Goal:** Fix critical blockers, establish design system foundation
**Team:** 2 Engineers (Full-time) + 1 Designer (Part-time)

### Week 1: Design System Foundation

#### Day 1-2: Design Tokens Architecture
```python
# src/design/tokens.py
"""
Centralized Design System for TURBO-CDI
Single source of truth for all visual properties
"""

from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass(frozen=True)
class ColorToken:
    """Immutable color definition with semantic meaning."""
    hex: str
    rgb: Tuple[int, int, int]
    name: str
    usage: str

class DesignTokens:
    """Complete design token system."""
    
    # Brand Colors
    PRIMARY = ColorToken(
        hex="#4ECDC4",
        rgb=(78, 205, 196),
        name="Teal",
        usage="Primary actions, discovery, innovation"
    )
    
    SECONDARY = ColorToken(
        hex="#FF6B6B", 
        rgb=(255, 107, 107),
        name="Coral",
        usage="Warnings, alerts, attention"
    )
    
    ACCENT = ColorToken(
        hex="#FFE66D",
        rgb=(255, 230, 109),
        name="Sunshine",
        usage="Highlights, confidence scores, stars"
    )
    
    SUCCESS = ColorToken(
        hex="#2ecc71",
        rgb=(46, 204, 113),
        name="Emerald",
        usage="Validation, success, completion"
    )
    
    WARNING = ColorToken(
        hex="#f39c12",
        rgb=(243, 156, 18),
        name="Amber",
        usage="Cautions, pending states"
    )
    
    ERROR = ColorToken(
        hex="#e74c3c",
        rgb=(231, 76, 60),
        name="Crimson",
        usage="Errors, failures, critical"
    )
    
    INFO = ColorToken(
        hex="#3498db",
        rgb=(52, 152, 219),
        name="Azure",
        usage="Information, IDs, neutral data"
    )
    
    # Neutral Scale
    WHITE = ColorToken("#ffffff", (255, 255, 255), "White", "Primary text")
    GRAY_100 = ColorToken("#f8f9fa", (248, 249, 250), "Gray 100", "Backgrounds")
    GRAY_200 = ColorToken("#e9ecef", (233, 236, 239), "Gray 200", "Borders light")
    GRAY_300 = ColorToken("#dee2e6", (222, 226, 230), "Gray 300", "Borders")
    GRAY_400 = ColorToken("#ced4da", (206, 212, 218), "Gray 400", "Disabled")
    GRAY_500 = ColorToken("#adb5bd", (173, 181, 189), "Gray 500", "Placeholder")
    GRAY_600 = ColorToken("#6c757d", (108, 117, 125), "Gray 600", "Secondary text")
    GRAY_700 = ColorToken("#495057", (73, 80, 87), "Gray 700", "Body text")
    GRAY_800 = ColorToken("#343a40", (52, 58, 64), "Gray 800", "Headers")
    GRAY_900 = ColorToken("#212529", (33, 37, 41), "Gray 900", "Deep backgrounds")
    
    # Dark Theme Specific
    DARK_BG_PRIMARY = ColorToken("#0f0f1a", (15, 15, 26), "Dark Void", "Main background")
    DARK_BG_SECONDARY = ColorToken("#1a1a2e", (26, 26, 46), "Dark Surface", "Cards")
    DARK_BG_TERTIARY = ColorToken("#16213e", (22, 33, 62), "Dark Elevated", "Elevated")
    
    # Semantic Mapping
    SEMANTIC = {
        "identifier": INFO,           # IDs, codes
        "name": PRIMARY,              # Names, titles
        "value": SUCCESS,             # Values, metrics
        "status_pending": WARNING,
        "status_success": SUCCESS,
        "status_error": ERROR,
        "status_info": INFO,
    }

# Spacing System (8px grid)
SPACING = {
    "0": 0,
    "px": 1,
    "0.5": 2,      # xs
    "1": 4,        # sm
    "2": 8,        # md
    "3": 12,
    "4": 16,       # lg
    "5": 20,
    "6": 24,       # xl
    "8": 32,       # 2xl
    "10": 40,
    "12": 48,      # 3xl
    "16": 64,      # 4xl
    "20": 80,
    "24": 96,      # 5xl
}

# Typography Scale
TYPOGRAPHY = {
    "family": {
        "sans": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        "display": "'Inter', sans-serif",  # For headers
    },
    "size": {
        "xs": 12,      # Captions, labels
        "sm": 14,      # Small text
        "base": 16,    # Body
        "lg": 18,      # Large body
        "xl": 20,      # Lead text
        "2xl": 24,     # H3
        "3xl": 30,     # H2
        "4xl": 36,     # H1
        "5xl": 48,     # Display
        "6xl": 60,     # Hero
    },
    "weight": {
        "light": 300,
        "normal": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
        "extrabold": 800,
    },
    "line_height": {
        "none": 1,
        "tight": 1.25,
        "snug": 1.375,
        "normal": 1.5,
        "relaxed": 1.625,
        "loose": 2,
    },
}

# Border Radius
RADIUS = {
    "none": 0,
    "sm": 2,
    "base": 4,
    "md": 6,
    "lg": 8,
    "xl": 12,
    "2xl": 16,
    "3xl": 24,
    "full": 9999,
}

# Shadows
SHADOWS = {
    "none": "none",
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "base": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    "inner": "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
    "glow_primary": "0 0 20px rgba(78, 205, 196, 0.4)",
    "glow_secondary": "0 0 20px rgba(255, 107, 107, 0.4)",
}

# Animation
ANIMATION = {
    "duration": {
        "75": "75ms",
        "100": "100ms",
        "150": "150ms",
        "200": "200ms",
        "300": "300ms",
        "500": "500ms",
        "700": "700ms",
        "1000": "1000ms",
    },
    "easing": {
        "linear": "linear",
        "in": "cubic-bezier(0.4, 0, 1, 1)",
        "out": "cubic-bezier(0, 0, 0.2, 1)",
        "in_out": "cubic-bezier(0.4, 0, 0.2, 1)",
        "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
    },
}

# Icons
ICONS = {
    # Navigation
    "home": "🏠",
    "discover": "🔬",
    "search": "🔍",
    "validate": "✓",
    "dashboard": "📊",
    "settings": "⚙️",
    
    # Actions
    "add": "+",
    "edit": "✎",
    "delete": "🗑",
    "save": "💾",
    "export": "📤",
    "import": "📥",
    "refresh": "↻",
    "close": "✕",
    
    # States
    "success": "✓",
    "error": "✗",
    "warning": "⚠️",
    "info": "ℹ",
    "loading": "◌",
    "pending": "○",
    
    # Features
    "hypothesis": "💡",
    "analogy": "🔗",
    "triz": "⚡",
    "c4": "◈",
    "graph": "🕸",
    "evolution": "📈",
    "effects": "⚛",
    
    # Data
    "paper": "📄",
    "patent": "📜",
    "reference": "📚",
    "experiment": "🧪",
    "metric": "📐",
}
```

**Deliverables:**
- [ ] `src/design/tokens.py` - Complete token system
- [ ] `src/design/__init__.py` - Public API
- [ ] `docs/design-system/README.md` - Documentation
- [ ] Figma file export - Visual reference

---

#### Day 3-4: CSS Custom Properties for Web UI

```css
/* web/styles/design-system.css */

:root {
  /* Colors */
  --color-primary: #4ECDC4;
  --color-primary-rgb: 78, 205, 196;
  --color-primary-light: #6EDDD4;
  --color-primary-dark: #3DBDB4;
  
  --color-secondary: #FF6B6B;
  --color-secondary-rgb: 255, 107, 107;
  --color-secondary-light: #FF8585;
  --color-secondary-dark: #E55A5A;
  
  --color-accent: #FFE66D;
  --color-success: #2ecc71;
  --color-warning: #f39c12;
  --color-error: #e74c3c;
  --color-info: #3498db;
  
  /* Dark theme */
  --bg-primary: #0f0f1a;
  --bg-secondary: #1a1a2e;
  --bg-tertiary: #16213e;
  --bg-elevated: rgba(255, 255, 255, 0.05);
  
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --text-muted: #6c757d;
  
  /* Spacing */
  --space-0: 0;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  
  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 30px;
  --text-4xl: 36px;
  --text-5xl: 48px;
  
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  
  /* Radius */
  --radius-none: 0;
  --radius-sm: 2px;
  --radius-base: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-none: none;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  --shadow-glow-primary: 0 0 20px rgba(78, 205, 196, 0.4);
  --shadow-glow-secondary: 0 0 20px rgba(255, 107, 107, 0.4);
  
  /* Transitions */
  --transition-fast: 150ms;
  --transition-normal: 300ms;
  --transition-slow: 500ms;
  
  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

#### Day 5-7: CLI Output Standardization

```python
# src/design/cli_output.py
"""
Standardized CLI output components using design tokens.
"""

from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.console import Console
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from enum import Enum
from typing import Optional, List, Any

from .tokens import DesignTokens, ICONS

console = Console()

class PanelType(Enum):
    """Semantic panel types with consistent styling."""
    INFO = {
        "border": DesignTokens.INFO.hex,
        "title_style": f"bold {DesignTokens.INFO.hex}",
        "icon": ICONS["info"],
    }
    SUCCESS = {
        "border": DesignTokens.SUCCESS.hex,
        "title_style": f"bold {DesignTokens.SUCCESS.hex}",
        "icon": ICONS["success"],
    }
    WARNING = {
        "border": DesignTokens.WARNING.hex,
        "title_style": f"bold {DesignTokens.WARNING.hex}",
        "icon": ICONS["warning"],
    }
    ERROR = {
        "border": DesignTokens.ERROR.hex,
        "title_style": f"bold {DesignTokens.ERROR.hex}",
        "icon": ICONS["error"],
    }
    RESULT = {
        "border": DesignTokens.PRIMARY.hex,
        "title_style": f"bold {DesignTokens.PRIMARY.hex}",
        "icon": ICONS["hypothesis"],
    }
    DISCOVERY = {
        "border": DesignTokens.PRIMARY.hex,
        "title_style": f"bold bright_white on {DesignTokens.PRIMARY.hex}",
        "icon": ICONS["discover"],
    }

class StyledPanel:
    """Factory for consistently styled panels."""
    
    @staticmethod
    def create(
        content: str,
        title: str,
        panel_type: PanelType,
        subtitle: Optional[str] = None,
        padding: tuple = (1, 2),
    ) -> Panel:
        """Create a standardized panel."""
        config = panel_type.value
        full_title = f"{config['icon']} {title.upper()}"
        
        return Panel(
            content,
            title=full_title,
            title_align="left",
            subtitle=subtitle,
            border_style=config["border"],
            padding=padding,
        )

class StyledTable:
    """Factory for consistently styled tables."""
    
    COLUMN_STYLES = {
        "id": DesignTokens.INFO.hex,
        "name": DesignTokens.PRIMARY.hex,
        "value": DesignTokens.SUCCESS.hex,
        "status_success": DesignTokens.SUCCESS.hex,
        "status_pending": DesignTokens.WARNING.hex,
        "status_error": DesignTokens.ERROR.hex,
        "metric": f"bold {DesignTokens.PRIMARY.hex}",
        "date": "dim",
        "description": "white",
    }
    
    @staticmethod
    def create(
        title: str,
        columns: List[dict],  # [{"name": "ID", "type": "id", "width": 10}, ...]
    ) -> Table:
        """Create a standardized table."""
        table = Table(title=title, show_header=True, header_style="bold white")
        
        for col in columns:
            style = StyledTable.COLUMN_STYLES.get(col.get("type"), "white")
            table.add_column(
                col["name"],
                style=style,
                width=col.get("width"),
                max_width=col.get("max_width"),
                justify=col.get("justify", "left"),
            )
        
        return table

class ProgressIndicator:
    """Standardized progress indicators."""
    
    @staticmethod
    def discovery_progress() -> Progress:
        """Progress bar for discovery operations."""
        return Progress(
            SpinnerColumn(spinner_name="dots", style=DesignTokens.PRIMARY.hex),
            TextColumn("[bold white]{task.description}"),
            BarColumn(complete_style=DesignTokens.PRIMARY.hex, finished_style=DesignTokens.SUCCESS.hex),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )
    
    @staticmethod
    def search_progress() -> Progress:
        """Progress bar for search operations."""
        return Progress(
            SpinnerColumn(spinner_name="line", style=DesignTokens.INFO.hex),
            TextColumn("[bold white]{task.description}"),
            console=console,
        )

class ErrorDisplay:
    """Standardized error display."""
    
    @staticmethod
    def show_error(message: str, suggestion: Optional[str] = None, exit_code: int = 1):
        """Display standardized error."""
        content = f"[bold]{message}[/bold]"
        if suggestion:
            content += f"\n\n[dim]💡 {suggestion}[/dim]"
        
        panel = StyledPanel.create(
            content,
            "Error",
            PanelType.ERROR,
        )
        console.print(panel)
        raise SystemExit(exit_code)
    
    @staticmethod
    def show_warning(message: str, suggestion: Optional[str] = None):
        """Display standardized warning."""
        content = f"[bold]{message}[/bold]"
        if suggestion:
            content += f"\n\n[dim]💡 {suggestion}[/dim]"
        
        panel = StyledPanel.create(
            content,
            "Warning",
            PanelType.WARNING,
        )
        console.print(panel)

class ResultDisplay:
    """Standardized result displays."""
    
    @staticmethod
    def hypothesis_card(
        hypothesis: str,
        confidence: float,
        method: str,
        c4_path: Optional[List[str]] = None,
    ):
        """Display a hypothesis result card."""
        confidence_pct = int(confidence * 100)
        confidence_bar = "█" * (confidence_pct // 10) + "░" * (10 - confidence_pct // 10)
        
        content = f"""[bold white]{hypothesis}[/bold white]

[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]
[bold]Confidence:[/bold]    [{DesignTokens.ACCENT.hex}]{confidence_bar}[/{DesignTokens.ACCENT.hex}] {confidence_pct}%
[bold]Method:[/bold]        {method}
"""
        if c4_path:
            path_str = " → ".join(c4_path)
            content += f"[bold]C4 Path:[/bold]       {path_str}\n"
        
        panel = StyledPanel.create(
            content,
            "Hypothesis",
            PanelType.RESULT,
        )
        console.print(panel)
    
    @staticmethod
    def metrics_grid(metrics: dict):
        """Display metrics in a grid."""
        layout = Layout()
        
        # Create rows
        rows = []
        items = list(metrics.items())
        for i in range(0, len(items), 4):
            row_items = items[i:i+4]
            row_layout = Layout()
            row_layout.split_row(*[
                Layout(ResultDisplay._metric_card(k, v), name=f"metric_{i+j}")
                for j, (k, v) in enumerate(row_items)
            ])
            rows.append(row_layout)
        
        layout.split_column(*rows)
        console.print(layout)
    
    @staticmethod
    def _metric_card(label: str, value: Any) -> Panel:
        """Create a single metric card."""
        content = f"[bold {DesignTokens.PRIMARY.hex}]{value}[/bold {DesignTokens.PRIMARY.hex}]\n[dim]{label}[/dim]"
        return Panel(content, border_style=DesignTokens.PRIMARY.hex)
```

**Week 1 Deliverables:**
- [ ] Complete design token system
- [ ] CSS custom properties
- [ ] CLI output standardization
- [ ] Component documentation

---

### Week 2: CLI Refactoring

**Day 1-2: Command Organization**

```python
# src/main.py - Refactored structure

import typer
from rich.console import Console

from .design.cli_output import StyledPanel, PanelType, ErrorDisplay

# Create main app with categories
app = typer.Typer(
    name="turbo",
    help="TURBO-CDI v5.0 - Scientific Hypothesis Generation Platform",
    rich_markup_mode="rich",
    add_completion=False,  # We'll add it manually
)

# ═══════════════════════════════════════════════════════════════════
# CATEGORY: Core Discovery (Most Used)
# ═══════════════════════════════════════════════════════════════════
core_app = typer.Typer(help="🔬 Core discovery commands")
app.add_typer(core_app, name="")

@core_app.command("solve", help="One-shot full discovery cycle")
def solve_command(...):
    """Generate hypotheses with full analysis in one command."""
    ...

@core_app.command("discover", help="Multi-agent collaborative discovery")
def discover_command(...):
    """Use AI agents (Analyst+Scientist+Critic+Synthesizer)."""
    ...

@core_app.command("explain", help="Explain C4 reasoning")
def explain_command(...):
    """Understand why a C4 path works."""
    ...

# ═══════════════════════════════════════════════════════════════════
# CATEGORY: Research Tools
# ═══════════════════════════════════════════════════════════════════
research_app = typer.Typer(help="📚 Research and analysis tools")
app.add_typer(research_app, name="research")

@research_app.command("search")
def research_search(...):
    """Search academic databases."""
    ...

@research_app.command("triz")
def research_triz(...):
    """TRIZ methodology tools."""
    ...

@research_app.command("analogy")
def research_analogy(...):
    """Cross-domain analogy discovery."""
    ...

# ═══════════════════════════════════════════════════════════════════
# CATEGORY: Validation
# ═══════════════════════════════════════════════════════════════════
validate_app = typer.Typer(help="✓ Validation and testing")
app.add_typer(validate_app, name="validate")

# ... etc

# ═══════════════════════════════════════════════════════════════════
# CATEGORY: System
# ═══════════════════════════════════════════════════════════════════
system_app = typer.Typer(help="⚙️  System commands")
app.add_typer(system_app, name="system")

@system_app.command("status")
def system_status():
    """Check system health."""
    ...

@system_app.command("config")
def system_config():
    """Manage configuration."""
    ...
```

---

**Day 3-4: Error Standardization**

Refactor all error handling to use `ErrorDisplay` class.

---

**Day 5-7: Progress Indicators**

Add stage-by-stage progress for long operations.

```python
# Example: Discovery with stages
with ProgressIndicator.discovery_progress() as progress:
    stages = [
        ("analyzing", "🔍 Analyzing problem structure..."),
        ("searching", "📚 Searching literature (Semantic Scholar)..."),
        ("generating", "💡 Generating hypotheses (C4+TRIZ)..."),
        ("evaluating", "⚖️  Evaluating solutions (Multi-Agent)..."),
        ("synthesizing", "🔗 Synthesizing recommendations..."),
    ]
    
    for stage_id, description in stages:
        task = progress.add_task(description, total=100)
        # ... do work ...
        progress.update(task, completed=100)
```

---

### Week 3: Web UI Critical Fixes

**Day 1-2: Dependency Bundling**

Replace CDN with bundled dependencies:

```bash
# Initialize Vite project
npm create vite@latest web-v2 -- --template react
cd web-v2
npm install

# Install dependencies
npm install @radix-ui/react-dialog @radix-ui/react-tabs
npm install framer-motion lucide-react
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

**Day 3-5: Core Components**

```typescript
// web-v2/src/components/ui/Button.tsx
import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          // Base
          'inline-flex items-center justify-center rounded-lg font-medium',
          'transition-all duration-200 ease-out',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          
          // Variants
          variant === 'primary' && [
            'bg-[#4ECDC4] text-white',
            'hover:bg-[#3DBDB4] hover:shadow-lg hover:shadow-[#4ECDC4]/25',
            'active:scale-95',
            'focus:ring-[#4ECDC4]',
          ],
          variant === 'secondary' && [
            'bg-[#FF6B6B] text-white',
            'hover:bg-[#E55A5A] hover:shadow-lg hover:shadow-[#FF6B6B]/25',
            'focus:ring-[#FF6B6B]',
          ],
          variant === 'accent' && [
            'bg-[#FFE66D] text-[#1a1a2e]',
            'hover:bg-[#FFF0A0]',
            'focus:ring-[#FFE66D]',
          ],
          variant === 'ghost' && [
            'bg-transparent text-white',
            'hover:bg-white/10',
            'focus:ring-white/50',
          ],
          variant === 'danger' && [
            'bg-red-500 text-white',
            'hover:bg-red-600',
            'focus:ring-red-500',
          ],
          
          // Sizes
          size === 'sm' && 'px-3 py-1.5 text-sm',
          size === 'md' && 'px-4 py-2 text-base',
          size === 'lg' && 'px-6 py-3 text-lg',
          
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading...
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
```

---

**Day 6-7: Layout & Navigation**

```typescript
// web-v2/src/components/layout/AppShell.tsx
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0f0f1a] text-white">
      <Sidebar />
      <main className="ml-64 p-8">
        <Header />
        {children}
      </main>
    </div>
  );
}
```

**Phase 1 Deliverables:**
- [ ] Complete design token system
- [ ] Refactored CLI with standardized output
- [ ] Web UI Vite foundation
- [ ] Core component library (Button, Card, Input, etc.)
- [ ] Error handling standardization

---

## 🐝 PHASE 2: SWARM (Weeks 4-8)
### Parallel Feature Implementation

**Goal:** Implement all missing Web UI features in parallel
**Team:** 4 Engineers working in parallel streams

### Stream A: Discovery Features (Weeks 4-6)
**Engineer 1:** Full-time on discovery workflow

```typescript
// Features to implement:
// 1. One-shot discovery page
// 2. Multi-agent discovery page
// 3. Explainability viewer
// 4. Results comparison

// pages/discover/OneShotPage.tsx
export function OneShotPage() {
  const [problem, setProblem] = useState('');
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<ProgressStage[]>([]);

  const handleDiscover = async () => {
    setIsLoading(true);
    setProgress([]);
    
    // WebSocket for real-time progress
    const ws = new WebSocket(`ws://localhost:8000/ws/${uuid()}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'progress') {
        setProgress(prev => [...prev, data]);
      } else if (data.type === 'result') {
        setResult(data.payload);
        setIsLoading(false);
        ws.close();
      }
    };
    
    ws.send(JSON.stringify({
      type: 'discover',
      payload: { problem, max_hypotheses: 5 }
    }));
  };

  return (
    <div className="max-w-4xl mx-auto">
      <PageHeader 
        title="One-Shot Discovery"
        description="Complete research cycle in a single operation"
      />
      
      <Card className="mb-8">
        <Textarea
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
          placeholder="Describe your research problem..."
          className="min-h-[120px]"
        />
        <div className="mt-4 flex justify-end">
          <Button 
            onClick={handleDiscover}
            isLoading={isLoading}
            size="lg"
          >
            <Beaker className="mr-2 h-5 w-5" />
            Start Discovery
          </Button>
        </div>
      </Card>
      
      {isLoading && <DiscoveryProgress stages={progress} />}
      
      {result && <DiscoveryResults result={result} />}
    </div>
  );
}
```

---

### Stream B: Visualization Features (Weeks 4-7)
**Engineer 2:** C4 path, TRIZ matrix, Graph view

```typescript
// pages/visualize/C4PathPage.tsx
// pages/visualize/TrizMatrixPage.tsx
// pages/visualize/GraphViewPage.tsx

// Using D3.js or React Flow for graph visualization
import ReactFlow, { Background, Controls } from 'reactflow';

export function GraphViewPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  
  useEffect(() => {
    fetch('/api/graph/nodes')
      .then(r => r.json())
      .then(data => {
        setNodes(data.nodes.map(n => ({
          id: n.id,
          position: { x: n.x, y: n.y },
          data: { label: n.label, type: n.type },
          style: getNodeStyle(n.type),
        })));
        setEdges(data.edges);
      });
  }, []);

  return (
    <div className="h-[calc(100vh-200px)]">
      <ReactFlow nodes={nodes} edges={edges}>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
```

---

### Stream C: Research Tools (Weeks 4-6)
**Engineer 3:** Search, validation, analytics

```typescript
// pages/research/SearchPage.tsx
// pages/validate/ValidationWorkflow.tsx
// pages/analytics/Dashboard.tsx

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'semantic' | 'arxiv' | 'patents'>('semantic');
  const [results, setResults] = useState<SearchResult[]>([]);

  return (
    <div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="semantic">
            <Database className="mr-2 h-4 w-4" />
            Semantic Scholar
          </TabsTrigger>
          <TabsTrigger value="arxiv">
            <FileText className="mr-2 h-4 w-4" />
            arXiv
          </TabsTrigger>
          <TabsTrigger value="patents">
            <ScrollText className="mr-2 h-4 w-4" />
            Patents
          </TabsTrigger>
        </TabsList>
        
        <div className="mt-6">
          <SearchInput 
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            placeholder={`Search ${activeTab}...`}
          />
          
          <SearchResults results={results} type={activeTab} />
        </div>
      </Tabs>
    </div>
  );
}
```

---

### Stream D: API & Backend (Weeks 4-8)
**Engineer 4:** API improvements, pagination, webhooks

```python
# src/api/server.py - Improvements

# 1. Pagination
from fastapi import Query
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

@app.get("/discoveries", response_model=PaginatedResponse[DiscoveryResponse])
async def list_discoveries(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|confidence|name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    filter_domain: Optional[str] = None,
    filter_status: Optional[str] = None,
):
    """List discoveries with pagination and filtering."""
    ...

# 2. Webhooks for async operations
@app.post("/webhooks/register")
async def register_webhook(
    url: str,
    events: List[str],  # ["discovery.completed", "validation.finished"]
    secret: Optional[str] = None,
):
    """Register webhook for async notifications."""
    ...

# 3. Bulk operations
@app.post("/discoveries/bulk")
async def bulk_operation(
    operation: str,  # "delete", "export", "validate"
    ids: List[str],
):
    """Perform operations on multiple discoveries."""
    ...

# 4. Real-time updates via WebSocket improvements
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Enhanced WebSocket with room support."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            message = await websocket.receive_json()
            
            if message["type"] == "subscribe":
                # Subscribe to room (e.g., specific discovery updates)
                await manager.subscribe(client_id, message["room"])
            
            elif message["type"] == "discover":
                # Stream progress updates
                async for update in run_discovery_stream(message["payload"]):
                    await manager.send_personal_message(update, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

---

### Week 8: Integration & Testing

**All Streams:**
- [ ] Feature integration testing
- [ ] End-to-end workflows
- [ ] Performance optimization
- [ ] Accessibility audit

**Phase 2 Deliverables:**
- [ ] Complete Web UI with all CLI features
- [ ] Enhanced API with pagination
- [ ] WebSocket real-time updates
- [ ] Visualizations (C4 path, TRIZ matrix, Graph)

---

## 🚀 PHASE 3: PRO (Weeks 9-12)
### Polish, Performance & Launch

### Week 9: Animation & Micro-interactions

```typescript
// Framer Motion animations
const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

// Usage
<motion.div
  initial="initial"
  animate="animate"
  exit="exit"
  variants={pageTransition}
>
  <motion.div variants={staggerContainer}>
    {hypotheses.map(h => (
      <motion.div
        key={h.id}
        variants={{
          initial: { opacity: 0, x: -20 },
          animate: { opacity: 1, x: 0 },
        }}
      >
        <HypothesisCard {...h} />
      </motion.div>
    ))}
  </motion.div>
</motion.div>
```

---

### Week 10: Performance Optimization

```typescript
// Lazy loading
const TrizMatrixPage = lazy(() => import('./pages/TrizMatrixPage'));

// Virtualization for long lists
import { VirtualList } from '@tanstack/react-virtual';

// Caching
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
    },
  },
});
```

---

### Week 11: Accessibility & Mobile

```typescript
// ARIA labels, keyboard navigation
<button
  aria-label="Start discovery"
  aria-busy={isLoading}
  aria-describedby="discovery-help"
  onClick={handleDiscover}
>
  Start Discovery
</button>

<p id="discovery-help" className="sr-only">
  This will analyze your problem and generate hypotheses
</p>

// Responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {metrics.map(m => <MetricCard key={m.id} {...m} />)}
</div>
```

---

### Week 12: Documentation & Launch

**Documentation:**
- Storybook for components
- API documentation
- User guides
- Video tutorials

**Launch Checklist:**
- [ ] Security audit
- [ ] Load testing
- [ ] Analytics setup
- [ ] Error tracking (Sentry)
- [ ] Community Discord
- [ ] Landing page

---

## 📊 SUCCESS METRICS

### Week 3 (End of SPEED)
| Metric | Target |
|--------|--------|
| Design System | 100% tokens defined |
| CLI Refactor | 50% commands updated |
| Web UI Base | Vite + Tailwind working |

### Week 8 (End of SWARM)
| Metric | Target |
|--------|--------|
| Feature Parity | 100% (CLI = Web) |
| API Coverage | All endpoints |
| Tests | 80% coverage |

### Week 12 (End of PRO)
| Metric | Target |
|--------|--------|
| UX Score | 10/10 |
| Visual Design | 10/10 |
| Performance | <2s load |
| Accessibility | WCAG 2.1 AA |

---

## 👥 TEAM STRUCTURE

### Required Team

```
Engineering Lead (You)
├── Frontend Engineer (Web UI) - Full time
├── Backend Engineer (API) - Full time  
├── Full-Stack Engineer (Features) - Full time
├── Full-Stack Engineer (Features) - Full time
└── UI/UX Designer - Part time (Weeks 1, 9-12)
```

### Responsibilities

| Role | Weeks 1-3 | Weeks 4-8 | Weeks 9-12 |
|------|-----------|-----------|------------|
| Frontend | Design System + Base | Stream A (Discovery) | Polish + Mobile |
| Backend | Token Architecture | Stream D (API) | Performance |
| Full-Stack 1 | CLI Refactor | Stream B (Viz) | Animation |
| Full-Stack 2 | CLI Refactor | Stream C (Research) | Testing |
| Designer | Tokens + Review | Review | Final Polish |

---

## 🎯 DELIVERABLES BY PHASE

### Phase 1: SPEED
- [ ] `src/design/` - Complete design system
- [ ] Refactored CLI with standardized output
- [ ] Web UI V2 foundation (Vite + React + Tailwind)
- [ ] Component library (Button, Card, Input, Modal, etc.)

### Phase 2: SWARM
- [ ] All 30+ CLI features in Web UI
- [ ] C4 Path visualization
- [ ] TRIZ Interactive Matrix
- [ ] Knowledge Graph visualization
- [ ] Real-time WebSocket updates
- [ ] Enhanced API (pagination, filters)

### Phase 3: PRO
- [ ] Animations and transitions
- [ ] Mobile responsive design
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Performance optimized (<2s load)
- [ ] Complete documentation
- [ ] Launch ready

---

## 💰 ESTIMATED COSTS

| Item | Cost |
|------|------|
| **Personnel (12 weeks)** | |
| 4 Engineers × 12 weeks | ~$60,000 |
| 1 Designer × 6 weeks | ~$9,000 |
| **Infrastructure** | |
| Vercel Pro (hosting) | $20/mo |
| Sentry (error tracking) | $26/mo |
| **Tools** | |
| Figma Professional | $45/mo |
| GitHub Team | $40/mo |
| **Total** | **~$70,000** |

---

## 🎉 EXPECTED OUTCOME

### Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **UX Score** | 4.2/10 | 10/10 |
| **Visual Design** | 3.8/10 | 10/10 |
| **Web UI Coverage** | 15% | 100% |
| **Design System** | None | Complete |
| **Mobile Support** | None | Full |
| **Accessibility** | None | WCAG AA |
| **Animation** | None | Polished |

### User Experience

**Before:**
- Overwhelming CLI with 30+ commands
- Web UI has 3 features
- Inconsistent colors and spacing
- No progress feedback
- Bare except clauses

**After:**
- Organized CLI with categories
- Web UI has all 30+ features
- Consistent design system
- Real-time progress with stages
- Professional error handling
- Beautiful animations
- Mobile responsive
- Accessible to all users

---

## ✅ GO/NO-GO DECISION POINTS

### Week 3 Checkpoint
- [ ] Design system approved
- [ ] CLI refactor 50% complete
- [ ] Web UI base working

**Decision:** Continue to SWARM phase?

### Week 8 Checkpoint  
- [ ] Feature parity achieved
- [ ] All streams integrated
- [ ] Tests passing

**Decision:** Continue to PRO phase?

### Week 12 Launch Review
- [ ] UX score ≥ 9/10
- [ ] Visual score ≥ 9/10
- [ ] Performance targets met
- [ ] All critical bugs fixed

**Decision:** Launch v5.0?

---

## 📞 NEXT STEPS

1. **Review this plan** - Adjust scope/resources as needed
2. **Approve budget** - ~$70K for 12 weeks
3. **Assemble team** - Hire/assign engineers and designer
4. **Schedule kickoff** - Week 1 planning session
5. **Set up infrastructure** - Repos, CI/CD, hosting

---

**Ready to build the perfect TURBO-CDI experience?** 🚀
