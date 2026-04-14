"""
Canvas-Engine Bridge
WebSocket-based real-time integration between visualization and simulation
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    START_SIMULATION = "start_simulation"
    STOP_SIMULATION = "stop_simulation"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PROGRESS = "simulation_progress"
    SIMULATION_COMPLETE = "simulation_complete"
    SIMULATION_ERROR = "simulation_error"
    PING = "ping"
    PONG = "pong"


@dataclass
class CanvasMessage:
    """Message format for Canvas-Engine communication"""
    type: str
    timestamp: str
    payload: Dict[str, Any]
    simulation_id: Optional[str] = None
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "simulation_id": self.simulation_id,
        })


class CanvasEngineBridge:
    """Bridge between Canvas frontend and Engine backend"""
    
    def __init__(self, turbo_engine):
        self.engine = turbo_engine
        self.connections: Set[Any] = set()
        self.active_simulations: Dict[str, Any] = {}
        
    async def handle_message(self, websocket, message: str) -> None:
        """Handle incoming message from Canvas"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == MessageType.START_SIMULATION.value:
                await self._handle_start(websocket, data)
            elif msg_type == MessageType.STOP_SIMULATION.value:
                await self._handle_stop(data)
            elif msg_type == MessageType.PING.value:
                await self._handle_ping(websocket)
                
        except Exception as e:
            logger.exception("Error handling message")
            
    async def _handle_start(self, websocket, data: Dict) -> None:
        """Handle simulation start request"""
        from .. import Hypothesis
        
        payload = data.get("payload", {})
        hypothesis = Hypothesis(
            title=payload.get("title", "Untitled"),
            description=payload.get("description", ""),
            parameters=payload.get("parameters", {}),
        )
        
        simulation_id = f"sim_{datetime.now().timestamp()}"
        
        # Start simulation
        task = asyncio.create_task(
            self._run_simulation(simulation_id, hypothesis, payload.get("pattern_id"))
        )
        self.active_simulations[simulation_id] = task
        
        # Acknowledge
        await websocket.send(CanvasMessage(
            type=MessageType.SIMULATION_STARTED.value,
            timestamp=datetime.now().isoformat(),
            payload={"simulation_id": simulation_id},
        ).to_json())
        
    async def _run_simulation(self, sim_id: str, hypothesis, pattern_id: Optional[str]) -> None:
        """Run simulation with progress updates"""
        try:
            result = await self.engine.simulate(hypothesis, pattern=pattern_id)
            
            # Broadcast completion to all connections
            for ws in self.connections:
                try:
                    await ws.send(CanvasMessage(
                        type=MessageType.SIMULATION_COMPLETE.value,
                        timestamp=datetime.now().isoformat(),
                        payload={
                            "simulation_id": sim_id,
                            "status": result.status.value,
                            "confidence": result.confidence_score,
                            "metrics": result.metrics,
                        },
                        simulation_id=sim_id,
                    ).to_json())
                except:
                    pass
                    
        except Exception as e:
            logger.exception(f"Simulation {sim_id} failed")
            
        finally:
            self.active_simulations.pop(sim_id, None)
            
    async def _handle_stop(self, data: Dict) -> None:
        """Handle simulation stop request"""
        sim_id = data.get("simulation_id")
        if sim_id and sim_id in self.active_simulations:
            self.active_simulations[sim_id].cancel()
            
    async def _handle_ping(self, websocket) -> None:
        """Handle ping (keepalive)"""
        await websocket.send(CanvasMessage(
            type=MessageType.PONG.value,
            timestamp=datetime.now().isoformat(),
            payload={},
        ).to_json())
        
    def register_connection(self, websocket):
        self.connections.add(websocket)
        
    def unregister_connection(self, websocket):
        self.connections.discard(websocket)
