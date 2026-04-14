"""
TURBO-CDI v7.0 - Cache Module
Performance optimization through intelligent caching

Implements:
- Path caching for C4 navigation
- State transformation memoization
- LRU eviction policies
"""

from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict

from core.meta_prime_engine import C4State


@lru_cache(maxsize=256)
def cached_path(start_hash: int, goal_hash: int) -> Optional[List]:
    """Cache computed navigation paths using state hashes"""
    # This will be populated by the navigation system
    return None


class C4Cache:
    """
    LRU Cache for C4 states and transformations.
    
    Provides efficient caching for:
    - Navigation paths between C4 states
    - Domain profile lookups
    - Transformation results
    
    Uses OrderedDict for O(1) LRU eviction.
    """
    
    def __init__(self, maxsize: int = 128):
        self._state_cache: Dict[int, C4State] = {}
        self._path_cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
    
    def get_path(self, start: C4State, goal: C4State) -> Optional[List]:
        """Get cached path between two C4 states"""
        key = (hash(start), hash(goal))
        if key in self._path_cache:
            # Move to end (most recently used)
            self._path_cache.move_to_end(key)
            return self._path_cache[key]
        return None
    
    def set_path(self, start: C4State, goal: C4State, path: List):
        """Cache a path between two C4 states with LRU eviction"""
        key = (hash(start), hash(goal))
        
        # Evict oldest if at capacity
        if len(self._path_cache) >= self._maxsize:
            self._path_cache.popitem(last=False)
        
        self._path_cache[key] = path
        self._path_cache.move_to_end(key)
    
    def get_state(self, state_hash: int) -> Optional[C4State]:
        """Get cached C4 state by hash"""
        return self._state_cache.get(state_hash)
    
    def set_state(self, state_hash: int, state: C4State):
        """Cache a C4 state"""
        if len(self._state_cache) >= self._maxsize:
            # Evict oldest
            self._state_cache.pop(next(iter(self._state_cache)))
        self._state_cache[state_hash] = state
    
    def clear(self):
        """Clear all caches"""
        self._state_cache.clear()
        self._path_cache.clear()
    
    @property
    def path_cache_size(self) -> int:
        """Current number of cached paths"""
        return len(self._path_cache)
    
    @property
    def state_cache_size(self) -> int:
        """Current number of cached states"""
        return len(self._state_cache)


class TransformationCache:
    """Cache for transformation results"""
    
    def __init__(self, maxsize: int = 256):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
    
    def get(self, operation_key: str) -> Optional[Dict]:
        """Get cached transformation result"""
        if operation_key in self._cache:
            self._cache.move_to_end(operation_key)
            return self._cache[operation_key]
        return None
    
    def set(self, operation_key: str, result: Dict):
        """Cache transformation result"""
        if len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)
        self._cache[operation_key] = result
        self._cache.move_to_end(operation_key)
    
    def invalidate_domain(self, domain: str):
        """Invalidate all cached entries for a domain"""
        keys_to_remove = [
            key for key in self._cache.keys() 
            if domain in key
        ]
        for key in keys_to_remove:
            del self._cache[key]


# Global cache instances
c4_cache = C4Cache()
transformation_cache = TransformationCache()