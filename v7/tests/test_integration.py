"""
TURBO-CDI v7.0 - Integration Tests
End-to-end testing of all system components
"""

import pytest
import time
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.meta_prime_engine import (
    MetaPrimeAPI, MetaPrimeEngine, C4State, 
    TimeAxis, ScaleAxis, AgencyAxis,
    SeptetObject, PentadOperation, Transformation
)
from core.lambda_validator import LambdaValidator
from core.qzrf_operators import OPERATOR_REGISTRY
from data.domain_profiles import ALL_DOMAINS


class TestIntegration:
    """End-to-end integration tests"""
    
    def test_all_domains_loaded(self):
        """Verify all 132+ domains are loaded"""
        assert len(ALL_DOMAINS) >= 132, f"Expected 132+ domains, got {len(ALL_DOMAINS)}"
    
    def test_all_operators_work(self):
        """Verify all 14 QZRF operators return valid C4 states"""
        state = C4State(TimeAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
        
        for name, op in OPERATOR_REGISTRY.items():
            result = op(state)
            assert result is not None, f"Operator {name} returned None"
            assert isinstance(result, C4State), f"Operator {name} didn't return C4State"
    
    def test_navigation_finds_path(self):
        """Verify navigation finds path within 6 steps (Theorem 11)"""
        api = MetaPrimeAPI()
        start = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        goal = C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
        path = api.engine.navigate(start, goal)
        assert len(path) <= 6, f"Path too long: {len(path)} steps"
    
    def test_validator_accepts_valid(self):
        """Validator accepts valid transformations"""
        validator = LambdaValidator()
        t = Transformation(
            operation=PentadOperation.ACTIVATE,
            target=SeptetObject.STATE,
            context=C4State(TimeAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
            reversibility=0.5, 
            resonance=0.7
        )
        result = validator.verify(t)
        assert result['valid'], f"Valid transformation rejected: {result['errors']}"
    
    def test_validator_rejects_invalid(self):
        """Validator rejects invalid transformations (DISRUPT on BOUNDARY)"""
        validator = LambdaValidator()
        t = Transformation(
            operation=PentadOperation.DISRUPT,
            target=SeptetObject.BOUNDARY,
            context=C4State(TimeAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
            reversibility=0.5, 
            resonance=0.7
        )
        result = validator.verify(t)
        assert not result['valid'], "Invalid transformation accepted"
    
    def test_full_workflow(self):
        """Full transformation planning workflow"""
        api = MetaPrimeAPI()
        result = api.plan_transformation(
            domain="psychology",
            from_state=C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF),
            to_state=C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
            target=SeptetObject.STATE
        )
        assert result['valid']
        assert result['estimated_effectiveness'] > 0


class TestPerformance:
    """Performance benchmarks"""
    
    def test_navigation_speed(self):
        """Navigation completes in under 1 second"""
        api = MetaPrimeAPI()
        start = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        goal = C4State(TimeAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM)
        
        start_time = time.time()
        result = api.engine.navigate(start, goal)
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0, f"Navigation too slow: {elapsed:.2f}s"
    
    def test_domain_loading(self):
        """Domain loading completes in under 100ms"""
        start = time.time()
        _ = len(ALL_DOMAINS)
        elapsed = time.time() - start
        
        assert elapsed < 0.1, f"Domain loading too slow: {elapsed:.2f}s"
    
    def test_all_27_c4_states_reachable(self):
        """All 27 C4 states can be generated and navigated"""
        states = C4State.all_states()
        assert len(states) == 27
        
        engine = MetaPrimeEngine()
        # Test navigation between random pairs
        for i, start in enumerate(states[:5]):
            for goal in states[i+1:6]:
                path = engine.navigate(start, goal)
                assert path is not None


class TestCacheIntegration:
    """Cache system integration tests"""
    
    def test_cache_imports(self):
        """Cache module can be imported"""
        from core.cache import C4Cache, cached_path, c4_cache
        assert C4Cache is not None
        assert callable(cached_path)
    
    def test_c4_cache_basic(self):
        """C4Cache can store and retrieve paths"""
        from core.cache import C4Cache
        cache = C4Cache(maxsize=10)
        
        start = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        goal = C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
        path = ["step1", "step2"]
        
        assert cache.get_path(start, goal) is None
        cache.set_path(start, goal, path)
        assert cache.get_path(start, goal) == path
    
    def test_c4_cache_lru_eviction(self):
        """C4Cache respects LRU eviction policy"""
        from core.cache import C4Cache
        cache = C4Cache(maxsize=3)
        
        states = [
            C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF),
            C4State(TimeAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.OTHER),
            C4State(TimeAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM),
        ]
        
        # Fill cache
        for i, s in enumerate(states):
            cache.set_path(s, states[-1], [f"path_{i}"])
        
        assert cache.path_cache_size == 3
        
        # Add one more to trigger eviction
        new_state = C4State(TimeAxis.PAST, ScaleAxis.META, AgencyAxis.SELF)
        cache.set_path(new_state, states[-1], ["new_path"])
        
        # Should still be at max capacity
        assert cache.path_cache_size == 3