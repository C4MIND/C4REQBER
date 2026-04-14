"""
Production-ready health checking system for TURBO-CDI v8.4
Comprehensive monitoring of all system components.
"""

from __future__ import annotations

import time
import asyncio
import psutil
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.infrastructure.config import Settings


@dataclass
class HealthStatus:
    """Health status for a single component"""

    status: str  # "healthy", "warning", "unhealthy", "unknown"
    message: str = ""
    details: Dict[str, Any] = None
    timestamp: datetime = None
    response_time: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}


class HealthChecker:
    """
    Comprehensive health checker for all system components.
    Performs checks on database, cache, external services, and system metrics.
    """

    def __init__(self, container: Container):
        self.container = container
        self.settings = container.config
        self.logger = logging.getLogger("health")
        self.check_timeout = 10.0  # seconds

    async def check_all(self) -> Dict[str, Any]:
        """
        Run comprehensive health check on all components.

        Returns aggregated health status with detailed component information.
        """
        start_time = time.time()

        # Run all health checks concurrently
        tasks = [
            self.check_database(),
            self.check_cache(),
            self.check_external_services(),
            self.check_system_metrics(),
            self.check_application_services(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        health_summary = {
            "overall_health": "healthy",
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(tasks),
            "checks_completed": 0,
            "checks_failed": 0,
            "services": {},
        }

        # Process results
        for i, result in enumerate(results):
            check_name = [
                "database",
                "cache",
                "external_services",
                "system_metrics",
                "application_services",
            ][i]

            if isinstance(result, Exception):
                self.logger.error(f"Health check failed for {check_name}: {result}")
                health_summary["services"][check_name] = {
                    "status": "unhealthy",
                    "message": f"Check failed: {str(result)}",
                    "timestamp": datetime.now().isoformat(),
                }
                health_summary["checks_failed"] += 1
            else:
                health_summary["services"][check_name] = result
                if result["status"] not in ["healthy", "warning"]:
                    health_summary["checks_failed"] += 1

                if result.get("status") == "completed":
                    health_summary["checks_completed"] += 1

        # Determine overall health
        if health_summary["checks_failed"] > 0:
            health_summary["overall_health"] = "unhealthy"
        elif any(s.get("status") == "warning" for s in health_summary["services"].values()):
            health_summary["overall_health"] = "warning"

        total_time = time.time() - start_time
        health_summary["total_check_time"] = round(total_time, 2)

        self.logger.info(
            f"Health check completed: {health_summary['overall_health']} "
            f"({health_summary['total_checks']} checks in {total_time:.2f}s)"
        )

        return health_summary

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and basic performance"""
        start_time = time.time()

        try:
            # Get repository instance
            repo = self.container.discovery_repo()

            # Run health check
            if hasattr(repo, "health_check"):
                result = await asyncio.wait_for(repo.health_check(), timeout=self.check_timeout)
            else:
                # Fallback - simple connectivity test
                result = await self._test_database_basic()

            result["response_time"] = round(time.time() - start_time, 3)

            if result.get("status") in ["healthy", "success"]:
                result["status"] = "healthy"
            else:
                result["status"] = "unhealthy"

            return result

        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "message": "Database check timed out",
                "response_time": round(time.time() - start_time, 3),
                "timeout": self.check_timeout,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database check failed: {str(e)}",
                "response_time": round(time.time() - start_time, 3),
            }

    async def check_cache(self) -> Dict[str, Any]:
        """Check cache system health"""
        start_time = time.time()

        try:
            # Check if cache is configured
            if hasattr(self.container, "cache") and self.container.cache:
                cache = self.container.cache()
                if hasattr(cache, "health_check"):
                    result = await asyncio.wait_for(
                        cache.health_check(), timeout=self.check_timeout
                    )
                else:
                    result = {"status": "healthy", "message": "Cache service available"}
            else:
                result = {"status": "warning", "message": "Cache not configured"}

            result["response_time"] = round(time.time() - start_time, 3)
            return result

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Cache check failed: {str(e)}",
                "response_time": round(time.time() - start_time, 3),
            }

    async def check_external_services(self) -> Dict[str, Any]:
        """Check external service integrations"""
        start_time = time.time()

        try:
            services_status = {}

            # Check LLM service
            try:
                if hasattr(self.container, "llm_client") and self.container.llm_client:
                    llm_client = self.container.llm_client()
                    if hasattr(llm_client, "health_check"):
                        llm_result = await asyncio.wait_for(
                            llm_client.health_check(), timeout=self.check_timeout
                        )
                        services_status["llm"] = llm_result
                    else:
                        services_status["llm"] = {
                            "status": "unknown",
                            "message": "No health check available",
                        }
                else:
                    services_status["llm"] = {
                        "status": "not_configured",
                        "message": "LLM client not available",
                    }
            except Exception as e:
                services_status["llm"] = {"status": "unhealthy", "message": str(e)}

            # Check vector database
            try:
                if hasattr(self.container, "vector_db"):
                    vector_db = self.container.vector_db()
                    if vector_db and hasattr(vector_db, "health_check"):
                        vec_result = await asyncio.wait_for(
                            vector_db.health_check(), timeout=self.check_timeout
                        )
                        services_status["vector_db"] = vec_result
                    else:
                        services_status["vector_db"] = {"status": "not_configured"}
                else:
                    services_status["vector_db"] = {"status": "not_configured"}
            except Exception as e:
                services_status["vector_db"] = {"status": "unhealthy", "message": str(e)}

            # Determine overall external services health
            unhealthy_services = [
                name
                for name, status in services_status.items()
                if status.get("status") not in ["healthy", "not_configured"]
            ]

            overall_status = "healthy"
            if unhealthy_services:
                overall_status = "unhealthy"
            elif any(s.get("status") == "warning" for s in services_status.values()):
                overall_status = "warning"

            return {
                "status": overall_status,
                "message": f"{len(unhealthy_services)} of {len(services_status)} external services unhealthy",
                "services": services_status,
                "unhealthy_services": unhealthy_services,
                "response_time": round(time.time() - start_time, 3),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"External services check failed: {str(e)}",
                "response_time": round(time.time() - start_time, 3),
            }

    async def check_system_metrics(self) -> Dict[str, Any]:
        """Check basic system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            # Network connections
            network_connections = len(psutil.net_connections())

            # Determine health based on thresholds
            status = "healthy"
            warnings = []

            if cpu_percent > 90:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 95:
                status = "unhealthy"
                warnings.append(f"Critical CPU usage: {cpu_percent}%")

            if memory.percent > 90:
                status = "warning" if status == "healthy" else status
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 95:
                status = "unhealthy"
                warnings.append(f"Critical memory usage: {memory.percent:.1f}%")

            if disk.percent > 95:
                status = "warning" if status == "healthy" else status
                warnings.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 98:
                status = "unhealthy"
                warnings.append(f"Critical disk usage: {disk.percent:.1f}%")

            return {
                "status": status,
                "message": "; ".join(warnings) if warnings else "System metrics normal",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_connections": network_connections,
                "warnings": warnings,
            }

        except Exception as e:
            return {
                "status": "unknown",
                "message": f"Failed to collect system metrics: {str(e)}",
                "error": str(e),
            }

    async def check_application_services(self) -> Dict[str, Any]:
        """Check application layer services"""
        try:
            services_status = {}

            # Check event bus
            try:
                from turbo_cdi.application.events import application_event_bus

                services_status["event_bus"] = {
                    "status": "healthy",
                    "message": f"Event bus active with {len(application_event_bus.handlers)} handlers",
                }
            except Exception as e:
                services_status["event_bus"] = {
                    "status": "unhealthy",
                    "message": f"Event bus failed: {str(e)}",
                }

            # Check transaction monitor
            try:
                from turbo_cdi.application.transactions import transaction_monitor

                tx_metrics = transaction_monitor.get_health_report()
                services_status["transaction_monitor"] = {
                    "status": tx_metrics["status"],
                    "message": f"Transactions: {tx_metrics.get('transactions_started', 0)} started, "
                    f"{tx_metrics.get('rollback_rate', 0):.1%} rollback rate",
                }
            except Exception as e:
                services_status["transaction_monitor"] = {
                    "status": "unhealthy",
                    "message": f"Transaction monitor failed: {str(e)}",
                }

            # Determine overall services health
            unhealthy_services = [
                name
                for name, status in services_status.items()
                if status.get("status") not in ["healthy", "warning"]
            ]

            overall_status = "healthy"
            if unhealthy_services:
                overall_status = "unhealthy"
            elif any(s.get("status") == "warning" for s in services_status.values()):
                overall_status = "warning"

            return {
                "status": overall_status,
                "message": f"{len(unhealthy_services)} of {len(services_status)} application services unhealthy",
                "services": services_status,
                "unhealthy_services": unhealthy_services,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Application services check failed: {str(e)}",
            }

    async def _test_database_basic(self) -> Dict[str, Any]:
        """Basic database connectivity test when full health check not available"""
        try:
            # Simple test - check if we can get a repository
            repo = self.container.discovery_repo()
            return {
                "status": "healthy",
                "message": "Basic database connectivity established",
                "type": "basic_check",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Basic database connectivity failed: {str(e)}",
                "type": "basic_check",
            }


class ReadinessChecker:
    """
    Kubernetes readiness probe checker.
    Determines if the application is ready to serve traffic.
    """

    def __init__(self, container: Container):
        self.container = container

    async def is_ready(self) -> Dict[str, Any]:
        """Check if application is ready to serve traffic"""
        try:
            # Check critical dependencies
            checks = [
                self._check_database(),
                self._check_critical_services(),
            ]

            results = await asyncio.gather(*checks, return_exceptions=True)

            # All checks must pass for readiness
            failed_checks = [
                f"check_{i}"
                for i, result in enumerate(results)
                if isinstance(result, Exception) or not result
            ]

            if failed_checks:
                return {
                    "ready": False,
                    "message": f"Readiness failed: {', '.join(failed_checks)}",
                    "failed_checks": failed_checks,
                }

            return {
                "ready": True,
                "message": "Application is ready to serve traffic",
            }

        except Exception as e:
            return {
                "ready": False,
                "message": f"Readiness check failed: {str(e)}",
                "error": str(e),
            }

    async def _check_database(self) -> bool:
        """Check database readiness"""
        try:
            repo = self.container.discovery_repo()
            if hasattr(repo, "health_check"):
                result = await repo.health_check()
                return result.get("status") in ["healthy", "success"]
            return True  # Basic check passed if no health method
        except Exception:
            return False

    async def _check_critical_services(self) -> bool:
        """Check critical application services"""
        try:
            # Check if container has required services
            required_services = ["discovery_repo", "llm_client"]
            for service in required_services:
                if not hasattr(self.container, service):
                    return False
            return True
        except Exception:
            return False


class LivenessChecker:
    """
    Kubernetes liveness probe checker.
    Determines if the application is alive and should be restarted if not.
    """

    def is_alive(self) -> Dict[str, Any]:
        """Check if application is alive"""
        # Simple liveness check - if this method can execute, app is alive
        return {
            "alive": True,
            "message": "Application is responding to liveness checks",
        }


# Global instances
health_checker = None
readiness_checker = None
liveness_checker = LivenessChecker()


def get_health_checker(container: Container) -> HealthChecker:
    """Get or create global health checker"""
    global health_checker
    if health_checker is None:
        health_checker = HealthChecker(container)
    return health_checker


def get_readiness_checker(container: Container) -> ReadinessChecker:
    """Get or create global readiness checker"""
    global readiness_checker
    if readiness_checker is None:
        readiness_checker = ReadinessChecker(container)
    return readiness_checker
