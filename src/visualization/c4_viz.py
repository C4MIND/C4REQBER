"""
TURBO-CDI: C4 Space Visualization
Terminal-based visualization of cognitive navigation
"""

from typing import List, Tuple, Optional

try:
    from ..core.c4_state import C4State
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.c4_state import C4State


class C4Visualizer:
    """
    Visualize C4 state space and navigation paths in terminal.
    """

    def __init__(self):
        self.width = 60
        self.height = 20

    def draw_cube_2d(self, path: Optional[List[C4State]] = None) -> str:
        """
        Draw 2D representation of C4 cube with path.

        Shows 3 slices (T=0,1,2) each with 3x3 S-A grid.
        """
        lines = []
        lines.append("┌" + "─" * 58 + "┐")
        lines.append("│" + " C4 COGNITIVE SPACE (Z₃³) ".center(58) + "│")
        lines.append("└" + "─" * 58 + "┘")
        lines.append("")

        # Path for highlighting
        path_coords = set()
        if path:
            for state in path:
                path_coords.add((state.T, state.S, state.A))

        # Draw each time slice
        time_names = ["PAST (T=0)", "PRESENT (T=1)", "FUTURE (T=2)"]

        for t in range(3):
            lines.append(f"  ╔═══ {time_names[t]} ═══╗")
            lines.append("  ║  S\\A  0:S  1:O  2:Sy ║")
            lines.append("  ║      ┌───┬───┬───┐  ║")

            for s in range(3):
                s_name = ["C", "A", "M"][s]
                row = f"  ║  {s}:{s_name}  │"

                for a in range(3):
                    coord = (t, s, a)

                    if coord in path_coords:
                        # Highlight path
                        idx = (
                            list(path_coords).index(coord)
                            if coord in path_coords
                            else -1
                        )
                        if idx == 0:
                            row += " S "  # Start
                        elif idx == len(path_coords) - 1:
                            row += " E "  # End
                        else:
                            row += f" {idx} "
                    else:
                        row += "   "

                    if a < 2:
                        row += "│"

                row += "  ║"
                lines.append(row)

                if s < 2:
                    lines.append("  ║      ├───┼───┼───┤  ║")

            lines.append("  ║      └───┴───┴───┘  ║")
            lines.append("  ╚═════════════════════╝")
            lines.append("")

        # Legend
        lines.append("  Legend:")
        lines.append("    S = Start    E = End    # = Step number")
        lines.append("    C = Concrete, A = Abstract, M = Meta")
        lines.append("    S = Self, O = Other, Sy = System")

        return "\n".join(lines)

    def draw_path_timeline(self, path: List[C4State], operators: List[str]) -> str:
        """Draw path as timeline."""
        lines = []
        lines.append("NAVIGATION PATH")
        lines.append("═" * 50)
        lines.append("")

        for i, (state, op) in enumerate(zip(path, operators)):
            # State representation
            t_names = ["Past", "Pres", "Fut"]
            s_names = ["Conc", "Abst", "Meta"]
            a_names = ["Self", "Othr", "Syst"]

            state_str = f"F⟨{t_names[state.T]},{s_names[state.S]},{a_names[state.A]}⟩"

            if i == 0:
                lines.append(f"  START: {state_str}")
            else:
                lines.append(f"        ↓ {op}")
                lines.append(f"  Step {i}: {state_str}")

        lines.append("")
        lines.append(f"Total steps: {len(operators)} (Theorem 11: ≤6)")

        return "\n".join(lines)

    def draw_operator_frequencies(self, paths: List[List[str]]) -> str:
        """Draw bar chart of operator usage."""
        from collections import Counter

        # Count all operators
        all_ops = []
        for path in paths:
            all_ops.extend(path)

        counts = Counter(all_ops)

        lines = []
        lines.append("OPERATOR USAGE STATISTICS")
        lines.append("═" * 50)
        lines.append("")

        max_count = max(counts.values()) if counts else 1

        for op, count in counts.most_common(15):
            bar_len = int((count / max_count) * 30)
            bar = "█" * bar_len
            lines.append(f"  {op:15} │{bar:<30}│ {count}")

        return "\n".join(lines)

    def draw_confidence_gauge(self, confidence: float, width: int = 40) -> str:
        """Draw ASCII confidence gauge."""
        filled = int(confidence * width)
        empty = width - filled

        bar = "█" * filled + "░" * empty

        # Color based on confidence
        if confidence >= 0.8:
            color_code = "\033[92m"  # Green
        elif confidence >= 0.5:
            color_code = "\033[93m"  # Yellow
        else:
            color_code = "\033[91m"  # Red

        reset = "\033[0m"

        lines = []
        lines.append(f"Confidence: {confidence:.1%}")
        lines.append(f"[{color_code}{bar}{reset}] {confidence:.2f}")

        return "\n".join(lines)

    def draw_domain_map(self, discoveries_by_domain: dict) -> str:
        """Draw ASCII map of discoveries by domain."""
        lines = []
        lines.append("DISCOVERIES BY DOMAIN")
        lines.append("═" * 50)
        lines.append("")

        max_count = max(discoveries_by_domain.values()) if discoveries_by_domain else 1

        for domain, count in sorted(discoveries_by_domain.items(), key=lambda x: -x[1]):
            bar_len = int((count / max_count) * 30)
            bar = "■" * bar_len
            lines.append(f"  {domain:15} │{bar:<30}│ {count}")

        return "\n".join(lines)


def print_c4_cube(path: Optional[List[C4State]] = None):
    """Utility function to print C4 cube."""
    viz = C4Visualizer()
    print(viz.draw_cube_2d(path))


def print_path(path: List[C4State], operators: List[str]):
    """Utility function to print path."""
    viz = C4Visualizer()
    print(viz.draw_path_timeline(path, operators))
