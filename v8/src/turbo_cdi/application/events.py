"""
Application Events for TURBO-CDI v8.4
Cross-cutting concerns and event-driven architecture at application layer.
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, List, Optional, Dict, Any
from datetime import datetime

from turbo_cdi.application.dto import BaseResponse


# Application Event Protocol
from turbo_cdi.domain.entities.advanced import DomainEvent


@dataclass(frozen=True)
class CorpusOperationEvent:
    """Event for corpus operations"""

    event_id: str = field(default_factory=lambda: f"app_{int(datetime.now().timestamp())}")
    event_type: str = "corpus_operation"
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    operation: str = ""  # "create", "update", "delete", "optimize"
    corpus_id: str = ""
    success: bool = True
    duration: float = 0.0
    error_message: Optional[str] = None


@dataclass(frozen=True)
class DiscoveryOperationEvent:
    """Event for discovery operations"""

    event_id: str = field(default_factory=lambda: f"app_{int(datetime.now().timestamp())}")
    event_type: str = "discovery_operation"
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    corpus_id: str = ""
    operation: str = ""  # "anomaly_detection", "presupposition_analysis", "comprehensive"
    anomalies_found: Optional[int] = None
    presuppositions_found: Optional[int] = None
    transformations_applied: Optional[int] = None
    success: bool = True
    duration: float = 0.0


@dataclass(frozen=True)
class SystemHealthEvent:
    """Event for system health monitoring"""

    event_id: str = field(default_factory=lambda: f"app_{int(datetime.now().timestamp())}")
    event_type: str = "system_health"
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    overall_health: str = "unknown"  # "healthy", "warning", "unhealthy"
    services_checked: int = 0
    unhealthy_services: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PerformanceEvent:
    """Event for performance monitoring"""

    event_id: str = field(default_factory=lambda: f"app_{int(datetime.now().timestamp())}")
    event_type: str = "performance"
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    operation: str = ""
    duration: float = 0.0
    memory_used: Optional[float] = None
    cpu_used: Optional[float] = None
    threshold_exceeded: bool = False


@dataclass(frozen=True)
class SecurityEvent:
    """Event for security monitoring"""

    event_id: str = field(default_factory=lambda: f"app_{int(datetime.now().timestamp())}")
    event_type: str = "security"
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    action: str = ""
    user: Optional[str] = None
    resource: Optional[str] = None
    success: bool = True
    suspicious: bool = False


# Event Handlers
@runtime_checkable
class ApplicationEventHandler(Protocol):
    """Protocol for application event handlers"""

    async def handle(self, event: ApplicationEvent) -> None: ...


class LoggingEventHandler:
    """Handler that logs events to the application log"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("application_events")

    async def handle(self, event: ApplicationEvent) -> None:
        """Log the event"""
        log_level = logging.INFO

        # Determine log level based on event type and content
        if hasattr(event, "success") and not event.success:
            log_level = logging.ERROR
        elif hasattr(event, "overall_health") and event.overall_health == "unhealthy":
            log_level = logging.WARNING
        elif hasattr(event, "threshold_exceeded") and event.threshold_exceeded:
            log_level = logging.WARNING

        self.logger.log(
            log_level,
            f"Application Event: {event.event_type}",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "correlation_id": event.correlation_id,
                "user_context": event.user_context,
                "timestamp": event.timestamp.isoformat(),
                **self._extract_event_data(event),
            },
        )

    def _extract_event_data(self, event: ApplicationEvent) -> Dict[str, Any]:
        """Extract relevant data from event for logging"""
        data = {}

        # Extract common fields
        for field in [
            "operation",
            "corpus_id",
            "success",
            "duration",
            "error_message",
            "anomalies_found",
            "presuppositions_found",
            "transformations_applied",
            "overall_health",
            "services_checked",
            "unhealthy_services",
            "memory_used",
            "cpu_used",
            "threshold_exceeded",
            "action",
            "user",
            "resource",
        ]:
            if hasattr(event, field):
                data[field] = getattr(event, field)

        return data


