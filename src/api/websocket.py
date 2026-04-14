"""
TURBO-CDI API: WebSocket Manager
Real-time connection handling
"""

from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast to all clients."""
        for connection in self.active_connections.values():
            await connection.send_json(message)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
