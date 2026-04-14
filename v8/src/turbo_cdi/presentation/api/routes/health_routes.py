"""
API routes for health checking and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.presentation.api.dependencies import get_container
from turbo_cdi.infrastructure.health import HealthChecker
from turbo_cdi.presentation.api.schemas import HealthResponse


router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(
    container: Container = Depends(get_container),
):
    """
    Comprehensive health check for the entire system.

    Checks database connectivity, service availability, cache status,
    and overall system health. Used by load balancers and monitoring systems.
    """
    try:
        # Create health checker
        health_checker = HealthChecker(container)

        # Run comprehensive health check
        health_result = await health_checker.check_all()

        # Determine HTTP status
        status_code = 200 if health_result["overall_health"] == "healthy" else 503

        return HealthResponse(
            status=health_result["overall_health"],
            timestamp=health_result["timestamp"],
            services=health_result["services"],
            database=health_result.get("database", {}),
            cache=health_result.get("cache", {}),
            external_services=health_result.get("external_services", {}),
        )

    except Exception as e:
        # If health check itself fails, return critical error
        return HealthResponse(
            status="critical",
            timestamp="now",
            services={"health_check": {"status": "failed", "error": str(e)}},
        )


@router.get("/database")
async def database_health(
    container: Container = Depends(get_container),
):
    """Check database connectivity and performance."""
    try:
        repo = container.discovery_repo()
        db_health = await repo.health_check()

        return {
            "status": db_health.get("status", "unknown"),
            "connection_time": db_health.get("connection_time"),
            "last_check": "now",
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")


@router.get("/cache")
async def cache_health(
    container: Container = Depends(get_container),
):
    """Check cache system health and performance."""
    try:
        cache = container.cache()
        cache_health = await cache.health_check()

        return {
            "status": cache_health.get("status", "unknown"),
            "hit_rate": cache_health.get("hit_rate"),
            "size": cache_health.get("size"),
            "last_check": "now",
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cache health check failed: {str(e)}")


@router.get("/external-services")
async def external_services_health(
    container: Container = Depends(get_container),
):
    """Check external service integrations (LLM, vector DBs, etc.)."""
    try:
        health_data = {}

        # Check LLM service
        try:
            llm_client = container.llm_client()
            llm_health = await llm_client.health_check()
            health_data["llm"] = llm_health
        except Exception as e:
            health_data["llm"] = {"status": "unhealthy", "error": str(e)}

        # Check vector database (if implemented)
        try:
            vector_db = getattr(container, "vector_db", lambda: None)()
            if vector_db:
                vector_health = await vector_db.health_check()
                health_data["vector_db"] = vector_health
            else:
                health_data["vector_db"] = {"status": "not_configured"}
        except Exception as e:
            health_data["vector_db"] = {"status": "unhealthy", "error": str(e)}

        # Check other external services...

        return {
            "services": health_data,
            "overall_status": "healthy"
            if all(s.get("status") == "healthy" for s in health_data.values())
            else "degraded",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"External services health check failed: {str(e)}"
        )


@router.get("/metrics")
async def system_metrics(
    container: Container = Depends(get_container),
):
    """
    Get detailed system metrics.

    Provides comprehensive performance and usage metrics
    for monitoring and analytics.
    """
    try:
        # Collect metrics from various sources
        metrics = {
            "timestamp": "now",
            "uptime": "unknown",  # TODO: Implement uptime tracking
            "requests_total": 0,  # TODO: Implement request counting
            "active_connections": 0,
            "memory_usage": {
                "rss": 0,
                "vms": 0,
                "percent": 0,
            },
            "cpu_usage": {
                "percent": 0,
            },
        }

        # Get application-level metrics
        try:
            from turbo_cdi.application.events import transaction_monitor, metrics_handler

            metrics.update(
                {
                    "transactions_started": transaction_monitor.metrics["transactions_started"],
                    "transactions_committed": transaction_monitor.metrics["transactions_committed"],
                    "transactions_rolled_back": transaction_monitor.metrics[
                        "transactions_rolled_back"
                    ],
                    "operations_by_type": metrics_handler.get_metrics().get(
                        "operations_by_type", {}
                    ),
                }
            )
        except Exception:
            pass  # Metrics not available yet

        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe.

    Indicates if the application is ready to serve traffic.
    """
    # Simple readiness check - in production, this should check
    # database connectivity, required services, etc.
    return {"status": "ready"}


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe.

    Indicates if the application is alive and healthy.
    """
    # Simple liveness check
    return {"status": "alive"}
