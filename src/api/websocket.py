"""
C4REQBER API: WebSocket Manager
Real-time connection handling
"""
from __future__ import annotations

import threading
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept new connection."""
        await websocket.accept()
        with self._lock:
            self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        """Remove connection."""
        with self._lock:
            self.active_connections.pop(client_id, None)

    async def send_personal_message(self, message: dict[str, Any], client_id: str) -> None:
        """Send message to specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast to all clients. Isolated failures don't affect others."""
        with self._lock:
            connections = list(self.active_connections.items())
        disconnected = []
        for client_id, connection in connections:
            try:
                await connection.send_json(message)
            except (ConnectionError, RuntimeError):
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
