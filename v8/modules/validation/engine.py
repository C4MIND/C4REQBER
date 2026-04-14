# Validation Engine - Stub for testing
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class ValidationEngine:
    """Stub validation engine for integration testing."""

    def __init__(self):
        self.validators: List[Any] = []

    def validate_plan(self, plan: Dict) -> Dict:
        """Validate a transformation plan."""
        return {"valid": True, "errors": [], "warnings": []}

    def add_validator(self, validator: Any) -> None:
        """Add a custom validator."""
        self.validators.append(validator)
