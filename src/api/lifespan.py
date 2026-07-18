from __future__ import annotations


"""
C4REQBER API: Application Lifespan
Startup/shutdown events, logging, background tasks.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.cache import CacheManager
from src.api.db_manager import get_db
from src.api.rate_limiter import RateLimiter
from src.knowledge.sources.base_p6 import client_registry
from src.utils.safe_subprocess import safe_subprocess_run, validate_command


def _detect_environment() -> None:
    """Detect environment capabilities at startup."""
    log = logging.getLogger("c4_cdi_turbo")
    # Apple Silicon detection
    import platform

    proc = platform.processor().lower()
    if "arm" in proc or "apple" in proc:
        log.info("Apple Silicon detected — MLX local LLM available")
    # Check ChromaDB
    try:
        import chromadb

        log.info("ChromaDB available — vector store enabled")
    except ImportError:
        pass
    # Check FastMCP
    try:
        import fastmcp

        log.info("FastMCP available — external MCP client enabled")
    except ImportError:
        pass
    # Check uv for package manager
    import shutil

    if shutil.which("uv"):
        log.info("uv found — package manager with isolated envs ready")


LMS_PATH = os.environ.get("LMS_PATH") or shutil.which("lms") or None
MLX_PYTHON_PATH = (
    os.environ.get("MLX_PYTHON_PATH")
    or shutil.which("python3.11")
    or shutil.which("python3")
    or None
)


def _start_external_service(
    name: str, check_url: str, start_cmd: list[str], timeout: int = 10
) -> None:
    """Start an external service if it's not already running."""
    try:
        check_result = safe_subprocess_run(
            ["curl", "-s", "-o", "/dev/null", check_url],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if check_result.returncode == 0:
            logging.getLogger("c4_cdi_turbo").info("%s already running", name)
            return
    except (OSError, RuntimeError):
        pass

    try:
        logging.getLogger("c4_cdi_turbo").info("Starting %s...", name)
        safe_cmd = validate_command(start_cmd)
        subprocess.Popen(
            safe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        for _ in range(timeout * 2):
            try:
                check_result = safe_subprocess_run(
                    ["curl", "-s", "-o", "/dev/null", check_url],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if check_result.returncode == 0:
                    logging.getLogger("c4_cdi_turbo").info("%s started successfully", name)
                    return
            except (OSError, RuntimeError):
                pass
            time.sleep(0.5)
        logging.getLogger("c4_cdi_turbo").warning("%s did not start within %ds", name, timeout)
    except (OSError, RuntimeError) as e:
        logging.getLogger("c4_cdi_turbo").error("Failed to start %s: %s", name, e)


async def startup_services() -> None:
    """Auto-start LM Studio, MLX server, and detect Apple Silicon on startup."""
    _detect_environment()
    if LMS_PATH is None:
        logging.getLogger("c4_cdi_turbo").warning(
            "LMS_PATH not set and 'lms' not found in PATH; skipping LM Studio auto-start"
        )
    else:
        _start_external_service(
            name="LM Studio",
            check_url="http://localhost:1234/v1/models",
            start_cmd=[LMS_PATH, "server", "start"],
        )

    if os.environ.get("MLX_SERVER_ENABLED", "0") in ("0", "false", "no"):
        logging.getLogger("c4_cdi_turbo").info("MLX_SERVER_ENABLED=0 — skipping MLX auto-start")
    elif MLX_PYTHON_PATH is None:
        logging.getLogger("c4_cdi_turbo").warning(
            "MLX_PYTHON_PATH not set and python3.11/python3 not found in PATH; skipping MLX Server auto-start"
        )
    else:
        _start_external_service(
            name="MLX Server",
            check_url="http://localhost:8001/v1/models",
            start_cmd=[
                MLX_PYTHON_PATH,
                "-m",
                "mlx_lm.server",
                "--port",
                "8001",
                "--model",
                "qwen2.5-coder-7b",
            ],
        )


@asynccontextmanager  # type: ignore[arg-type]
async def lifespan(app: FastAPI) -> None:  # type: ignore[misc]
    """Application lifespan handler."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger("c4_cdi_turbo")
    logger.info("C4REQBER API starting up...")

    app.state.cache = CacheManager()
    app.state.rate_limiter = RateLimiter()

    await app.state.cache.connect()
    try:
        db = await get_db()
        await db.ping()
    except Exception as e:
        logger.warning("DB unavailable at startup: %s", e)

    await startup_services()

    async def _periodic_cleanup() -> None:
        while True:
            await asyncio.sleep(600)
            app.state.rate_limiter.cleanup()

    cleanup_task = asyncio.create_task(_periodic_cleanup())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    try:
        await app.state.cache.disconnect()
    except Exception as e:
        logger.warning("Cache disconnect failed: %s", e)
    try:
        db = await get_db()
        await db.disconnect()  # type: ignore[union-attr]
    except Exception as e:
        logger.warning("DB disconnect failed: %s", e)
    try:
        await client_registry.close_all()
        logger.info("Closed all P6 scientific data clients")
    except Exception as e:
        logger.warning("P6 client cleanup failed: %s", e)
    logger.info("C4REQBER API shutting down...")
