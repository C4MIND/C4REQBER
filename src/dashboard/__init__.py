"""
c4-cdi-turbo: Dashboard Module
Analytics and business metrics
"""
from __future__ import annotations

from src.dashboard.metrics import (
    Dashboard,
    DashboardMetrics,
    get_dashboard,
)


__all__ = [
    "Dashboard",
    "DashboardMetrics",
    "get_dashboard",
]
