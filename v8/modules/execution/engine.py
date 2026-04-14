# Execution Engine - Stub for testing
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable


@dataclass
class ExecutionEngine:
    """Stub execution engine for integration testing."""

    def __init__(self):
        self.executors: Dict[str, Callable] = {}

    def execute_step(self, step: Dict, context: Optional[Dict] = None) -> Dict:
        """Execute a single step."""
        return {"success": True, "step": step, "result": None}

    def register_executor(self, name: str, executor: Callable) -> None:
        """Register a custom executor."""
        self.executors[name] = executor
