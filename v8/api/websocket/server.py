"""
TURBO-CDI v8.0 - WebSocket Real-Time Server
Phase 5: API Layer

Provides real-time updates for:
- Transformation progress
- Meta-system observations
- Falsification test results
- Bridge discoveries
"""

import asyncio
import json
import websockets
from typing import Dict, Set, Any, Optional
from datetime import datetime
from dataclasses import asdict
from urllib.parse import urlparse
from collections import defaultdict
import hmac
import time
import logging
import base64
import re
import uuid
import weakref
import signal
from pathlib import Path

from pydantic import BaseModel, Field, validator

# Import C4State for type annotations
from modules import C4State

# Track fire-and-forget tasks to prevent GC
_active_tasks: weakref.WeakSet = weakref.WeakSet()


def fire_and_forget(coro) -> asyncio.Task:
    """Create a background task and track it to prevent GC."""
    task = asyncio.create_task(coro)
    _active_tasks.add(task)
    task.add_done_callback(lambda t: _active_tasks.discard(t))
    return task


# ═════════════════════════════════════════════════════════════════════════════
# PYDANTIC INPUT VALIDATION MODELS (C7)
# ═════════════════════════════════════════════════════════════════════════════


class NavigateCommand(BaseModel):
    command: str
    from_state: str = Field(default="P00", alias="from")
    to_state: str = Field(default="F10", alias="to")
    domain: str = "general"
    target: str = "STATE"


class FalsifyCommand(BaseModel):
    command: str
    trials: int = Field(default=100, ge=1, le=10000)


class DiscoverCommand(BaseModel):
    command: str
    query: str = ""
    domain: str = "general"


class QueryRAGCommand(BaseModel):
    command: str
    query: str
    sources: list = Field(default_factory=lambda: ["user_docs"])
    top_k: int = Field(default=5, ge=1, le=50)


class SelectGapCommand(BaseModel):
    command: str
    gap_id: str
    domain: str = "general"


logger = logging.getLogger(__name__)


