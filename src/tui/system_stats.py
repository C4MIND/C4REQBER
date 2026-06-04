"""
TUI: System Stats Monitor
CPU/RAM monitoring via psutil.
"""
from __future__ import annotations

from typing import Any


try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_system_stats() -> dict[str, Any]:
    """Get CPU and RAM statistics."""
    if HAS_PSUTIL:
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.0),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        }
    return {
        "cpu_percent": 0,
        "ram_percent": 0,
        "ram_used_gb": 0.0,
        "ram_total_gb": 0.0,
        "note": "psutil not installed. pip install psutil for real-time system stats.",
    }
