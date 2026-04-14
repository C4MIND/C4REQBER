import heapq
from typing import List, Dict
from core.meta_prime_engine import C4State, QZRFOperation, QZRFOperator
from core.qzrf_operators import OPERATOR_REGISTRY


def astar_navigate(start: C4State, goal: C4State) -> List[QZRFOperation]:
    """
    A* pathfinding for C4 navigation
    Guarantees optimal path (minimum steps)
    """
    counter = 0
    open_set = [(0, counter, start, [])]
    g_score: Dict[C4State, float] = {start: 0}
    closed_set = set()
    
    while open_set:
        _, _, current, path = heapq.heappop(open_set)
        
        if current == goal:
            return path
        
        if current in closed_set:
            continue
        closed_set.add(current)
        
        for op_name, transform in OPERATOR_REGISTRY.items():
            next_state = transform(current)
            if next_state is None or next_state in closed_set:
                continue
            
            tentative_g = g_score[current] + 1
            
            if tentative_g < g_score.get(next_state, float('inf')):
                g_score[next_state] = tentative_g
                f = tentative_g + next_state.distance_to(goal)
                counter += 1
                new_path = path + [QZRFOperation(
                    operator=QZRFOperator[op_name],
                    resonance_coefficient=0.7,
                    source_state=current,
                    target_state=next_state
                )]
                heapq.heappush(open_set, (f, counter, next_state, new_path))
    
    return []