class TurboWebSocketServer:
    """
    WebSocket server for real-time TURBO-CDI updates.

    Features:
    - Real-time transformation progress
    - Live meta-system monitoring
    - Falsification test streaming
    - Bridge discovery updates
    """

    MAX_CONNECTIONS = 100
    ALLOWED_ORIGINS = ["localhost", "127.0.0.1"]
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB

    def __init__(self, host: str = "localhost", port: int = 8765, api_key: Optional[str] = None):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.clients: Set[Any] = set()
        self.turbo = None  # Will be set on start
        self.running = False
        self._connection_semaphore = asyncio.Semaphore(self.MAX_CONNECTIONS)
        self._rate_limits = defaultdict(lambda: {"count": 0, "reset": time.time()})
        self.RATE_LIMIT_PER_MINUTE = 100

    async def register(self, websocket):
        """Register new client with authentication checks"""
        # Check connection limit using semaphore
        if self._connection_semaphore.locked():
            await websocket.close(1013, "Server overloaded")
            return

        async with self._connection_semaphore:
            # Check origin header
            origin = ""
            if hasattr(websocket, "request") and websocket.request:
                origin = websocket.request.headers.get("Origin", "")
            elif hasattr(websocket, "request_headers"):
                origin = websocket.request_headers.get("Origin", "")
            allowed = False
            if origin:
                parsed = urlparse(origin)
                for allowed_origin in self.ALLOWED_ORIGINS:
                    if parsed.hostname == allowed_origin:
                        allowed = True
                        break
            else:
                allowed = True  # Allow non-browser clients

            if not allowed:
                await websocket.close(1008, "Invalid origin")
                return

            # Check API key if configured
            if self.api_key is not None:
                provided_key = ""
                if hasattr(websocket, "request") and websocket.request:
                    provided_key = websocket.request.headers.get("X-API-Key", "")
                elif hasattr(websocket, "request_headers"):
                    provided_key = websocket.request_headers.get("X-API-Key", "")
                if self.api_key is not None and not hmac.compare_digest(provided_key, self.api_key):
                    await self.send_to_client(
                        websocket,
                        {
                            "type": "error",
                            "message": "Invalid API key",
                        },
                    )
                    await websocket.close(1008, "Invalid API key")
                    return

            self.clients.add(websocket)
            await self.send_to_client(
                websocket,
                {
                    "type": "connected",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Connected to TURBO-CDI v8.0 WebSocket",
                },
            )
            print(f"Client connected. Total: {len(self.clients)}")

    async def unregister(self, websocket: Any):
        """Unregister client"""
        self.clients.discard(websocket)
        # Clean up rate limit data to prevent memory leak
        client_id = id(websocket)
        self._rate_limits.pop(client_id, None)
        print(f"Client disconnected. Total: {len(self.clients)}")

    async def send_to_client(self, websocket: Any, data: Dict):
        """Send message to specific client"""
        try:
            await websocket.send(json.dumps(data, default=str))
        except Exception:
            # Client disconnected, remove from set
            self.clients.discard(websocket)

    async def broadcast(self, data: Dict):
        """Broadcast message to all clients"""
        if not self.clients:
            return
        message = json.dumps(data, default=str)
        await asyncio.gather(
            *[client.send(message) for client in self.clients], return_exceptions=True
        )

    async def handle_message(self, websocket: Any, message: str):
        """Handle incoming message from client"""
        # Rate limiting check
        client_id = id(websocket)
        now = time.time()
        if now > self._rate_limits[client_id]["reset"] + 60:
            self._rate_limits[client_id] = {"count": 0, "reset": now}

        self._rate_limits[client_id]["count"] += 1
        if self._rate_limits[client_id]["count"] > self.RATE_LIMIT_PER_MINUTE:
            await websocket.close(1008, "Rate limit exceeded")
            return

        if len(message) > self.MAX_MESSAGE_SIZE:
            await self.send_to_client(
                websocket, {"type": "error", "message": "Message too large (max 1MB)"}
            )
            return

        try:
            data = json.loads(message)
            command = data.get("command")

            if command == "navigate":
                await self.cmd_navigate(websocket, data)
            elif command == "meta":
                await self.cmd_meta(websocket, data)
            elif command == "falsify":
                await self.cmd_falsify(websocket, data)
            elif command == "discover":
                query = data.get("query", "")
                domain = data.get("domain", "general")
                await self.send_to_client(
                    websocket,
                    {
                        "type": "discovery_started",
                        "query": query,
                    },
                )
                result = await self.turbo.discover_domain(query, domain)
                await self.send_to_client(
                    websocket,
                    {
                        "type": "discovery_complete",
                        "gaps_count": len(result.get("gaps", [])),
                        "knowledge_map": result.get("knowledge_map", {}),
                    },
                )
            elif command == "upload_doc":
                filename = data.get("filename", "document")
                content_b64 = data.get("content", "")
                try:
                    content = base64.b64decode(content_b64)
                    safe_name = re.sub(r"[^\w\-_\.]", "", filename) or "unnamed"
                    temp_path = Path("/tmp") / f"{uuid.uuid4()}_{safe_name}"
                    temp_path.write_bytes(content)
                    result = await asyncio.to_thread(self.turbo.ingest_document, str(temp_path))
                    await self.send_to_client(
                        websocket,
                        {
                            "type": "upload_complete",
                            "doc_id": result["doc_id"],
                            "title": result["title"],
                            "chunks": result["chunks"],
                        },
                    )
                except Exception as e:
                    logger.error(f"Upload failed: {e}")
                    await self.send_to_client(
                        websocket, {"type": "error", "message": "Upload failed"}
                    )
            elif command == "query_rag":
                try:
                    validated = QueryRAGCommand(**data)
                except Exception as e:
                    await self.send_to_client(
                        websocket, {"type": "error", "message": f"Invalid parameters: {e}"}
                    )
                    return
                result = await self.turbo.query_knowledge_base(
                    validated.query,
                    validated.sources,
                    validated.top_k,
                )
                await self.send_to_client(
                    websocket,
                    {
                        "type": "rag_results",
                        "query": validated.query,
                        "results": result.get("results", []),
                    },
                )
            elif command == "select_gap":
                gap_id = data.get("gap_id", "")
                domain = data.get("domain", "general")
                result = await self.turbo.select_gap_and_plan(gap_id, domain)
                await self.send_to_client(
                    websocket,
                    {
                        "type": "gap_plan",
                        "gap_id": gap_id,
                        "from_state": result["from_state"],
                        "to_state": result["to_state"],
                        "plan": result["plan"],
                    },
                )
            elif command == "subscribe":
                await self.cmd_subscribe(websocket, data)
            elif command == "ping":
                await self.send_to_client(
                    websocket, {"type": "pong", "timestamp": datetime.now().isoformat()}
                )
            else:
                await self.send_to_client(
                    websocket,
                    {"type": "error", "message": f"Unknown command: {command}"},
                )
        except json.JSONDecodeError:
            await self.send_to_client(websocket, {"type": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            await self.send_to_client(
                websocket, {"type": "error", "message": "Internal server error"}
            )

    async def cmd_navigate(self, websocket: Any, data: Dict):
        """Handle navigate command with progress updates"""
        from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis, SeptetObject

        try:
            validated = NavigateCommand(**data)
            from_state_str = validated.from_state
            to_state_str = validated.to_state
            domain = validated.domain
            target_str = validated.target
        except Exception as e:
            await self.send_to_client(
                websocket, {"type": "error", "message": f"Invalid parameters: {e}"}
            )
            return

        await self.send_to_client(
            websocket,
            {
                "type": "navigation_start",
                "from": from_state_str,
                "to": to_state_str,
                "domain": domain,
            },
        )

        # Real progress: parsing parameters
        await self.send_to_client(
            websocket,
            {"type": "navigation_progress", "step": "parsing", "progress": 0.2},
        )
        from_state = self._parse_state(from_state_str)
        to_state = self._parse_state(to_state_str)
        target = self._parse_target(target_str)

        # Real progress: planning transformation
        await self.send_to_client(
            websocket,
            {"type": "navigation_progress", "step": "planning", "progress": 0.5},
        )
        plan = await self.turbo.plan_transformation(
            from_state=from_state,
            to_state=to_state,
            domain=domain,
            target=target,
        )

        # Real progress: complete
        await self.send_to_client(
            websocket,
            {"type": "navigation_progress", "step": "complete", "progress": 1.0},
        )

        await self.send_to_client(
            websocket,
            {
                "type": "navigation_complete",
                "result": {
                    "path_steps": len(plan.path),
                    "effectiveness": round(plan.estimated_effectiveness, 3),
                    "reversibility": round(plan.estimated_reversibility, 3),
                    "peer_review": plan.peer_review.overall_status if plan.peer_review else None,
                    "bias_warnings": len(plan.bias_warnings),
                    "paradoxes": len(plan.paradoxes) if plan.paradoxes else 0,
                    "path": plan.path,
                },
            },
        )

    async def cmd_meta(self, websocket: Any, data: Dict):
        """Handle meta command"""
        report_type = data.get("report_type", "stats")

        if report_type == "stats":
            stats = await asyncio.to_thread(self.turbo.get_stats)
            await self.send_to_client(websocket, {"type": "meta_stats", "data": stats})
        elif report_type == "report":
            report = await asyncio.to_thread(self.turbo.get_meta_report)
            await self.send_to_client(
                websocket,
                {
                    "type": "meta_report",
                    "data": {
                        "system_health": report.system_health,
                        "self_awareness": report.self_awareness_score,
                        "observations_count": len(report.observations),
                        "recommendations": report.recommendations,
                    },
                },
            )

    async def cmd_falsify(self, websocket: Any, data: Dict):
        """Handle falsify command with streaming results"""
        try:
            validated = FalsifyCommand(**data)
            n_trials = validated.trials
        except Exception as e:
            await self.send_to_client(
                websocket, {"type": "error", "message": f"Invalid parameters: {e}"}
            )
            return

        await self.send_to_client(websocket, {"type": "falsification_start", "trials": n_trials})

        # Run falsification
        report = await asyncio.to_thread(self.turbo.run_falsification_suite, n_trials=n_trials)

        # Stream results
        for result in report.results:
            await self.send_to_client(
                websocket,
                {
                    "type": "falsification_result",
                    "hypothesis": result.hypothesis_id,
                    "description": result.description,
                    "status": result.status.value,
                    "trials": result.trials,
                },
            )

        await self.send_to_client(
            websocket,
            {
                "type": "falsification_complete",
                "summary": {
                    "survival_rate": report.survival_rate,
                    "falsified_count": report.falsified_count,
                    "total": report.total_hypotheses,
                },
            },
        )

    async def cmd_discover(self, websocket: Any, data: Dict):
        """Handle discover command"""
        discover_type = data.get("type", "patterns")

        if discover_type == "patterns":
            await self.send_to_client(websocket, {"type": "discovery_start", "mode": "patterns"})

            patterns = await asyncio.to_thread(self.turbo.discover_patterns, n_explore=50)

            for i, pattern in enumerate(patterns[:10]):  # Limit to 10
                await self.send_to_client(
                    websocket,
                    {
                        "type": "pattern_found",
                        "index": i + 1,
                        "name": pattern.name,
                        "novelty": pattern.novelty_score,
                        "effectiveness": pattern.effectiveness_estimate,
                    },
                )

            await self.send_to_client(
                websocket, {"type": "discovery_complete", "found": len(patterns)}
            )

        elif discover_type == "bridges":
            await self.send_to_client(websocket, {"type": "discovery_start", "mode": "bridges"})

            analysis = await asyncio.to_thread(self.turbo.analyze_bridge_network)

            await self.send_to_client(websocket, {"type": "bridge_analysis", "data": analysis})

    async def cmd_subscribe(self, websocket: Any, data: Dict):
        """Subscribe to real-time updates"""
        channel = data.get("channel", "meta")

        await self.send_to_client(
            websocket,
            {
                "type": "subscribed",
                "channel": channel,
                "message": f"Subscribed to {channel} updates",
            },
        )

        # Start sending periodic updates
        if channel == "meta":
            fire_and_forget(self._send_meta_updates(websocket))

    async def _send_meta_updates(self, websocket: Any):
        """Send periodic meta updates"""
        try:
            while websocket in self.clients:
                await asyncio.sleep(5)  # Every 5 seconds

                if websocket not in self.clients:
                    break

                report = await asyncio.to_thread(self.turbo.get_meta_report)
                await self.send_to_client(
                    websocket,
                    {
                        "type": "meta_update",
                        "timestamp": datetime.now().isoformat(),
                        "health": report.system_health,
                        "self_awareness": report.self_awareness_score,
                    },
                )
        except Exception as e:
            print(f"Meta update error: {e}")

    def _parse_state(self, state_str: str) -> C4State:
        """Parse C4 state from string"""
        from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis

        clean = (
            state_str.strip().replace("C4", "").replace("(", "").replace(")", "").replace(",", "")
        )

        if len(clean) >= 3:
            time_char = clean[0].upper()
            scale_val = int(clean[1]) if clean[1].isdigit() else 0
            agency_val = int(clean[2]) if clean[2].isdigit() else 0
        else:
            time_char, scale_val, agency_val = "P", 0, 0

        time_map = {
            "P": TimeAxis.PAST,
            "0": TimeAxis.PAST,
            "C": TimeAxis.PRESENT,
            "1": TimeAxis.PRESENT,
            "F": TimeAxis.FUTURE,
            "2": TimeAxis.FUTURE,
        }

        scale_map = {0: ScaleAxis.CONCRETE, 1: ScaleAxis.ABSTRACT, 2: ScaleAxis.META}
        agency_map = {0: AgencyAxis.SELF, 1: AgencyAxis.OTHER, 2: AgencyAxis.SYSTEM}

        return C4State(
            time_map.get(time_char, TimeAxis.PAST),
            scale_map.get(scale_val, ScaleAxis.CONCRETE),
            agency_map.get(agency_val, AgencyAxis.SELF),
        )

    def _parse_target(self, target_str: str):
        """Parse Septet target"""
        from modules import SeptetObject

        target_map = {
            "state": SeptetObject.STATE,
            "STATE": SeptetObject.STATE,
            "structure": SeptetObject.STRUCTURE,
            "STRUCTURE": SeptetObject.STRUCTURE,
            "content": SeptetObject.CONTENT,
            "CONTENT": SeptetObject.CONTENT,
            "function": SeptetObject.FUNCTION,
            "FUNCTION": SeptetObject.FUNCTION,
            "relations": SeptetObject.RELATIONS,
            "RELATIONS": SeptetObject.RELATIONS,
            "memory": SeptetObject.MEMORY,
            "MEMORY": SeptetObject.MEMORY,
            "boundary": SeptetObject.BOUNDARY,
            "BOUNDARY": SeptetObject.BOUNDARY,
        }
        return target_map.get(target_str, SeptetObject.STATE)

    async def websocket_handler(self, websocket: Any):
        """Main WebSocket handler"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    def start(self, turbo_instance):
        """Start WebSocket server with graceful shutdown"""
        self.turbo = turbo_instance
        self.running = True
        self._shutdown_event = asyncio.Event()

        print(f"🌐 Starting WebSocket server on ws://{self.host}:{self.port}")
        print(
            f"   Commands: navigate, meta, falsify, discover, upload_doc, query_rag, select_gap, subscribe, ping"
        )

        def signal_handler(sig, frame):
            print("\n🛑 Shutdown signal received, closing server...")
            self.running = False
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        async def main():
            server = await websockets.serve(self.websocket_handler, self.host, self.port)
            try:
                await self._shutdown_event.wait()
            finally:
                server.close()
                await server.wait_closed()
                # Close all client connections
                close_tasks = [asyncio.create_task(client.close()) for client in list(self.clients)]
                if close_tasks:
                    await asyncio.gather(*close_tasks, return_exceptions=True)
                self.clients.clear()
                print("👋 Server shut down gracefully")

        asyncio.run(main())

    async def start_async(self, turbo_instance):
        """Async start method with graceful shutdown"""
        self.turbo = turbo_instance
        self.running = True
        self._shutdown_event = asyncio.Event()

        print(f"🌐 WebSocket server starting on ws://{self.host}:{self.port}")

        server = await websockets.serve(self.websocket_handler, self.host, self.port)

        async def shutdown_monitor():
            await self._shutdown_event.wait()
            server.close()
            await server.wait_closed()
            close_tasks = [asyncio.create_task(client.close()) for client in list(self.clients)]
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            self.clients.clear()

        asyncio.create_task(shutdown_monitor())
        return server

    def stop(self):
        """Signal the server to shut down gracefully."""
        self.running = False
        if hasattr(self, "_shutdown_event"):
            self._shutdown_event.set()


# Example client usage
CLIENT_EXAMPLE = """
# JavaScript Client Example:

const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('Connected to TURBO-CDI');
    
    // Navigate transformation space
    ws.send(JSON.stringify({
        command: 'navigate',
        from: 'P00',
        to: 'F10',
        domain: 'psychology'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Subscribe to meta updates
ws.send(JSON.stringify({
    command: 'subscribe',
    channel: 'meta'
}));
"""


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from core.orchestrator import TurboCDIv8

    turbo = TurboCDIv8()
    server = TurboWebSocketServer()
    server.start(turbo)
