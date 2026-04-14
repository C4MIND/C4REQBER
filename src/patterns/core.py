"""
TURBO-CDI v6.5 - Core Module
Base classes and utilities for simulation patterns
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class SimulationStatus(Enum):
    """Simulation execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationLevel(Enum):
    """Validation hierarchy levels"""

    FORMAL_PROOF = 5  # Agda/Coq
    MODEL_CHECKING = 4  # TLA+
    PROPERTY_TESTING = 3  # QuickCheck/Hypothesis
    MONTE_CARLO = 2  # Statistical validation
    EMPIRICAL = 1  # Real-world data


@dataclass
class SimulationParameter:
    """Pattern parameter definition"""

    name: str
    type: str
    default: Any = None
    description: str = ""
    min: Optional[float] = None  # Using 'min' to match pattern usage
    max: Optional[float] = None  # Using 'max' to match pattern usage
    options: Optional[list] = None  # For enum-type parameters


@dataclass
class Hypothesis:
    """Simulation hypothesis"""

    text: str = ""
    title: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class SimulationResult:
    """Simulation execution result"""

    simulation_id: str = ""
    pattern_id: str = ""
    status: SimulationStatus = SimulationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    validation_score: float = 0.0
    confidence_score: float = 0.0
    logs: List[str] = field(default_factory=list)
    validation_level: ValidationLevel = ValidationLevel.EMPIRICAL
    error_message: str = ""


class SimulationPattern(ABC):
    """
    Abstract base class for all simulation patterns.
    Follows Christopher Alexander's pattern language structure.
    """

    PATTERN_ID: str = ""
    id: str = ""  # Alias for compatibility
    PATTERN_VERSION: str = "6.5.0"
    PATTERN_CATEGORY: str = "EXTENDED"

    def __init__(self, config: Any = None):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def run(self, hypothesis: Optional[Hypothesis] = None) -> SimulationResult:
        """Execute the simulation pattern"""
        pass

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return pattern metadata"""
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "category": cls.PATTERN_CATEGORY,
            "name": cls.__name__,
        }

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
        """Check if this pattern can simulate the hypothesis"""
        return False

    def estimate_resources(self) -> Dict[str, Any]:
        """Estimate computational resources needed"""
        return {
            "memory_mb": 100,
            "cpu_cores": 1,
            "gpu_required": False,
            "estimated_time_seconds": 60,
        }


def simulation_pattern(cls=None, **kwargs):
    """Decorator to register a simulation pattern"""

    def decorator(cls):
        # Set metadata from kwargs
        if "id" in kwargs:
            cls.PATTERN_ID = kwargs["id"]
            cls.id = kwargs["id"]  # Compatibility alias
        if "name" in kwargs:
            cls.PATTERN_NAME = kwargs.get("name", cls.__name__)
            cls.name = kwargs.get("name", cls.__name__)  # Compatibility alias
        if "category" in kwargs:
            cls.PATTERN_CATEGORY = kwargs.get("category", "EXTENDED")
            cls.category = kwargs.get("category", "EXTENDED")  # Compatibility alias
        if "description" in kwargs:
            cls.PATTERN_DESCRIPTION = kwargs.get("description", "")
            cls.description = kwargs.get("description", "")  # Compatibility alias
        if not hasattr(cls, "parameters"):
            cls.parameters = []  # Compatibility for get_metadata
        # Register with global registry
        PatternRegistry.register(cls)
        return cls

    if cls is not None:
        return decorator(cls)
    return decorator


class PatternRegistry:
    """Registry for simulation patterns"""

    _patterns: Dict[str, type] = {}

    @classmethod
    def register(cls, pattern_class: type):
        """Register a pattern class"""
        pattern_id = getattr(pattern_class, "PATTERN_ID", pattern_class.__name__)
        cls._patterns[pattern_id] = pattern_class
        logger.info(f"Registered pattern: {pattern_id}")

    @classmethod
    def get(cls, pattern_id: str) -> Optional[type]:
        """Get a pattern by ID"""
        return cls._patterns.get(pattern_id)

    @classmethod
    def list_patterns(cls) -> List[str]:
        """List all registered pattern IDs"""
        return list(cls._patterns.keys())
