"""
TURBO-CDI v8.0 - WebSocket Client Demo
Phase 5: API Layer

Example client for testing WebSocket connectivity
"""

import asyncio
import websockets
import json
from datetime import datetime


class TurboWebSocketClient:
    """
    Demo WebSocket client for TURBO-CDI.

    Usage:
        client = TurboWebSocketClient()
        asyncio.run(client.connect())
    """

    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        """Connect to WebSocket server and interact"""
        print(f"🔌 Connecting to {self.uri}...")

        async with websockets.connect(self.uri) as websocket:
            self.websocket = websocket

            # Handle incoming messages
            receive_task = asyncio.create_task(self._receive_messages())

            # Send commands
            await self._demo_commands()

            # Wait a bit then close
            await asyncio.sleep(2)
            receive_task.cancel()

    async def _receive_messages(self):
        """Receive and print messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ⬅️  {json.dumps(data, indent=2)}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Receive error: {e}")

    async def _demo_commands(self):
        """Demo sequence of commands"""
        commands = [
            # 1. Ping
            {"command": "ping"},
            # 2. Get meta stats
            {"command": "meta", "report_type": "stats"},
            # 3. Navigate
            {
                "command": "navigate",
                "from": "P00",
                "to": "F10",
                "domain": "psychology",
                "target": "STATE",
            },
            # 4. Subscribe to meta updates
            {"command": "subscribe", "channel": "meta"},
        ]

        for cmd in commands:
            await asyncio.sleep(0.5)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ➡️  Sending: {cmd['command']}")
            await self.websocket.send(json.dumps(cmd))
            await asyncio.sleep(0.5)

    async def navigate(self, from_state: str, to_state: str, domain: str):
        """Send navigate command"""
        await self.websocket.send(
            json.dumps(
                {
                    "command": "navigate",
                    "from": from_state,
                    "to": to_state,
                    "domain": domain,
                }
            )
        )

    async def get_meta(self):
        """Get meta stats"""
        await self.websocket.send(
            json.dumps({"command": "meta", "report_type": "stats"})
        )

    async def subscribe_meta(self):
        """Subscribe to meta updates"""
        await self.websocket.send(
            json.dumps({"command": "subscribe", "channel": "meta"})
        )


async def demo_client():
    """Run demo client"""
    client = TurboWebSocketClient()
    try:
        await client.connect()
    except ConnectionRefusedError:
        print("❌ Could not connect. Is the server running?")
        print("   Start server with: python3 -m api.websocket.server")


if __name__ == "__main__":
    asyncio.run(demo_client())