class MetricsEventHandler:
    """Handler that collects metrics from events"""

    def __init__(self):
        self.metrics = {
            "operations_total": 0,
            "operations_by_type": {},
            "errors_total": 0,
            "performance_warnings": 0,
            "health_checks": 0,
        }

    async def handle(self, event: ApplicationEvent) -> None:
        """Collect metrics from the event"""
        self.metrics["operations_total"] += 1

        # Count by operation types
        if hasattr(event, "operation"):
            op_type = event.operation
            if op_type not in self.metrics["operations_by_type"]:
                self.metrics["operations_by_type"][op_type] = 0
            self.metrics["operations_by_type"][op_type] += 1

        # Count errors
        if hasattr(event, "success") and not event.success:
            self.metrics["errors_total"] += 1

        # Count performance warnings
        if hasattr(event, "threshold_exceeded") and event.threshold_exceeded:
            self.metrics["performance_warnings"] += 1

        # Count health checks
        if event.event_type == "system_health":
            self.metrics["health_checks"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = {
            "operations_total": 0,
            "operations_by_type": {},
            "errors_total": 0,
            "performance_warnings": 0,
            "health_checks": 0,
        }


class NotificationEventHandler:
    """Handler that sends notifications for important events"""

    def __init__(self, notification_service: Optional[Any] = None):
        self.notification_service = notification_service
        self.logger = logging.getLogger("notifications")

    async def handle(self, event: ApplicationEvent) -> None:
        """Handle notifications for critical events"""
        notification_needed = self._should_notify(event)

        if notification_needed and self.notification_service:
            await self._send_notification(event)
        elif notification_needed:
            self._log_notification(event)

    def _should_notify(self, event: ApplicationEvent) -> bool:
        """Determine if event requires notification"""
        # Notify on critical errors
        if hasattr(event, "success") and not event.success:
            return True

        # Notify on unhealthy system
        if hasattr(event, "overall_health") and event.overall_health == "unhealthy":
            return True

        # Notify on performance thresholds exceeded
        if hasattr(event, "threshold_exceeded") and event.threshold_exceeded:
            return True

        # Notify on security events
        if event.event_type == "security" and hasattr(event, "suspicious") and event.suspicious:
            return True

        return False

    async def _send_notification(self, event: ApplicationEvent) -> None:
        """Send notification through notification service"""
        message = self._build_notification_message(event)

        # In practice, this would integrate with email, Slack, etc.
        await self.notification_service.send_notification(
            title=f"TURBO-CDI Alert: {event.event_type}",
            message=message,
            priority="high" if self._is_critical(event) else "medium",
            metadata={
                "event_id": event.event_id,
                "correlation_id": event.corpus_id if hasattr(event, "correlation_id") else None,
            },
        )

    def _log_notification(self, event: ApplicationEvent) -> None:
        """Log notification when service not available"""
        message = self._build_notification_message(event)
        self.logger.warning(f"NOTIFICATION: {message}")

    def _build_notification_message(self, event: ApplicationEvent) -> str:
        """Build notification message"""
        if hasattr(event, "error_message") and event.error_message:
            return f"Error in {event.event_type}: {event.error_message}"

        if event.event_type == "system_health":
            unhealthy_count = len(getattr(event, "unhealthy_services", []))
            return f"System health degraded: {unhealthy_count} services unhealthy"

        if hasattr(event, "threshold_exceeded") and event.threshold_exceeded:
            return f"Performance threshold exceeded in {getattr(event, 'operation', 'unknown operation')}"

        return f"Alert: {event.event_type} event occurred"

    def _is_critical(self, event: ApplicationEvent) -> bool:
        """Determine if this is a critical notification"""
        return (hasattr(event, "overall_health") and event.overall_health == "unhealthy") or (
            hasattr(event, "suspicious") and event.suspicious
        )


# Application Event Bus
class ApplicationEventBus:
    """
    Event bus for application-level events.
    Handles cross-cutting concerns and async event processing.
    """

    def __init__(self):
        self.handlers: List[ApplicationEventHandler] = []
        self.logger = logging.getLogger("event_bus")

    def subscribe(self, handler: ApplicationEventHandler) -> None:
        """Subscribe a handler to all events"""
        self.handlers.append(handler)
        self.logger.info(f"Subscribed handler: {handler.__class__.__name__}")

    def unsubscribe(self, handler: ApplicationEventHandler) -> None:
        """Unsubscribe a handler"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            self.logger.info(f"Unsubscribed handler: {handler.__class__.__name__}")

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish an event to all subscribed handlers"""
        try:
            # Publish to all handlers concurrently
            tasks = []
            for handler in self.handlers:
                tasks.append(handler.handle(event))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.logger.debug(f"Published event: {event.event_type} ({event.event_id})")

        except Exception as e:
            self.logger.error(f"Error publishing event {event.event_type}: {e}")


# Global Application Event Bus
application_event_bus = ApplicationEventBus()

# Initialize default handlers
logging_handler = LoggingEventHandler()
application_event_bus.subscribe(logging_handler)

metrics_handler = MetricsEventHandler()
application_event_bus.subscribe(metrics_handler)

notification_handler = NotificationEventHandler()
application_event_bus.subscribe(notification_handler)


# Event Publisher Utility
class ApplicationEventPublisher:
    """
    Utility class for publishing application events.
    Integrates with the global event bus and adds correlation context.
    """

    def __init__(self, event_bus: ApplicationEventBus = application_event_bus):
        self.event_bus = event_bus

    async def publish_corpus_operation(
        self,
        operation: str,
        corpus_id: str,
        success: bool,
        duration: float,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish a corpus operation event"""
        event = CorpusOperationEvent(
            event_id=f"app_{operation}_{corpus_id}_{int(datetime.now().timestamp())}",
            event_type="corpus_operation",
            operation=operation,
            corpus_id=corpus_id,
            success=success,
            duration=duration,
            error_message=error_message,
            correlation_id=correlation_id,
            user_context=user_context,
            timestamp=datetime.now(),
        )
        await self.event_bus.publish(event)

    async def publish_discovery_operation(
        self,
        corpus_id: str,
        operation: str,
        success: bool = True,
        duration: float = 0.0,
        anomalies_found: Optional[int] = None,
        presuppositions_found: Optional[int] = None,
        transformations_applied: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish a discovery operation event"""
        event = DiscoveryOperationEvent(
            event_id=f"app_discovery_{operation}_{corpus_id}_{int(datetime.now().timestamp())}",
            event_type="discovery_operation",
            corpus_id=corpus_id,
            operation=operation,
            anomalies_found=anomalies_found,
            presuppositions_found=presuppositions_found,
            transformations_applied=transformations_applied,
            success=success,
            duration=duration,
            correlation_id=correlation_id,
            timestamp=datetime.now(),
        )
        await self.event_bus.publish(event)

    async def publish_system_health(
        self,
        overall_health: str,
        services_checked: int,
        unhealthy_services: List[str],
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish a system health event"""
        event = SystemHealthEvent(
            event_id=f"app_health_{int(datetime.now().timestamp())}",
            event_type="system_health",
            overall_health=overall_health,
            services_checked=services_checked,
            unhealthy_services=unhealthy_services,
            correlation_id=correlation_id,
            timestamp=datetime.now(),
        )
        await self.event_bus.publish(event)

    async def publish_performance_event(
        self,
        operation: str,
        duration: float,
        memory_used: Optional[float] = None,
        cpu_used: Optional[float] = None,
        threshold_exceeded: bool = False,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish a performance event"""
        event = PerformanceEvent(
            event_id=f"app_perf_{operation}_{int(datetime.now().timestamp())}",
            event_type="performance",
            operation=operation,
            duration=duration,
            memory_used=memory_used,
            cpu_used=cpu_used,
            threshold_exceeded=threshold_exceeded,
            correlation_id=correlation_id,
            timestamp=datetime.now(),
        )
        await self.event_bus.publish(event)
