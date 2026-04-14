"""
TURBO-CDI v6.0 API Server
FastAPI-based HTTP API and WebSocket endpoints
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

from .. import TURBOCDIEngine, Hypothesis, EngineConfig
from .bridge import CanvasEngineBridge

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TURBO-CDI v6.0 API",
    description="Meta-Simulation Engine API",
    version="6.0.0",
)

# CORS for Canvas frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
_engine: Optional[TURBOCDIEngine] = None
_bridge: Optional[CanvasEngineBridge] = None


def get_engine() -> TURBOCDIEngine:
    """Get or create engine singleton"""
    global _engine
    if _engine is None:
        _engine = TURBOCDIEngine(EngineConfig())
    return _engine


def get_bridge() -> CanvasEngineBridge:
    """Get or create bridge singleton"""
    global _bridge
    if _bridge is None:
        _bridge = CanvasEngineBridge(get_engine())
    return _bridge


# Pydantic models
class HypothesisRequest(BaseModel):
    title: str
    description: str = ""
    parameters: Dict[str, Any] = {}
    c4_state: Optional[str] = None


class SimulationRequest(BaseModel):
    hypothesis: HypothesisRequest
    pattern_id: Optional[str] = None


class SimulationResponse(BaseModel):
    simulation_id: str
    status: str
    confidence: float
    metrics: Dict[str, Any]
    logs: List[str]


# HTTP Endpoints
@app.get("/")
async def root():
    """API info"""
    engine = get_engine()
    return {
        "name": "TURBO-CDI v6.0",
        "version": "6.0.0",
        "status": "running",
        "patterns": len(engine.get_pattern_library()),
    }


@app.get("/patterns")
async def list_patterns():
    """List available simulation patterns"""
    engine = get_engine()
    return engine.get_pattern_library()


@app.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """Run simulation via HTTP"""
    engine = get_engine()
    
    hypothesis = Hypothesis(
        title=request.hypothesis.title,
        description=request.hypothesis.description,
        parameters=request.hypothesis.parameters,
        c4_state=request.hypothesis.c4_state,
    )
    
    import asyncio
    result = await engine.simulate(hypothesis, pattern=request.pattern_id)
    
    return SimulationResponse(
        simulation_id=result.simulation_id,
        status=str(result.status.name),
        confidence=result.confidence_score,
        metrics=result.metrics,
        logs=result.logs,
    )


@app.post("/validate")
async def validate(request: SimulationRequest):
    """Run full validation hierarchy"""
    engine = get_engine()
    
    hypothesis = Hypothesis(
        title=request.hypothesis.title,
        description=request.hypothesis.description,
        parameters=request.hypothesis.parameters,
    )
    
    report = await engine.validate(hypothesis)
    
    return {
        "hypothesis_id": report.hypothesis_id,
        "final_level": report.final_level.name,
        "confidence": report.confidence,
        "recommendations": report.recommendations,
        "attempts": [
            {
                "level": a.level.name,
                "status": a.status,
                "confidence": a.confidence,
            }
            for a in report.attempts
        ],
    }


@app.get("/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get simulation status"""
    bridge = get_bridge()
    
    if simulation_id in bridge.active_simulations:
        return {"status": "running", "simulation_id": simulation_id}
    
    raise HTTPException(status_code=404, detail="Simulation not found")


# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time simulation updates"""
    await websocket.accept()
    
    bridge = get_bridge()
    bridge.register_connection(websocket)
    
    try:
        while True:
            # Receive message from Canvas
            message = await websocket.receive_text()
            
            # Handle via bridge
            await bridge.handle_message(websocket, message)
            
    except WebSocketDisconnect:
        bridge.unregister_connection(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception("WebSocket error")
        bridge.unregister_connection(websocket)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "engine": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
