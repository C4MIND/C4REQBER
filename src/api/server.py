"""
TURBO-CDI: FastAPI Server
Production-ready REST API with WebSocket support
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn

from src.api.models import (
    DiscoveryRequest,
    DiscoveryResponse,
    HypothesisResponse,
    ValidationRequest,
    SearchRequest,
    SearchResponse,
    HealthResponse,
    MetricsResponse,
    UserCreate,
    UserResponse,
    TokenResponse,
    WebSocketMessage,
)
from src.api.database import get_db, Database
from src.api.auth import AuthManager
from src.api.cache import CacheManager
from src.api.rate_limiter import RateLimiter
from src.api.websocket import ConnectionManager


# Security
security = HTTPBearer()

# Connection manager for WebSockets
ws_manager = ConnectionManager()

# Cache manager
cache = CacheManager()

# Rate limiter
rate_limiter = RateLimiter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await cache.connect()
    yield
    # Shutdown
    await cache.disconnect()


# Create FastAPI app
app = FastAPI(
    title="TURBO-CDI API",
    description="Scientific Hypothesis Generation Platform",
    version="4.5.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth manager
auth_manager = AuthManager()


# ═══════════════════════════════════════════════════════════════════
# DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validate JWT token and return user."""
    token = credentials.credentials
    user = await auth_manager.get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


async def check_rate_limit(user: dict = Depends(get_current_user)):
    """Check API rate limits."""
    allowed = await rate_limiter.check_limit(user["id"])
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )
    return user


# ═══════════════════════════════════════════════════════════════════
# HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db_status = await check_database()
    cache_status = await check_cache()

    return HealthResponse(
        status="healthy" if db_status and cache_status else "degraded",
        version="4.5.0",
        timestamp=datetime.utcnow(),
        services={
            "database": "up" if db_status else "down",
            "cache": "up" if cache_status else "down",
            "api": "up",
        },
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics."""
    db = await get_db()

    return MetricsResponse(
        total_discoveries=await db.count_discoveries(),
        total_hypotheses=await db.count_hypotheses(),
        active_experiments=await db.count_active_experiments(),
        validation_rate=await db.get_validation_rate(),
        avg_confidence=await db.get_avg_confidence(),
        api_requests_24h=await rate_limiter.get_request_count(hours=24),
        cache_hit_rate=await cache.get_hit_rate(),
    )


# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════


@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register new user."""
    user = await auth_manager.create_user(
        email=user_data.email, password=user_data.password, name=user_data.name
    )
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
    )


@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserCreate):
    """Login and get JWT token."""
    token = await auth_manager.authenticate(credentials.email, credentials.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=token, token_type="bearer")


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@app.post("/discover", response_model=DiscoveryResponse)
async def create_discovery(
    request: DiscoveryRequest, user: dict = Depends(check_rate_limit)
):
    """Create new scientific discovery."""
    # Check cache
    cache_key = f"discovery:{hash(request.problem)}"
    cached = await cache.get(cache_key)
    if cached:
        return DiscoveryResponse(**cached)

    # Run discovery
    from src.solver.one_shot import get_one_shot_solver

    solver = get_one_shot_solver()
    result = await solver.solve(
        problem=request.problem, max_hypotheses=request.max_hypotheses or 5
    )

    # Save to database
    db = await get_db()
    discovery_id = await db.save_discovery(result, user_id=user["id"])

    response = DiscoveryResponse(
        id=discovery_id,
        problem=result.problem,
        hypotheses=[
            HypothesisResponse(
                id=h["id"],
                hypothesis=h["hypothesis"],
                confidence=h["confidence"],
                method=h["method"],
                c4_path=h.get("c4_path", []),
                triz_principles=h.get("triz_principles", []),
            )
            for h in result.hypotheses
        ],
        top_hypothesis=result.hypotheses[0]["hypothesis"]
        if result.hypotheses
        else None,
        duration_seconds=result.duration_seconds,
        estimated_cost=result.estimated_cost_usd,
        created_at=datetime.utcnow(),
    )

    # Cache result
    await cache.set(cache_key, response.dict(), ttl=3600)

    return response


@app.get("/discoveries", response_model=List[DiscoveryResponse])
async def list_discoveries(
    skip: int = 0, limit: int = 20, user: dict = Depends(get_current_user)
):
    """List user's discoveries."""
    db = await get_db()
    discoveries = await db.get_user_discoveries(user["id"], skip, limit)
    return discoveries


@app.get("/discoveries/{discovery_id}", response_model=DiscoveryResponse)
async def get_discovery(discovery_id: str, user: dict = Depends(get_current_user)):
    """Get specific discovery."""
    db = await get_db()
    discovery = await db.get_discovery(discovery_id, user_id=user["id"])

    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    return DiscoveryResponse(**discovery)


# ═══════════════════════════════════════════════════════════════════
# SEARCH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@app.post("/search/papers", response_model=SearchResponse)
async def search_papers(request: SearchRequest, user: dict = Depends(check_rate_limit)):
    """Search academic papers."""
    from src.search.semantic_scholar import get_semantic_scholar_client

    client = get_semantic_scholar_client()
    papers = await client.search_papers(
        query=request.query,
        limit=request.limit or 10,
        year_start=request.year_start,
        year_end=request.year_end,
    )

    return SearchResponse(
        query=request.query,
        total=len(papers),
        papers=[
            {
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "citation_count": p.citation_count,
                "abstract": p.abstract[:200] + "..."
                if len(p.abstract) > 200
                else p.abstract,
            }
            for p in papers
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# VALIDATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@app.post("/validate/{discovery_id}")
async def validate_hypothesis(
    discovery_id: str,
    request: ValidationRequest,
    user: dict = Depends(get_current_user),
):
    """Submit validation result for hypothesis."""
    db = await get_db()

    await db.update_discovery_status(
        discovery_id=discovery_id,
        status=request.outcome,
        notes=request.notes,
        user_id=user["id"],
    )

    return {"status": "success", "discovery_id": discovery_id}


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT
# ═══════════════════════════════════════════════════════════════════


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for real-time updates."""
    await ws_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = WebSocketMessage(**data)

            # Handle different message types
            if message.type == "discover":
                # Start discovery and stream progress
                await handle_discovery_stream(websocket, message.payload)

            elif message.type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)


async def handle_discovery_stream(websocket: WebSocket, payload: dict):
    """Stream discovery progress via WebSocket."""
    problem = payload.get("problem", "")

    # Send progress updates
    stages = [
        ("analyzing", "Analyzing problem..."),
        ("searching", "Searching literature..."),
        ("generating", "Generating hypotheses..."),
        ("evaluating", "Evaluating solutions..."),
        ("complete", "Discovery complete!"),
    ]

    for stage, message in stages:
        await websocket.send_json(
            {"type": "progress", "stage": stage, "message": message}
        )
        await asyncio.sleep(0.5)  # Simulate work


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════


async def check_database() -> bool:
    """Check database connectivity."""
    try:
        db = await get_db()
        await db.ping()
        return True
    except:
        return False


async def check_cache() -> bool:
    """Check cache connectivity."""
    try:
        await cache.ping()
        return True
    except:
        return False


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "src.api.server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1")),
    )
