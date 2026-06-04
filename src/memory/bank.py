"""
C4REQBER: Structural Memory Bank
Persistent storage for intermediate results, partial isomorphisms, and failed attempts.

DEPRECATED: This module has been split. Use src.memory.core and src.memory.operations instead.
This file remains as a backward-compatibility wrapper.
"""
from __future__ import annotations

from typing import Any


__all__ = [
    "MemoryQuery",
    "StructuralMemoryBank",
]

from src.memory.core import MemoryQuery, StructuralMemoryBank
from src.memory.operations import ValidationOperations


# Attach validation methods to StructuralMemoryBank for backward compatibility
# Validation operations are accessed via the bank instance

_original_init = StructuralMemoryBank.__init__


def _compat_init(self, db_path: Any=None) -> None:  # type: ignore[no-untyped-def]
    _original_init(self, db_path)
    self._validation_ops = ValidationOperations(self)


StructuralMemoryBank.__init__ = _compat_init  # type: ignore[method-assign]

# Add backward-compatible validation methods
StructuralMemoryBank.create_validation = lambda self, experiment: self._validation_ops.create_validation(experiment)  # type: ignore[attr-defined]
StructuralMemoryBank.get_validation = lambda self, exp_id, user_id=None: self._validation_ops.get_validation(exp_id, user_id)  # type: ignore[attr-defined]
StructuralMemoryBank.list_validations = lambda self, status=None, user_id=None: self._validation_ops.list_validations(status, user_id)  # type: ignore[attr-defined]
StructuralMemoryBank.update_validation = lambda self, exp_id, updates, user_id=None: self._validation_ops.update_validation(exp_id, updates, user_id)  # type: ignore[attr-defined]
StructuralMemoryBank.get_validation_async = lambda self, exp_id, user_id=None: self._validation_ops.get_validation_async(exp_id, user_id)  # type: ignore[attr-defined]
StructuralMemoryBank.list_validations_async = lambda self, status=None, user_id=None: self._validation_ops.list_validations_async(status, user_id)  # type: ignore[attr-defined]
StructuralMemoryBank.create_validation_async = lambda self, experiment: self._validation_ops.create_validation_async(experiment)  # type: ignore[attr-defined]
StructuralMemoryBank.update_validation_async = lambda self, exp_id, updates, user_id=None: self._validation_ops.update_validation_async(exp_id, updates, user_id)  # type: ignore[attr-defined]
