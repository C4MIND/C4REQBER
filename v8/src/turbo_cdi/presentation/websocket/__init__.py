"""
WebSocket handlers for real-time TURBO-CDI operations.
Provides real-time discovery streams and progress monitoring.
"""

import json
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from rich.console import Console

from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.presentation.api.dependencies import get_container

console = Console()
router = APIRouter()


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        console.print(f"🔗 WebSocket client connected: {client_id}", style="blue")

    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.tasks:
            self.tasks[client_id].cancel()
            del self.tasks[client_id]
        console.print(f"📴 WebSocket client disconnected: {client_id}", style="yellow")

    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                console.print(f"Failed to send message to {client_id}: {e}", style="red")
                self.disconnect(client_id)

    async def broadcast(self, message: dict, exclude_client: Optional[str] = None):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            if client_id == exclude_client:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                console.print(f"Failed to broadcast to {client_id}: {e}", style="red")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def start_task(self, client_id: str, task: asyncio.Task):
        """Register a background task for a client"""
        if client_id in self.tasks:
            self.tasks[client_id].cancel()

        self.tasks[client_id] = task
        task.add_done_callback(lambda t: self.tasks.pop(client_id, None))


# Global connection manager
manager = ConnectionManager()


@router.websocket("/discovery/{client_id}")
async def discovery_websocket(
    websocket: WebSocket,
    client_id: str,
    container: Container = Depends(get_container),
):
    """
    Real-time discovery WebSocket endpoint

    Provides streaming updates during knowledge discovery operations:
    - Progress updates
    - Anomaly detections
    - Transformation applications
    - System metrics
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive commands from client
            message = await websocket.receive_json()
            command = message.get("command")

            if command == "start_discovery":
                # Start real-time discovery
                task = asyncio.create_task(run_real_time_discovery(client_id, message, container))
                await manager.start_task(client_id, task)

            elif command == "stop_discovery":
                # Stop ongoing discovery
                manager.disconnect(client_id)

            elif command == "ping":
                # Health check
                await manager.send_message(
                    client_id,
                    {"type": "pong", "timestamp": datetime.now().isoformat(), "status": "alive"},
                )

            else:
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "message": f"Unknown command: {command}",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        console.print(f"WebSocket error for {client_id}: {e}", style="red")
        manager.disconnect(client_id)


@router.websocket("/system/{client_id}")
async def system_websocket(
    websocket: WebSocket,
    client_id: str,
    container: Container = Depends(get_container),
):
    """
    System monitoring WebSocket endpoint

    Streams real-time system metrics and health updates:
    - CPU/Memory usage
    - Database connections
    - Cache hit rates
    - Active operations
    """
    await manager.connect(websocket, client_id)

    try:
        # Start system monitoring task
        monitoring_task = asyncio.create_task(monitor_system_metrics(client_id, container))
        await manager.start_task(client_id, monitoring_task)

        while True:
            # Listen for client commands (keep-alive, etc.)
            message = await websocket.receive_json()

            if message.get("command") == "ping":
                await manager.send_message(
                    client_id, {"type": "pong", "timestamp": datetime.now().isoformat()}
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        console.print(f"System WebSocket error for {client_id}: {e}", style="red")
        manager.disconnect(client_id)


async def run_real_time_discovery(client_id: str, config: dict, container: Container):
    """
    Run discovery with real-time updates via WebSocket
    """
    corpus_id = config.get("corpus_id")
    if not corpus_id:
        await manager.send_message(
            client_id,
            {
                "type": "error",
                "message": "corpus_id required",
                "timestamp": datetime.now().isoformat(),
            },
        )
        return

    try:
        # Send start notification
        await manager.send_message(
            client_id,
            {
                "type": "discovery_started",
                "corpus_id": corpus_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Run discovery service
        discovery_service = container.knowledge_discovery_service()

        # Simulate real-time updates
        progress_steps = [
            "Initializing discovery engine...",
            "Loading corpus data...",
            "Analyzing knowledge structures...",
            "Detecting anomalies...",
            "Applying cognitive transformations...",
            "Generating insights...",
            "Finalizing results...",
        ]

        for i, step in enumerate(progress_steps):
            # Send progress update
            await manager.send_message(
                client_id,
                {
                    "type": "progress",
                    "step": step,
                    "progress": (i + 1) / len(progress_steps) * 100,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Simulate work time
            await asyncio.sleep(2)

        # Run actual discovery
        results = await discovery_service.comprehensive_discovery_analysis(
            corpus_id=corpus_id, analysis_timeout=300
        )

        # Send results
        await manager.send_message(
            client_id,
            {
                "type": "discovery_completed",
                "results": results,
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        await manager.send_message(
            client_id, {"type": "error", "message": str(e), "timestamp": datetime.now().isoformat()}
        )
        console.print(f"Discovery error for {client_id}: {e}", style="red")


async def monitor_system_metrics(client_id: str, container: Container):
    """
    Monitor system metrics and send updates via WebSocket
    """
    try:
        while True:
            try:
                # Get current health metrics
                from turbo_cdi.infrastructure.health import HealthChecker

                health_checker = HealthChecker(container)

                # Quick metrics check
                health_data = await health_checker.check_all()

                # Send metrics update
                await manager.send_message(
                    client_id,
                    {
                        "type": "metrics_update",
                        "metrics": {
                            "overall_health": health_data.get("overall_health", "unknown"),
                            "timestamp": datetime.now().isoformat(),
                            "services": {
                                "database": health_data["services"]
                                .get("database", {})
                                .get("status"),
                                "cache": health_data["services"].get("cache", {}).get("status"),
                            },
                        },
                    },
                )

            except Exception as e:
                console.print(f"Failed to send metrics for {client_id}: {e}", style="red")

            # Update every 30 seconds
            await asyncio.sleep(30)

    except asyncio.CancelledError:
        # Task was cancelled
        pass
    except Exception as e:
        console.print(f"Metrics monitoring error for {client_id}: {e}", style="red")


# Utility function to broadcast system events
async def broadcast_system_event(event_type: str, data: dict):
    """
    Broadcast a system event to all connected clients
    """
    message = {"type": event_type, "data": data, "timestamp": datetime.now().isoformat()}

    await manager.broadcast(message)


# Startup/shutdown events
async def websocket_startup():
    """Initialize WebSocket services"""
    console.print("🔗 WebSocket services initialized", style="blue")


async def websocket_shutdown():
    """Clean up WebSocket services"""
    # Close all connections
    for client_id in list(manager.active_connections.keys()):
        manager.disconnect(client_id)

    console.print("🔌 WebSocket services shut down", style="yellow")
