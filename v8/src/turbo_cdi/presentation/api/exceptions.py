"""
Exception handlers for FastAPI application.
Properly formats and handles different types of exceptions.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import logging

from turbo_cdi.application.use_cases import ApplicationError
from turbo_cdi.presentation.api.schemas import APIError, ErrorResponse


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException"""
    error_response = ErrorResponse(
        error="HTTPException",
        message=exc.detail,
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(status_code=exc.status_code, content=error_response.dict())


def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    error_response = ErrorResponse(
        error="ValidationError",
        message="Input validation failed",
        details={"validation_errors": exc.errors()},
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(status_code=422, content=error_response.dict())


def validation_exception_handler_v2(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request validation errors"""
    error_response = ErrorResponse(
        error="RequestValidationError",
        message="Request validation failed",
        details={"validation_errors": exc.errors()},
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(status_code=422, content=error_response.dict())


def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Input validation failed",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle domain application errors"""
    logger = logging.getLogger("application")
    logger.warning(f"Application error: {exc}")

    return JSONResponse(
        status_code=400,
        content={
            "error": "ApplicationError",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors"""
    logger = logging.getLogger("api_error")

    if exc.status_code >= 500:
        logger.error(f"API Error: {exc.error_code} - {exc.message}", exc_info=True)
    else:
        logger.warning(f"API Error: {exc.error_code} - {exc.message}")

    error_response = ErrorResponse(
        error=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=exc.status_code, content=error_response.dict())


def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger = logging.getLogger("error")
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred. Please try again later.",
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=500, content=error_response.dict())


# Starlette exception handler for compatibility
async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTPExceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
