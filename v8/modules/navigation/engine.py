"""
TURBO-CDI v8.0 - Navigation Module
L4: C4 Space Navigation (27 states, A* pathfinding)

Standalone module for C4 state navigation.
Implements Theorem 11: Any state reachable in ≤6 steps.
"""

from typing import List, Optional, Tuple
import heapq
from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis


class NavigationEngine:
    """
    L4: C4-Meta Navigation Engine

    Implements A* pathfinding through C4 space (Z₃³).
    27 states, any state reachable in ≤6 steps.
    """

    def __init__(self):
        self._all_states = self._generate_all_states()
        self._neighbor_cache: dict[C4State, List[C4State]] = {}

    def _generate_all_states(self) -> List[C4State]:
        """Generate all 27 C4 states"""
        return [
            C4State(t, d, a) for t in TimeAxis for d in ScaleAxis for a in AgencyAxis
        ]

    def get_all_states(self) -> List[C4State]:
        """Return all 27 C4 states"""
        return self._all_states.copy()

    def distance(self, s1: C4State, s2: C4State) -> int:
        """
        Calculate Hamming distance between two states.
        Each axis can change by -1, 0, or +1 (mod 3).
        """
        t_dist = min(
            abs(s1.time.value - s2.time.value), 3 - abs(s1.time.value - s2.time.value)
        )
        d_dist = min(
            abs(s1.scale.value - s2.scale.value),
            3 - abs(s1.scale.value - s2.scale.value),
        )
        a_dist = min(
            abs(s1.agency.value - s2.agency.value),
            3 - abs(s1.agency.value - s2.agency.value),
        )
        return t_dist + d_dist + a_dist

    def get_neighbors(self, state: C4State) -> List[C4State]:
        """
        Get all states reachable in one step from current state.
        A step changes exactly one axis by ±1 (mod 3).
        """
        if state in self._neighbor_cache:
            return self._neighbor_cache[state]

        neighbors = []

        # Change time axis
        for dt in [-1, 1]:
            new_time = TimeAxis((state.time.value + dt) % 3)
            neighbors.append(C4State(new_time, state.scale, state.agency))

        # Change scale axis
        for dd in [-1, 1]:
            new_scale = ScaleAxis((state.scale.value + dd) % 3)
            neighbors.append(C4State(state.time, new_scale, state.agency))

        # Change agency axis
        for da in [-1, 1]:
            new_agency = AgencyAxis((state.agency.value + da) % 3)
            neighbors.append(C4State(state.time, state.scale, new_agency))

        self._neighbor_cache[state] = neighbors
        return neighbors

    def navigate(self, from_state: C4State, to_state: C4State) -> List[C4State]:
        """
        A* pathfinding from from_state to to_state.
        Returns path including start and end states.
        """
        if from_state == to_state:
            return [from_state]

        # A* algorithm
        open_set: List[Tuple[float, int, C4State]] = []
        counter = 0
        heapq.heappush(open_set, (0, counter, from_state))

        came_from: dict[C4State, C4State] = {}
        g_score: dict[C4State, float] = {from_state: 0}
        f_score: dict[C4State, float] = {
            from_state: self.distance(from_state, to_state)
        }

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == to_state:
                return self._reconstruct_path(came_from, current)

            for neighbor in self.get_neighbors(current):
                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.distance(neighbor, to_state)
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))

        return []  # No path found (shouldn't happen in C4)

    def _reconstruct_path(self, came_from: dict, current: C4State) -> List[C4State]:
        """Reconstruct path from A* came_from map"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))

    def calculate_path_cost(self, path: List[C4State]) -> float:
        """Calculate cost of a path (sum of step costs)"""
        if len(path) < 2:
            return 0.0

        cost = 0.0
        for i in range(len(path) - 1):
            cost += self.distance(path[i], path[i + 1])

        return cost

    def verify_theorem_11(self, n_trials: int = 1000) -> Tuple[bool, Optional[dict]]:
        """
        Verify Theorem 11: Any state reachable in ≤6 steps.

        Tests n random state pairs.
        Returns (passed, counter_example if failed).
        """
        import random

        all_states = self._all_states

        for _ in range(n_trials):
            s1 = random.choice(all_states)
            s2 = random.choice(all_states)

            path = self.navigate(s1, s2)

            if len(path) - 1 > 6:  # -1 because path includes start
                return False, {
                    "from": str(s1),
                    "to": str(s2),
                    "actual_steps": len(path) - 1,
                    "max_allowed": 6,
                }

        return True, None
