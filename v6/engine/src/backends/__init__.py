"""
TURBO-CDI Validation Backends

Optional backends for formal verification and model checking.
These are stubs - full integration requires external tools.
"""

from .agda_stub import AgdaBackend, get_agda_backend
from .tla_stub import TlaBackend, get_tla_backend

__all__ = [
    'AgdaBackend',
    'get_agda_backend',
    'TlaBackend', 
    'get_tla_backend',
]

BACKEND_STATUS = {
    'agda': 'stub',  # Proof script generation only
    'tla': 'stub',   # Spec generation only
    'coq': 'planned',
    'alloy': 'planned',
}

def get_backend_status():
    """Get status of all validation backends"""
    return BACKEND_STATUS
