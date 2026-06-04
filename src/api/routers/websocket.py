"""
C4REQBER API: WebSocket Router
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.auth import AuthManager
from src.api.rate_limiter import WebSocketRateLimiter
from src.api.websocket import ConnectionManager


router = APIRouter(prefix="/api/v1", tags=["websocket"])

ws_manager = ConnectionManager()
auth_manager = AuthManager()
_ws_rate_limiter = WebSocketRateLimiter()
_WS_HANDLER_SEM = asyncio.Semaphore(3)


async def _check_ws_rate_limit(client_id: str) -> bool:
    return await _ws_rate_limiter.check_limit(
        client_id, max_requests=10, window_seconds=60
    )


async def _safe_send(websocket: WebSocket, message: dict[str, Any]) -> bool:
    try:
        await websocket.send_json(message)
        return True
    except WebSocketDisconnect:
        return False


async def handle_discovery_stream(
    websocket: WebSocket, payload: dict[str, Any]
) -> None:
    """Handle discovery stream."""
    from src.agents.pipeline import UniversalSolvePipeline
    from src.llm.multi_provider import ProviderPreset, ProviderRouter

    problem = payload.get("problem") or payload.get("query", "")
    mode = payload.get("mode", "autopilot")
    provider_preset = payload.get("provider_preset")

    if not await _safe_send(
        websocket,
        {
            "type": "progress",
            "stage": "analyzing",
            "message": f"Analyzing: {problem[:60]}...",
        },
    ):
        return

    try:
        if provider_preset:
            try:
                preset = ProviderPreset(provider_preset)
                router = ProviderRouter.from_preset(preset)
                pipeline = UniversalSolvePipeline(provider_router=router)
            except ValueError:
                pipeline = UniversalSolvePipeline()
        else:
            pipeline = UniversalSolvePipeline()

        async for event in pipeline.solve_streaming(problem=problem, mode=mode):
            event_type = event.get("event")
            if event_type == "start":
                if not await _safe_send(
                    websocket,
                    {
                        "type": "progress",
                        "stage": "started",
                        "message": "Pipeline started",
                    },
                ):
                    return
            elif event_type == "step_start":
                if not await _safe_send(
                    websocket,
                    {
                        "type": "progress",
                        "stage": event.get("stage"),
                        "message": f"Running {event.get('stage')}...",
                    },
                ):
                    return
            elif event_type == "step_complete":
                if not await _safe_send(
                    websocket,
                    {
                        "type": "agent_done",
                        "agentName": event.get("stage"),
                        "confidence": 0.8,
                        "result": f"{event.get('stage')} completed",
                    },
                ):
                    return
            elif event_type == "complete":
                result = event.get("result", {})
                hypotheses = [
                    {
                        "id": "h1",
                        "hypothesis": result.get("final_solution", "")[:200],
                        "confidence": result.get("confidence", 0.5),
                    }
                ]
                await _safe_send(
                    websocket,
                    {
                        "type": "complete",
                        "result": f"Discovery complete. Confidence: {result.get('confidence', 0):.0%}",
                        "hypotheses": hypotheses,
                    },
                )
                return
            elif event_type == "error":
                await _safe_send(
                    websocket,
                    {
                        "type": "error",
                        "message": event.get("error", "Pipeline error"),
                    },
                )
                return
    except Exception as e:
        await _safe_send(
            websocket, {"type": "error", "message": f"Pipeline failed: {str(e)}"}
        )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """Websocket endpoint."""
    token = websocket.query_params.get("token")
    if not token:
        for header, value in websocket.headers.items():
            if (
                header.lower() == "authorization"
                and value.startswith("Bearer ")
            ):
                token = value[7:]
                break

    if not token:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    if auth_manager.secret:
        try:
            payload = await auth_manager.decode_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Unauthorized")
                return
        except Exception:
            logging.getLogger("c4reqber.api.websocket").warning(
                "Token decode failed", exc_info=True
            )
            await websocket.close(code=4001, reason="Unauthorized")
            return
    else:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await ws_manager.connect(websocket, client_id)

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                raise
            except Exception:
                logging.getLogger("c4reqber.api.websocket").warning(
                    "Invalid JSON from WebSocket client", exc_info=True
                )
                await _safe_send(
                    websocket,
                    {"type": "error", "message": "Invalid JSON format."},
                )
                continue

            if not await _check_ws_rate_limit(client_id):
                await _safe_send(
                    websocket,
                    {
                        "type": "error",
                        "message": "Rate limit exceeded. Slow down.",
                    },
                )
                continue

            payload_str = json.dumps(data)
            if len(payload_str) > 100_000:
                await _safe_send(
                    websocket,
                    {"type": "error", "message": "Message too large."},
                )
                continue

            try:
                from src.api.models import WebSocketMessage

                message = WebSocketMessage(**data)
            except Exception:
                logging.getLogger("c4reqber.api.websocket").warning(
                    "Invalid WebSocketMessage payload", exc_info=True
                )
                await _safe_send(
                    websocket,
                    {"type": "error", "message": "Invalid message format."},
                )
                continue

            if message.type in ("discover", "discovery_stream"):
                async with _WS_HANDLER_SEM:
                    await handle_discovery_stream(websocket, message.payload)  # type: ignore[arg-type]
            elif message.type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except (RuntimeError, OSError) as e:
        print(f"WebSocket error for {client_id}: {e}")
    finally:
        ws_manager.disconnect(client_id)
