"""Error handlers and utilities for C44TCDI.

Provides decorators and context managers to reduce try-except duplication
across the codebase, especially in API routers.
"""

import logging
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, TypeVar

from src.plugins.invoke import invoke_plugin_execute
from src.utils.honesty_status import outer_status_from_plugin_result


logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Async safe execution helpers
# ---------------------------------------------------------------------------


async def safe_execute(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    default: T | None = None,
    log_message: str = "Operation failed",
) -> T | None:
    """Safely execute an async function with error logging.

    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        default: Default value to return on error
        log_message: Message to log on error

    Returns:
        Result of the function or default value on error
    """
    try:
        return await func(*args)
    except (TimeoutError, TypeError) as e:
        logger.debug("%s: %s", log_message, e)
        return default


def sync_safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: T | None = None,
    log_message: str = "Operation failed",
) -> T | None:
    """Safely execute a sync function with error logging.

    Args:
        func: Sync function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        default: Default value to return on error
        log_message: Message to log on error

    Returns:
        Result of the function or default value on error
    """
    try:
        return func(*args)
    except (ValueError, TypeError, KeyError, Exception) as e:
        logger.debug("%s: %s", log_message, e)
        return default


# ---------------------------------------------------------------------------
# Step executor: eliminates repeated try-except in API endpoints
# ---------------------------------------------------------------------------


def execute_step(
    results: dict[str, Any],
    key: str,
    func: Callable[..., T],
    *args: Any,
    errors: list[str] | None = None,
    default_value: Any = None,
    error_keys: list[str] | None = None,
) -> T | None:
    """Execute a step function and handle exceptions uniformly.

    This eliminates the repeated pattern:
        try:
            results["key"] = some_function(args)
        except (ValueError, TypeError, KeyError, Exception) as e:
            results["key"] = {"error": str(e)}
            errors.append(f"key: {str(e)}")

    Args:
        results: The results dictionary to update
        key: The key to store the result under
        func: The function to execute
        *args: Arguments to pass to func
        errors: Optional list to append error messages to
        default_value: Value to store on error (default: {"error": str(e)})
        error_keys: Optional list of keys to set with error info

    Returns:
        The function result, or None on error
    """
    try:
        result = func(*args)
        results[key] = result
        return result
    except Exception as e:
        error_msg = str(e)
        if default_value is not None:
            results[key] = default_value
        else:
            results[key] = {"error": error_msg}

        if errors is not None:
            errors.append(f"{key}: {error_msg}")

        # Also set error on additional keys if specified
        if error_keys:
            for ek in error_keys:
                results[ek] = {"error": error_msg}

        logger.warning("Step '%s' failed: %s", key, error_msg)
        return None


async def async_execute_step(
    results: dict[str, Any],
    key: str,
    func: Callable[..., Awaitable[T]],
    *args: Any,
    errors: list[str] | None = None,
    default_value: Any = None,
    error_keys: list[str] | None = None,
) -> T | None:
    """Async version of execute_step.

    Args:
        results: The results dictionary to update
        key: The key to store the result under
        func: The async function to execute
        *args: Arguments to pass to func
        errors: Optional list to append error messages to
        default_value: Value to store on error
        error_keys: Optional list of keys to set with error info

    Returns:
        The function result, or None on error
    """
    try:
        result = await func(*args)
        results[key] = result
        return result
    except Exception as e:
        error_msg = str(e)
        if default_value is not None:
            results[key] = default_value
        else:
            results[key] = {"error": error_msg}

        if errors is not None:
            errors.append(f"{key}: {error_msg}")

        if error_keys:
            for ek in error_keys:
                results[ek] = {"error": error_msg}

        logger.warning("Step '%s' failed: %s", key, error_msg)
        return None


# ---------------------------------------------------------------------------
# Timed execution context managers
# ---------------------------------------------------------------------------


@contextmanager
def timed_execution(name: str, level: str = "info") -> Iterator[None]:
    """Context manager to time execution and log it.

    Args:
        name: Name of the operation for logging
        level: Log level to use ("debug", "info", "warning")

    Yields:
        None

    Example:
        with timed_execution("FRA routing"):
            result = run_fra_routing(problem)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        log_func = getattr(logger, level, logger.info)
        log_func("%s: %.3fs", name, elapsed)


@asynccontextmanager
async def async_timed_execution(name: str, level: str = "info") -> AsyncIterator[None]:
    """Async context manager to time execution and log it.

    Args:
        name: Name of the operation for logging
        level: Log level to use ("debug", "info", "warning")

    Yields:
        None
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        log_func = getattr(logger, level, logger.info)
        log_func("%s: %.3fs", name, elapsed)


# ---------------------------------------------------------------------------
# ErrorHandler context manager
# ---------------------------------------------------------------------------


class ErrorHandler:
    """Context manager for error handling with logging.

    Can be used as:
        with ErrorHandler("Operation failed") as eh:
            result = some_function()
        if eh.error:
            # handle error
    """

    def __init__(self, log_message: str = "Operation failed", default: Any = None) -> None:
        self.log_message = log_message
        self.default = default
        self.result = None
        self.error = None

    def __enter__(self) -> "ErrorHandler":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is not None:
            logger.debug("%s: %s", self.log_message, exc_val)
            self.error = exc_val
            return True
        return False


# ---------------------------------------------------------------------------
# Plugin execution helper
# ---------------------------------------------------------------------------


def execute_plugin(
    plugin_name: str,
    display_name: str,
    context: str,
    problem: str,
    domain: str,
) -> dict[str, Any]:
    """Execute a single cognitive plugin with uniform error handling.

    Eliminates the repeated pattern in run_cognitive_plugins().

    Args:
        plugin_name: Name of the plugin module
        display_name: Display name for the plugin
        context: Context string to pass
        problem: Problem string
        domain: Domain string

    Returns:
        Dict with plugin execution result
    """
    try:
        import importlib

        module = importlib.import_module(f"src.plugins.{plugin_name}")
        if hasattr(module, "execute"):
            result = invoke_plugin_execute(
                module.execute,
                problem=problem[:2000],
                context=context,
                domain=domain,
            )
            return {
                "name": display_name,
                "result": result,
                "status": outer_status_from_plugin_result(result),
            }
        return {"name": display_name, "status": "no_execute"}
    except (AttributeError, ImportError, TypeError) as e:
        return {"name": display_name, "status": "error", "error": str(e)[:100]}
